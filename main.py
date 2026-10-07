"""Search TVmaze for TV shows and summarise episode ratings per season."""
from datetime import datetime
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
import requests

# load the config file (the default search and how many results to list),
# next to this file, so the app works whichever folder you run it from
CONFIG_FILE = Path(__file__).with_name("config.json")
with open(CONFIG_FILE) as f:
    CONFIG = json.load(f)

API = "https://api.tvmaze.com"
TIMEOUT = 10  # seconds to wait for TVmaze before giving up

# the log file, next to this file: every search, and anything that goes wrong
LOG_FILE = Path(__file__).with_name("searches.log")
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# the Make webhook address is kept in .env, which is never uploaded to GitHub:
# anyone with the address could set off the scenario
ENV_FILE = Path(__file__).with_name(".env")


class MakeAlertHandler(logging.Handler):
    """Sends each ERROR line to a Make scenario's webhook, and Make emails it.
    If sending fails, it says so on screen instead of an error dump."""

    failed = False

    def __init__(self, url):
        super().__init__(level=logging.ERROR)   # only errors are sent
        self.url = url

    def emit(self, record):
        try:
            response = requests.post(self.url, timeout=10, json={
                "app": "TV show search",
                "time": datetime.fromtimestamp(record.created).isoformat(" ", "seconds"),
                "level": record.levelname,
                "message": self.format(record),   # includes any error details
            })
            response.raise_for_status()
        except Exception:
            self.handleError(record)

    def handleError(self, record):
        self.failed = True
        print("(The error alert could not be sent to Make: check "
              "MAKE_WEBHOOK_URL in .env, that the scenario is on, and your "
              "internet connection.)")


def make_alert_handler():
    """The Make alert sender, or None if .env has no MAKE_WEBHOOK_URL."""
    url = (os.getenv("MAKE_WEBHOOK_URL") or "").strip()
    return MakeAlertHandler(url) if url else None


def setup_logging():
    """Log everything to searches.log, and send errors to Make if .env is set
    up. Returns the alert sender, or None when error alerts are off."""
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format=LOG_FORMAT)
    load_dotenv(ENV_FILE)
    alerts = make_alert_handler()
    if alerts is not None:
        logging.getLogger().addHandler(alerts)
    return alerts

MENU = """
1. Search for a show
2. Ratings per season (needs a show ID)
3. Quit"""


class TVMazeError(Exception):
    """TVmaze could not be reached, or answered with an error."""


# ------------------------------------------------------------ talking to TVmaze
def get_json(path, params=None):
    """GET one TVmaze endpoint. Returns the JSON, or None for 'not found'."""
    try:
        response = requests.get(f"{API}{path}", params=params, timeout=TIMEOUT)
    except requests.RequestException as error:
        logging.error(f"Could not reach TVmaze for {path}: {type(error).__name__}")
        raise TVMazeError("Could not reach TVmaze. Check your internet connection.")
    if response.status_code == 404:
        logging.warning(f"TVmaze found nothing at {path} (HTTP 404)")
        return None
    if response.status_code == 429:
        logging.error(f"TVmaze rate limit hit for {path} (HTTP 429)")
        raise TVMazeError("TVmaze is limiting requests. Wait a few seconds and try again.")
    if response.status_code != 200:
        logging.error(f"TVmaze returned HTTP {response.status_code} for {path}")
        raise TVMazeError(f"TVmaze returned an error (HTTP {response.status_code}).")
    return response.json()


def search_shows(query, limit=5):
    """The top matches for a name, each with its ID, name, year and rating."""
    results = get_json("/search/shows", params={"q": query}) or []
    shows = []
    for result in results[:limit]:
        show = result["show"]
        shows.append({
            "id": show["id"],
            "name": show["name"],
            "year": (show.get("premiered") or "")[:4] or "?",
            "rating": (show.get("rating") or {}).get("average"),
        })
    return shows


def get_show(show_id):
    return get_json(f"/shows/{show_id}")


def get_episodes(show_id):
    # Specials are left out: TVmaze only includes them when asked to.
    return get_json(f"/shows/{show_id}/episodes") or []


# ------------------------------------------------------------ the summary
def season_ratings(episodes):
    """Per season: episode count, how many are rated, and their average.

    Episodes with no rating are skipped. A season with no ratings at all
    gets an average of None rather than 0.
    """
    seasons = {}
    for episode in episodes:
        season = seasons.setdefault(episode["season"], {"episodes": 0, "ratings": []})
        season["episodes"] += 1
        rating = (episode.get("rating") or {}).get("average")
        if rating is not None:
            season["ratings"].append(rating)
    summary = []
    for number in sorted(seasons):
        ratings = seasons[number]["ratings"]
        summary.append({
            "season": number,
            "episodes": seasons[number]["episodes"],
            "rated": len(ratings),
            "average": round(sum(ratings) / len(ratings), 1) if ratings else None,
        })
    return summary


# ------------------------------------------------------------ the menu options
def show_search():
    default = CONFIG["default_query"]
    query = input(f"Show name (press Enter for '{default}'): ").strip()
    if not query:
        query = default
    logging.info(f"Searching for TV show: {query}")
    shows = search_shows(query, CONFIG["search_limit"])
    if not shows:
        logging.warning(f"No shows found for: {query}")
        print(f"No shows found for '{query}'.")
        return
    print(f"\n{'ID':>6}  {'Year':<4}  {'Rating':>6}  Name")
    for show in shows:
        rating = show["rating"] if show["rating"] is not None else "n/a"
        print(f"{show['id']:>6}  {show['year']:<4}  {rating:>6}  {show['name']}")


def show_season_ratings():
    text = input("Show ID: ").strip()
    if not text.isdigit():
        logging.warning(f"Invalid show ID entered: {text!r}")
        print("The show ID must be a number, for example 431.")
        return
    logging.info(f"Getting ratings for show ID: {text}")
    show = get_show(int(text))
    if show is None:
        print(f"No show has ID {text}.")
        return
    summary = season_ratings(get_episodes(show["id"]))
    if not summary:
        print(f"{show['name']} has no episodes listed.")
        return
    print(f"\nRatings per season for {show['name']}")
    print(f"{'Season':>6}  {'Episodes':>8}  {'Rated':>5}  {'Average':>7}")
    for row in summary:
        average = row["average"] if row["average"] is not None else "n/a"
        print(f"{row['season']:>6}  {row['episodes']:>8}  {row['rated']:>5}  {average:>7}")


def main():
    alerts = setup_logging()
    logging.info(f"App started (error alerts {'on' if alerts else 'off'})")
    print("TV show search. Data from TVmaze (tvmaze.com).")
    while True:
        print(MENU)
        try:
            choice = input("Choose 1, 2 or 3: ").strip()
            if choice == "1":
                show_search()
            elif choice == "2":
                show_season_ratings()
            elif choice == "3":
                break
            else:
                print("Please choose 1, 2 or 3.")
        except TVMazeError as error:
            print(error)                    # already logged where it happened
        except (EOFError, KeyboardInterrupt):
            print()
            break
        except Exception:
            # anything unexpected: the full details go to the log
            logging.exception("Unexpected error")
            print(f"Something unexpected went wrong. Details are in {LOG_FILE.name}.")
    logging.info("App closed")


if __name__ == "__main__":
    main()
