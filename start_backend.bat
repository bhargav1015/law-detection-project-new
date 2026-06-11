@echo off
REM Activate virtual environment and run backend (Windows)
call backend\venv\Scripts\activate.bat
python backend\app.py
pause
