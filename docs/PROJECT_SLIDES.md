Slide 1 — Title
- **Title:** Law Detection — Offline Prototype
- **Subtitle:** TF‑IDF classifier + semantic embeddings fallback
- **Presenter:** Your Name / Team

Slide 2 — Problem & Goal
- **Problem:** Students need an offline tool to identify likely laws and defenses from case descriptions.
- **Goal:** Provide a free, local prototype suitable for classroom demos and assignments.

Slide 3 — Approach
- **Pipeline:** Rules → TF‑IDF classifier (`scikit-learn`) → semantic k‑NN (`sentence-transformers`).
- **Artifacts:** `model.joblib`, `embeddings.npz`, `dataset.jsonl`.

Slide 4 — Demo Steps
- Create venv, install deps: `setup.ps1` / `setup.sh`.
- Build embeddings: `python backend/emb_classifier.py --build`.
- Start backend: `FREE_MODE=1 python backend/app.py`.
- Open `index.html`, submit sample case, view history.

Slide 5 — Architecture
- Frontend (static HTML/JS) → Flask API → Inference (Classifier, Embeddings, Rules)
- History persisted in `backend/history.json` and logs in `backend/logs/analysis.log`.

Slide 6 — Next Steps
- Expand labeled dataset and retrain classifier.
- Add UI to label cases and trigger retrain.
- Replace Flask dev server with WSGI for production.

Slide 7 — Contact / Repo
- Repo: your repo URL
- Docs: `docs/PROJECT_DOCUMENTATION.md`
