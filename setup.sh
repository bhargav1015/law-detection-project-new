#!/usr/bin/env bash
set -euo pipefail
BUILD=${1:-0}

python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if [ "$BUILD" = "1" ]; then
  python backend/emb_classifier.py --build
fi

echo "Setup complete. Run the backend in free/offline mode with:"
echo "  FREE_MODE=1 python backend/app.py"