**Law Detection Project — Documentation

**Overview**
- **Purpose**: Local, offline system to classify legal case descriptions into broad categories and suggest applicable laws, defenses, and follow-up questions. Designed for free use (no paid LLMs).
- **Inference Flow**: rule-based keywords → TF‑IDF classifier (`scikit-learn`) → semantic k‑NN on sentence-transformer embeddings (`sentence-transformers`).

**Quick Start (Windows PowerShell)**
- **Create venv + install**:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```
- **Build embeddings (optional but recommended)**:
```powershell
python backend/emb_classifier.py --build
```
- **Start backend (offline)**:
```powershell
$env:FREE_MODE='1'
.\venv\Scripts\Activate.ps1
python backend/app.py
```
- **Open frontend**: open [index.html](../index.html) or [analyze.html](../analyze.html) in your browser.

**API Endpoints**
- **GET** `/health` — returns `{ "status": "ok" }`.
- **POST** `/analyze` — form-encoded `caseText` (string), optional `followUpAnswers` JSON, optional file uploads. Returns analysis JSON with keys: `id`, `caseText`, `category`, `laws`, `defenses`, `reasons`, `followUps`, `followUpAnswers`.
- **GET** `/history` — returns saved analyses from [backend/history.json](../backend/history.json).
- **DELETE** `/history/<id>` — remove analysis by id.
- **POST** `/history/<id>/view` — mark an analysis as viewed (frontend calls this when user opens a saved result).

**Key Files**
- **Backend server**: [backend/app.py](../backend/app.py)
- **Embedding helper**: [backend/emb_classifier.py](../backend/emb_classifier.py)
- **Classifier model**: [backend/model.joblib](../backend/model.joblib)
- **Dataset**: [backend/dataset.jsonl](../backend/dataset.jsonl)
- **Embeddings**: [backend/embeddings.npz](../backend/embeddings.npz)
- **User history**: [backend/history.json](../backend/history.json)
- **Analysis log**: [backend/logs/analysis.log](../backend/logs/analysis.log)
- **Frontend scripts**: [js/script.js](../js/script.js)
- **Smoke test**: [backend/test_request.py](../backend/test_request.py)

**Technologies & Purposes**
- **Python**: application logic, ML helpers.
- **Flask**: lightweight REST API serving frontend and handling uploads.
- **scikit-learn**: TF‑IDF feature extraction and supervised classifier (fast, small dataset).
- **sentence-transformers + torch**: semantic embeddings for nearest-neighbor fallback when classifier confidence is low.
- **joblib / numpy**: save and load model artifacts and embeddings.
- **requests / fetch**: HTTP clients for tests and frontend communication.

**How inference works (detail)**
1. Backend receives `caseText`.
2. If classifier is available and confident (threshold `CLASSIFIER_THRESHOLD` default 0.6) it uses classifier mapping (`CLASSIFIER_MAPS`) to suggest laws.
3. If classifier is not confident, and embeddings are available, it runs semantic nearest-neighbor via `emb_classifier.predict()` and accepts suggestion when distance ≤ `EMB_THRESHOLD` (default 0.35).
4. If neither method yields a match, deterministic keyword rules are applied as a final fallback.
5. Result is saved to history with a `viewed` flag (default `false`). If a duplicate `caseText` is submitted, backend checks `viewed` and `content_changed` to decide whether to append, update, or ignore (see code in [backend/app.py](../backend/app.py#L1)).

**Frontend behavior**
- Submits cases from [index.html](../index.html) via `js/script.js` using form-encoded POSTs.
- Results saved to `localStorage` and displayed in [results.html](../results.html).
- History list shows saved analyses; clicking "View" marks an entry viewed via `/history/<id>/view` and opens `results.html`.
- Viewed entries show a green "Viewed" badge in history.

**Development / Retraining**
- Add or edit labeled examples in [backend/dataset.jsonl](../backend/dataset.jsonl).
- Retrain classifier: run `python backend/train_classifier.py` (script available in `backend/`).
- After retraining, save model to `backend/model.joblib` and optionally rebuild embeddings.

**Troubleshooting**
- If embedding build fails, ensure internet access for model download and sufficient disk/memory for `torch`.
- If server fails to start, inspect stdout in the terminal and check [backend/logs/analysis.log](../backend/logs/analysis.log) for errors.
- If `/analyze` returns 400, ensure the request uses form-encoded `caseText` or `FormData` from the frontend.

**Presentation Tips (for PPT)**
- One slide: Problem, Approach (rules → classifier → embeddings), Demo steps.
- One slide: Architecture diagram (Frontend → Flask → Classifier + Embeddings + Rules).
- One slide: Key artifacts and commands (copy Quick Start commands above).

**Next steps / Enhancements**
- Add unit tests for the inference chain.
- Add admin UI to label/merge examples and retrain from UI.
- Replace Flask dev server with a production WSGI server for deployment.

---
If you'd like, I can:
- Commit this document to the repo as `docs/PROJECT_DOCUMENTATION.md` (I already created it),
- Generate a PPT-friendly slide text file or a simple architecture PNG you can drop into your slides.
Which of those should I do next?