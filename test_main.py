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
