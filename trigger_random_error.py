"""Make one error happen for real, chosen at random, to watch the error
handling work end to end: the app shows its message, searches.log gets an
ERROR line, and Make emails you.

Only TVmaze is faked, so nothing real is broken. The logging and the Make
alert are the real ones.

    .venv\\Scripts\\python trigger_random_error.py
"""
import logging
import random
from unittest import mock

import requests

import main


def tvmaze_reply(status, data=None):
    response = mock.Mock(status_code=status)
    response.json.return_value = data
    return response


ERRORS = {
    "no internet": requests.ConnectionError("simulated"),
    "TVmaze too slow": requests.Timeout("simulated"),
    "too many requests (HTTP 429)": tvmaze_reply(429),
    "TVmaze server error (HTTP 500)": tvmaze_reply(500),
    "unexpected crash (broken data from TVmaze)":
        tvmaze_reply(200, [{"not_a_show": {}}]),
}

name, fake_tvmaze = random.choice(list(ERRORS.items()))
print(f"Random error chosen: {name}\n")

alerts = main.setup_logging()
logging.info(f"Random error test: simulating '{name}'")
tvmaze_does = ({"side_effect": fake_tvmaze} if isinstance(fake_tvmaze, Exception)
               else {"return_value": fake_tvmaze})
# Search for friends, then quit, as if typed: 1, friends, 3.
with mock.patch("main.setup_logging", return_value=alerts), \
        mock.patch("main.requests.get", **tvmaze_does), \
        mock.patch("builtins.input", side_effect=["1", "friends", "3"]):
    main.main()

print(f"\nDone. searches.log has the ERROR line"
      + (", and Make should email you in a minute." if alerts else
         ". Error alerts are off, so no email (no MAKE_WEBHOOK_URL in .env)."))
