<#
PowerShell setup script for Windows.
Usage:
  ./setup.ps1            # creates venv and installs requirements
  ./setup.ps1 -BuildEmbeddings  # also builds embeddings
#>
[CmdletBinding()]
param(
    [switch]$BuildEmbeddings
)

python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
if ($BuildEmbeddings) {
    python backend/emb_classifier.py --build
}

Write-Host "Setup complete. To run backend in free/offline mode:"
Write-Host "  `$env:FREE_MODE='1'; python backend/app.py`"