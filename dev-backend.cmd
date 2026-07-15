@echo off
cd /d "%~dp0backend"

if not exist ".\.venv\Scripts\python.exe" (
  echo Backend virtual environment not found: backend\.venv
  echo Create it or install dependencies before starting the backend.
  exit /b 1
)

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
