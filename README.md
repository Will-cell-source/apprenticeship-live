Scratch space for hands-on coding during the live apprenticeship training session: a terminal app that searches TVmaze for TV shows and summarises episode ratings per season for a show ID.

```
.venv\Scripts\python main.py
.venv\Scripts\python -m pytest
```

Settings are in `config.json`: `default_query` (the show searched when you press Enter) and `search_limit` (how many results the search lists).

Every search and problem is logged to `searches.log`. Each ERROR is also sent to a Make scenario, which emails it: put the scenario's webhook address in `.env` (see `.env.example`), then check it with `.venv\Scripts\python send_test_alert.py`.

Data from [TVmaze](https://www.tvmaze.com/api).
