Scratch space for hands-on coding during the live apprenticeship training session: a terminal app that searches TVmaze for TV shows and summarises episode ratings per season for a show ID.

```
.venv\Scripts\python main.py
.venv\Scripts\python -m pytest
```

`test_errors.py` checks every type of problem the app can meet: the log level it is recorded at, what you see, and whether it is sent to Make. `trigger_random_error.py` makes one of those errors happen for real, at random (only TVmaze is faked), so you can watch the log line and the Make email arrive.

Settings are in `config.json`: `default_query` (the show searched when you press Enter) and `search_limit` (how many results the search lists).

Every search and problem is logged to `searches.log`. Each ERROR is also sent to a Make scenario, which emails it: put the scenario's webhook address in `.env` (see `.env.example`), then check it with `.venv\Scripts\python send_test_alert.py`.

Data from [TVmaze](https://www.tvmaze.com/api).
