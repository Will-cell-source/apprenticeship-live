# Simple app test

Run these in a terminal opened in the "apprenticeship live" folder. Each step says what you should see.

1. `.venv\Scripts\python -m pytest` → **27 passed**
2. `.venv\Scripts\python main.py` → "TV show search. Data from TVmaze (tvmaze.com)." and a menu with options 1, 2 and 3
3. Type `1`, then `friends` → a table of **5 shows** (the `search_limit` in `config.json`); the first row is **431, 1994, Friends**
4. Type `1`, then just press **Enter** → it searches the default show from `config.json` (friends), so the first row is again **431, 1994, Friends**
5. Type `1`, then `zzqqxxnotashow` → "No shows found for 'zzqqxxnotashow'."
6. Type `2`, then `431` → "Ratings per season for Friends" with **seasons 1 to 10**, each average about 8.5 to 9.0
7. Type `2`, then `abc` → "The show ID must be a number, for example 431."
8. Type `2`, then `999999999` → "No show has ID 999999999."
9. Type `3` → the app closes
10. Open `searches.log` in the folder → the lines end with these, each starting with the date and time:
    - `INFO - App started (error alerts off)`, or `(error alerts on)` once `.env` has your Make webhook address
    - `INFO - Searching for TV show: friends` (twice)
    - `INFO - Searching for TV show: zzqqxxnotashow` then `WARNING - No shows found for: zzqqxxnotashow`
    - `INFO - Getting ratings for show ID: 431`
    - `WARNING - Invalid show ID entered: 'abc'`
    - `INFO - Getting ratings for show ID: 999999999` then `WARNING - TVmaze found nothing at /shows/999999999 (HTTP 404)`
    - `INFO - App closed`
11. Only once `.env` has your Make webhook address and the scenario is on: `.venv\Scripts\python send_test_alert.py` → "Test alert sent to Make." and, within a minute, the email your Make scenario sends, saying "Test alert: if you got this email, error alerts work."

12. `.venv\Scripts\python -m pytest test_errors.py -v` → **11 passed**, listing each type of problem by name: normal search (INFO), no shows found, show ID not a number, show ID does not exist (WARNING), no internet, TVmaze too slow, too many requests, TVmaze server error, unexpected crash (ERROR, sent to Make), plus the crash details and the app carrying on after an error

13. `.venv\Scripts\python trigger_random_error.py` → "Random error chosen: ..." (one of no internet, TVmaze too slow, too many requests, TVmaze server error, unexpected crash), the app's message for it, then "Done." In `searches.log`: `INFO - Random error test: simulating '...'` followed by an `ERROR` line, and within a minute a Make email with that ERROR. Run it a few times to see different errors.

If every step matches, the app works: steps 3 to 5 test the show search (steps 3 and 4 test the two settings in `config.json`), steps 6 to 8 test the ratings-per-season feature, step 10 tests the logging, step 11 tests the error alerts, step 12 tests every type and level of error, and step 13 makes a real random error happen end to end. Ratings come live from TVmaze, so the averages in step 6 can move slightly over time.
