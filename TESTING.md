# Simple app test

Run these in a terminal opened in the "apprenticeship live" folder. Each step says what you should see.

1. `.venv\Scripts\python -m pytest` → **8 passed**
2. `.venv\Scripts\python main.py` → "TV show search. Data from TVmaze (tvmaze.com)." and a menu with options 1, 2 and 3
3. Type `1`, then `friends` → a table of up to 5 shows; the first row is **431, 1994, Friends**
4. Type `1`, then `zzqqxxnotashow` → "No shows found for 'zzqqxxnotashow'."
5. Type `2`, then `431` → "Ratings per season for Friends" with **seasons 1 to 10**, each average about 8.5 to 9.0
6. Type `2`, then `abc` → "The show ID must be a number, for example 431."
7. Type `2`, then `999999999` → "No show has ID 999999999."
8. Type `3` → the app closes

If every step matches, the app works: steps 3 and 4 test the show search, and steps 5 to 7 test the ratings-per-season feature. Ratings come live from TVmaze, so the averages in step 5 can move slightly over time.
