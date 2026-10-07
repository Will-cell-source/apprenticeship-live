# Simple app test

Run these in a terminal opened in the "apprenticeship live" folder. Each step says what you should see.

1. `.venv\Scripts\python -m pytest` → **10 passed**
2. `.venv\Scripts\python main.py` → "TV show search. Data from TVmaze (tvmaze.com)." and a menu with options 1, 2 and 3
3. Type `1`, then `friends` → a table of **5 shows** (the `search_limit` in `config.json`); the first row is **431, 1994, Friends**
4. Type `1`, then just press **Enter** → it searches the default show from `config.json` (friends), so the first row is again **431, 1994, Friends**
5. Type `1`, then `zzqqxxnotashow` → "No shows found for 'zzqqxxnotashow'."
6. Type `2`, then `431` → "Ratings per season for Friends" with **seasons 1 to 10**, each average about 8.5 to 9.0
7. Type `2`, then `abc` → "The show ID must be a number, for example 431."
8. Type `2`, then `999999999` → "No show has ID 999999999."
9. Type `3` → the app closes

If every step matches, the app works: steps 3 to 5 test the show search (steps 3 and 4 test the two settings in `config.json`), and steps 6 to 8 test the ratings-per-season feature. Ratings come live from TVmaze, so the averages in step 6 can move slightly over time.
