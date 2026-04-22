## Environment Setup & Desktop Bridge

**Goal:** Establish a functional hybrid environment where a Vue.js frontend communicates seamlessly with a Python backend inside a pywebview container.

- [x] **Project Skeleton:** Initialize a dual-folder structure (e.g., `/frontend` for Vite/Vue and `/backend` for Python).
- [x] **Vite/Vue Setup:** Scaffold a Vue 3 project with Tailwind CSS (for quick layout) and Vite.
- [x] **Pywebview Integration:** Create a `main.py` entry point that launches `pywebview` and points to the Vite dev server (development) or build folder (production).
- [x] **Bridge Implementation:** Establish a `Bridge` class in Python to expose functions like `start_initial_sync()` and `analyze_album_for_track(track_id)` to the JavaScript window object.
- [x] **ffmpeg** librosa need ffmpeg to work so make sure it installed
- [x] **Testing Point 1: Verify Bridge Connection**
  - [x] Run the Python script; confirm a desktop window opens.
  - [x] Execute a test Python function from the Vue console (e.g., `window.pywebview.api.echo('test')`) and confirm the response.

## Data Architecture & Deezer Integration

**Goal:** Ingest user streaming data and perform Librosa analysis to establish the "Taste Centroid."

- [x] **SQLite Schema:**
  - [x] `user_preferences`: Store "Sonic DNA" vectors (Librosa features) for each liked track.
  - [x] `scanned_albums`: Cache results for album scores, track-by-track similarity, and metadata.
  - [x] `physical_shelf`: Store user-confirmed purchases.
- [x] **Deezer API Client:** Implement a Python module using `Requests` to fetch a user's "Loved Tracks" (metadata + preview URLs).
- [x] **Initial Profiling (Librosa):**
  - [x] Implement a background loop to download previews for all "Loved Tracks."
  - [x] Use `librosa` to extract MFCCs, Chroma, and spectral features for each track.
  - [x] Save these feature vectors into the `user_preferences` table to define the user's permanent "Taste Centroid."
- [x] **Testing Point 2: Data Ingestion & Analysis**
  - [x] Verify that Librosa features are correctly calculated and stored for the initial batch of favorite tracks.

## LLM Decision Layer & Insights

**Goal:** Use OpenAI to translate Librosa similarity math into human-readable "Purchase Confidence."

- [x] **Audio Logic Gate:** Implement the function to fetch all tracks of a target album and run Librosa analysis on each, comparing them against the stored `user_preferences`.
- [x] **OpenAI SDK Integration:** Configure the `OpenAI` client to interpret the resulting similarity data. We put in the base url in the env file to switch between local and api
- [x] **Sonic Breakdown Prompt:** Design a prompt that takes the numerical similarity scores and metadata to generate a "Sonic Breakdown" (e.g., "This album matches your preference for high-energy rhythm but includes one experimental ambient track").
- [x] **Confidence Score Calculation:** Build the logic gate that aggregates track-to-centroid scores into a final 0–100% percentage.
- [x] **Testing Point 4: Confidence Logic**
  - [x] Verify the LLM correctly identifies "Outliers" (Filler tracks) based on the audio math provided to it.

## Marketplace Acquisition Scraper

**Goal:** Automatically find physical purchase links using Playwright and LLM-driven parsing.

- [x] **Scraper Foundation:** Initialize `Playwright` in headless mode.
- [x] **Site Drivers:**
  - [x] Implement scrapers for `Velvet.nl`, `Bol.com`, and a fallback Google search.
- [x] **LLM Scraping Logic:** Use the LLM to parse raw HTML/Text from the scrapers to find the exact "Buy it Now" price and stock status (handles fragile site changes).
- [x] **Acquisition Trigger:** Logic to only initiate scraping if the Album Confidence Score exceeds 65% after the user clicks the "Worth Buying" button.
- [x] **Testing Point 5: Scraper Reliability**
  - [x] Search for a known vinyl record and verify the scraper returns at least one valid URL and price from a Dutch retailer.

## Frontend UI & User Flow

**Goal:** Create the visual experience for the "Buy-Ready" loop, focusing on track-initiated searches.

- [x] **Dashboard:** Build a view displaying the sync'd "Loved Tracks" from the database with their sonic profile status.
- [x] **"Worth Buying?" Action:**
  - [x] Add a prominent button/icon to each track in the favorites list: "Is the album worth it?".
  - [x] Implement the loading state while Librosa analyzes the rest of that track's parent album.
- [x] **The Verdict View:**
  - [x] Display the 0-100% Purchase Confidence Score for the album.
  - [x] Show the "Filler Detection" list (flagging risky tracks that don't match the user's saved features).
  - [x] Display acquisition links with prices once the scan finishes.
- [ ] **Collection Log:** "I bought this" button to add the record to the "Physical Shelf" view.
- [ ] **Testing Point 6: UX Walkthrough**
  - [ ] Perform the full flow: Sync Tracks -> Automated Librosa Profiling -> Click "Worth Buying" on a track -> Review Album Score -> View Purchase Links.

## Deployment

**Goal:** Package the application for local desktop use.

- [ ] **Asset Optimization:** Run `npm run build` in the frontend to generate optimized static files.
- [ ] **Python Bundling:**
  - [ ] Use `PyInstaller` or `Nuitka` to bundle the Python environment, Librosa dependencies (FFmpeg), and the `pywebview` app.
  - [ ] Ensure `playwright` browsers are correctly bundled or downloaded on first run.
- [ ] **Environment Security:** Ensure API keys (OpenAI, Deezer) are managed via a local `.env` file or a secure user input field in the UI.
- [ ] **Final QA:** Run the bundled executable on a clean machine to verify all dependencies (Librosa/Playwright) are present.