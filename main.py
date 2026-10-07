"""Search TVmaze for TV shows and summarise episode ratings per season."""
import requests

API = "https://api.tvmaze.com"
TIMEOUT = 10  # seconds to wait for TVmaze before giving up

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
    except requests.RequestException:
        raise TVMazeError("Could not reach TVmaze. Check your internet connection.")
    if response.status_code == 404:
        return None
    if response.status_code == 429:
        raise TVMazeError("TVmaze is limiting requests. Wait a few seconds and try again.")
    if response.status_code != 200:
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
    query = input("Show name: ").strip()
    if not query:
        print("Please type a show name.")
        return
    shows = search_shows(query)
    if not shows:
        print(f"No shows found for '{query}'.")
        return
    print(f"\n{'ID':>6}  {'Year':<4}  {'Rating':>6}  Name")
    for show in shows:
        rating = show["rating"] if show["rating"] is not None else "n/a"
        print(f"{show['id']:>6}  {show['year']:<4}  {rating:>6}  {show['name']}")


def show_season_ratings():
    text = input("Show ID: ").strip()
    if not text.isdigit():
        print("The show ID must be a number, for example 431.")
        return
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
            print(error)
        except (EOFError, KeyboardInterrupt):
            print()
            break


if __name__ == "__main__":
    main()
