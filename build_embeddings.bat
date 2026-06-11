@echo off
if exist venv\Scripts\activate (
  call venv\Scripts\activate
) else (
  python -m venv venv
  call venv\Scripts\activate
)
python backend/emb_classifier.py --build
echo Embeddings built: backend\embeddings.npz