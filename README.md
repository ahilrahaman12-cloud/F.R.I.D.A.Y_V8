# Refined F.R.I.D.A.Y.

This is a cleaned desktop assistant project based on the supplied archive.

## What changed

- Removed incomplete, duplicate desktop-control and planner experiments.
- Moved diagnostics out of the application entry point into `tests/`.
- Centralized configuration in `config.py`; secrets stay in a local `.env` file.
- Limited model file access to `workspace/`, preventing path traversal outside it.
- Added a confirmation gate for destructive or externally impactful requests.
- Continuously observes the local display in memory and supplies the newest frame to Gemini with each request.
- Uses `D:\Obsedian\F.R.I.D.A.Y. Vault` as an Obsidian-compatible memory vault.
- Kept the supplied interface in `templates/index.html`.

## Run it

1. Create a virtual environment and install `requirements.txt`.
2. Copy `.env.example` to `.env`, then insert your own Gemini API key.
3. Run `python app.py`.

## Test it

Run `python -m unittest discover -s tests -v` from this folder.

## Screen privacy

While the app is running, it captures a new local screen frame every two seconds. Frames are held only in memory, but the latest frame is sent to Gemini whenever you submit a request so F.R.I.D.A.Y. can visually understand the desktop.

## Obsidian Memory

Open `D:\Obsedian\F.R.I.D.A.Y. Vault` as a vault in Obsidian. F.R.I.D.A.Y. updates its profile, operating lessons, and activity log there in the background. Add your own Markdown notes to that vault; notes whose filename or contents match the current request are included as context automatically.
also this is a collaborative project with Pritam-goswami210 we forgot how to add contributers so you can also download the zip from his repo
