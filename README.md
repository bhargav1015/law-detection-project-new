Law Detection Project — Local / Free Setup

This project runs fully offline using a local classifier + semantic embeddings (sentence-transformers). No paid LLMs are required.

Documentation: See [PROJECT DOCUMENTATION](docs/PROJECT_DOCUMENTATION.md) for full setup, architecture, and presentation notes.

Quick start (Windows PowerShell)

1. Clone the repo and change directory

   git clone <your-repo-url> law-detection-project
   cd law-detection-project

2. Setup (create venv and install deps)

   .\setup.ps1
   # optionally build embeddings too:
   .\setup.ps1 -BuildEmbeddings

Quick start (macOS / Linux)

   git clone <your-repo-url> law-detection-project
   cd law-detection-project
   ./setup.sh  # add 1 to build embeddings: ./setup.sh 1

Build embeddings (if you added more labeled examples)

   python backend/emb_classifier.py --build

Run backend in free/offline mode

Windows PowerShell:
   $env:FREE_MODE='1'; python backend/app.py

Unix/macOS:
   FREE_MODE=1 python backend/app.py

Server will run on http://127.0.0.1:5000. Open `index.html` or `analyze.html` in your browser (File→Open).

Notes
- `FREE_MODE=1` disables external LLM calls; the inference chain is: classifier → embedding k-NN → keyword rules.
- Add more labeled examples to `backend/dataset.jsonl` (one JSON object per line) and re-run the build step.
- Tune similarity cutoff with environment variable `EMB_THRESHOLD` (default 0.35).

If you want automation for a classroom, I can produce a single `setup_all.ps1` that runs the full flow and includes a simple smoke test.
# AI Law Detection - Local Run

This project is a prototype frontend + lightweight backend for analyzing legal case descriptions and suggesting likely IPC sections and defense strategies.

## Setup (Windows)

1. Create and activate Python virtual environment (already created in `backend/venv` if you ran setup):

```powershell
backend\venv\Scripts\activate
```

2. Install dependencies:

```powershell
pip install -r backend/requirements.txt
```

3. Start the backend server:

```powershell
python backend/app.py
```

If you want to enable the hosted LLM (OpenAI) integration, set your API key as an environment variable before starting the backend:

```powershell
setx OPENAI_API_KEY "your_api_key_here"
```

Then open a new terminal (so the env var is available) and start the backend.

You can also set `LLM_PROVIDER` to change provider (default `openai`).

Example on Windows (PowerShell) to set provider and key for current session:

```powershell
$env:OPENAI_API_KEY = "your_api_key_here"
$env:LLM_PROVIDER = "openai"
python backend/app.py
```

Frontend note: If you open `analyze.html` directly from the file system (file://), the frontend will try to reach the backend at `http://127.0.0.1:5000`. For best results, serve the frontend over HTTP (VS Code Live Server or a simple Python HTTP server):

```powershell
# from project root
python -m http.server 8000
# then open http://localhost:8000/index.html
```

LLM testing
 - To verify the LLM integration (OpenAI) works, set `OPENAI_API_KEY` in your environment and run the test script:

```powershell
$env:OPENAI_API_KEY = "your_api_key_here"
python backend/test_llm.py
```

If the script prints a JSON object, the LLM path is available and ready for end-to-end testing via the frontend.

4. Open `index.html` in your browser (double-click or serve via Live Server in VS Code).

## Features
- Submit case descriptions and optional files (each file < 5MB).
- Keyword-based mapping suggests IPC sections (prototype: murder/kill, cheating, default civil mapping).
- Follow-up questions appear for certain cases (e.g., killing) and answers can refine the analysis.
- All analyses are saved to `backend/history.json` and uploaded files are stored in `backend/uploads`.
- View and remove previous analyses via `history.html`.

## Notes
- This is a prototype. Replace keyword mapping with a true NLP model for production use.
- Do not use this server in production without proper security and data protection.
