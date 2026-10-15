@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run start_windows.bat or follow README.md to create the environment first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pytest -q
pause
