"""Every kind of problem the app can meet, and how it is handled.

Each row of SCENARIOS is one situation. For each, the test runs the real
menu with a fake TVmaze and a fake Make, then checks:
  - the most serious log level written (INFO, WARNING or ERROR)
  - the exact log message
  - what the user sees on screen
  - whether an alert was sent to Make (only ERRORs are)
Nothing goes over the internet and nothing is written to searches.log.
"""
import logging
from unittest import mock

import pytest
import requests

import main

FAKE_WEBHOOK = "https://hook.example.test/fake-webhook-for-tests"


def tvmaze_reply(status=200, data=None):
    response = mock.Mock(status_code=status)
    response.json.return_value = data
    return response


FRIENDS = [{"show": {"id": 431, "name": "Friends", "premiered": "1994-09-22",
                     "rating": {"average": 8.5}}}]
BROKEN_DATA = [{"not_a_show": {}}]      # TVmaze sending something unexpected

SCENARIOS = [
    # name, what the user types, what TVmaze does,
    # level, log message, on screen, sent to Make?
    ("normal search", ["1", "friends"], tvmaze_reply(data=FRIENDS),
     "INFO", "Searching for TV show: friends", "Friends", False),
    ("no shows found", ["1", "zzqq"], tvmaze_reply(data=[]),
     "WARNING", "No shows found for: zzqq", "No shows found for 'zzqq'", False),
    ("show ID not a number", ["2", "abc"], None,
     "WARNING", "Invalid show ID entered: 'abc'", "must be a number", False),
    ("show ID does not exist", ["2", "999999999"], tvmaze_reply(status=404),
     "WARNING", "TVmaze found nothing at /shows/999999999 (HTTP 404)",
     "No show has ID 999999999", False),
    ("no internet", ["1", "friends"], requests.ConnectionError(),
     "ERROR", "Could not reach TVmaze for /search/shows: ConnectionError",
     "Could not reach TVmaze", True),
    ("TVmaze too slow", ["1", "friends"], requests.Timeout(),
     "ERROR", "Could not reach TVmaze for /search/shows: Timeout",
     "Could not reach TVmaze", True),
    ("too many requests", ["1", "friends"], tvmaze_reply(status=429),
     "ERROR", "TVmaze rate limit hit for /search/shows (HTTP 429)",
     "Wait a few seconds", True),
    ("TVmaze server error", ["1", "friends"], tvmaze_reply(status=500),
     "ERROR", "TVmaze returned HTTP 500 for /search/shows", "HTTP 500", True),
    ("unexpected crash", ["1", "friends"], tvmaze_reply(data=BROKEN_DATA),
     "ERROR", "Unexpected error", "Something unexpected went wrong", True),
]

SEVERITY = {"INFO": 1, "WARNING": 2, "ERROR": 3}


def run_app(typed, tvmaze, caplog):
    """Run the real menu: type `typed`, then 3 to quit. Returns the fake
    `requests.post`, which stands in for Make."""
    alerts = main.MakeAlertHandler(FAKE_WEBHOOK)

    def setup_logging():            # the fake Make instead of the real one
        logging.getLogger().addHandler(alerts)
        return alerts

    tvmaze_does = ({"side_effect": tvmaze} if isinstance(tvmaze, Exception)
                   else {"return_value": tvmaze})
    try:
        with caplog.at_level(logging.INFO), \
                mock.patch("main.setup_logging", setup_logging), \
                mock.patch("builtins.input", side_effect=typed + ["3"]), \
                mock.patch("main.requests.get", **tvmaze_does), \
                mock.patch("main.requests.post") as make:
            main.main()
    finally:
        logging.getLogger().removeHandler(alerts)
    return make


@pytest.mark.parametrize(
    "typed, tvmaze, level, log_message, on_screen, sent_to_make",
    [pytest.param(*row[1:], id=row[0]) for row in SCENARIOS])
def test_each_problem_is_logged_shown_and_alerted_correctly(
        typed, tvmaze, level, log_message, on_screen, sent_to_make,
        caplog, capsys):
    make = run_app(typed, tvmaze, caplog)
    logged = [(r.levelname, r.getMessage()) for r in caplog.records]

    assert (level, log_message) in logged
    most_serious = max(logged, key=lambda line: SEVERITY[line[0]])[0]
    assert most_serious == level
    assert on_screen in capsys.readouterr().out
    assert make.called == sent_to_make
    if sent_to_make:
        sent = make.call_args.kwargs["json"]
        assert sent["level"] == "ERROR"
        assert log_message in sent["message"]


def test_an_unexpected_crash_sends_make_the_full_error_details(caplog):
    make = run_app(["1", "friends"], tvmaze_reply(data=BROKEN_DATA), caplog)
    details = make.call_args.kwargs["json"]["message"]
    assert "Traceback" in details and "KeyError: 'show'" in details


def test_the_app_keeps_running_after_each_error(caplog):
    """After an error the menu comes back: a second, normal search works."""
    with mock.patch("main.requests.get",
                    side_effect=[requests.ConnectionError(),
                                 tvmaze_reply(data=FRIENDS)]), \
            mock.patch("main.setup_logging", return_value=None), \
            mock.patch("builtins.input",
                       side_effect=["1", "friends", "1", "friends", "3"]), \
            caplog.at_level(logging.INFO):
        main.main()
    searches = [r.getMessage() for r in caplog.records
                if r.getMessage() == "Searching for TV show: friends"]
    assert len(searches) == 2
    assert caplog.records[-1].getMessage() == "App closed"
