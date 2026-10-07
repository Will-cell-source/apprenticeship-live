import logging
import os
from unittest import mock

import pytest
import requests

import main


def fake_response(status=200, data=None):
    response = mock.Mock(status_code=status)
    response.json.return_value = data
    return response


def episode(season, rating):
    return {"season": season, "rating": {"average": rating}}


# ------------------------------------------------------------ season_ratings
def test_season_ratings_averages_each_season_and_skips_unrated_episodes():
    episodes = [episode(1, 8.0), episode(1, 9.0), episode(1, None),
                episode(2, None)]
    assert main.season_ratings(episodes) == [
        {"season": 1, "episodes": 3, "rated": 2, "average": 8.5},
        {"season": 2, "episodes": 1, "rated": 0, "average": None},
    ]


def test_season_ratings_rounds_to_one_decimal_place():
    episodes = [episode(1, 7.0), episode(1, 8.0), episode(1, 8.0)]
    assert main.season_ratings(episodes)[0]["average"] == 7.7


def test_season_ratings_of_no_episodes_is_empty():
    assert main.season_ratings([]) == []


# ------------------------------------------------------------ talking to TVmaze
def test_search_shows_returns_the_top_five_with_id_year_and_rating():
    results = [{"show": {"id": n, "name": f"Show {n}", "premiered": "1994-09-22",
                         "rating": {"average": 8.5}}} for n in range(6)]
    results[0]["show"]["premiered"] = None
    with mock.patch("main.requests.get",
                    return_value=fake_response(data=results)) as get:
        shows = main.search_shows("friends")
    assert get.call_args.kwargs["params"] == {"q": "friends"}
    assert len(shows) == 5
    assert shows[0] == {"id": 0, "name": "Show 0", "year": "?", "rating": 8.5}
    assert shows[1]["year"] == "1994"


def test_an_empty_search_uses_the_default_query_in_config():
    with mock.patch.dict(main.CONFIG, {"default_query": "the office"}), \
            mock.patch("builtins.input", return_value=""), \
            mock.patch("main.search_shows", return_value=[]) as search:
        main.show_search()
    assert search.call_args.args[0] == "the office"


def test_the_search_lists_as_many_results_as_search_limit_in_config():
    with mock.patch.dict(main.CONFIG, {"search_limit": 3}), \
            mock.patch("builtins.input", return_value="friends"), \
            mock.patch("main.search_shows", return_value=[]) as search:
        main.show_search()
    search.assert_called_once_with("friends", 3)


def test_each_search_is_logged_as_info(caplog):
    with caplog.at_level(logging.INFO), \
            mock.patch("builtins.input", return_value="lassie"), \
            mock.patch("main.search_shows", return_value=[]):
        main.show_search()
    assert ("INFO", "Searching for TV show: lassie") in [
        (r.levelname, r.getMessage()) for r in caplog.records]


def test_a_failed_request_is_logged_as_an_error(caplog):
    with mock.patch("main.requests.get", return_value=fake_response(status=500)):
        with pytest.raises(main.TVMazeError):
            main.search_shows("friends")
    assert ("ERROR", "TVmaze returned HTTP 500 for /search/shows") in [
        (r.levelname, r.getMessage()) for r in caplog.records]


FAKE_WEBHOOK = "https://hook.example.test/fake-webhook-for-tests"


def test_without_a_webhook_address_no_alerts_are_sent():
    with mock.patch.dict(os.environ, {}, clear=True):
        assert main.make_alert_handler() is None


def sent_to_make(level, message, **post_behaviour):
    """Log one line through the Make alert sender with a fake Make, and return
    the handler and the fake `requests.post` so a test can see what was sent."""
    with mock.patch.dict(os.environ, {"MAKE_WEBHOOK_URL": FAKE_WEBHOOK}):
        handler = main.make_alert_handler()
    logger = logging.getLogger("alert-test")
    logger.addHandler(handler)
    try:
        with mock.patch("main.requests.post", **post_behaviour) as post:
            logger.log(level, message)
    finally:
        logger.removeHandler(handler)
    return handler, post


def test_an_error_is_sent_to_the_make_webhook():
    handler, post = sent_to_make(logging.ERROR,
                                 "TVmaze returned HTTP 500 for /search/shows")
    post.assert_called_once()
    assert post.call_args.args == (FAKE_WEBHOOK,)
    sent = post.call_args.kwargs["json"]
    assert sent["level"] == "ERROR"
    assert sent["message"] == "TVmaze returned HTTP 500 for /search/shows"
    assert sent["app"] == "TV show search" and sent["time"]
    assert not handler.failed


def test_an_alert_that_cannot_be_sent_gives_a_short_message(capsys):
    handler, _ = sent_to_make(logging.ERROR, "TVmaze returned HTTP 500",
                              side_effect=requests.ConnectionError("offline"))
    output = capsys.readouterr()
    assert "could not be sent to Make" in output.out
    assert "Traceback" not in output.err
    assert handler.failed, "so send_test_alert.py can report the failure"


def test_info_and_warnings_are_not_sent_to_make():
    for level in (logging.INFO, logging.WARNING):
        _, post = sent_to_make(level, "Searching for TV show: friends")
        assert not post.called


def test_an_unknown_show_id_is_none():
    with mock.patch("main.requests.get", return_value=fake_response(status=404)):
        assert main.get_show(999999999) is None


@pytest.mark.parametrize("problem", [fake_response(status=429),
                                     fake_response(status=500),
                                     requests.ConnectionError()])
def test_api_problems_become_a_readable_error(problem):
    kwargs = ({"side_effect": problem} if isinstance(problem, Exception)
              else {"return_value": problem})
    with mock.patch("main.requests.get", **kwargs):
        with pytest.raises(main.TVMazeError):
            main.search_shows("friends")
