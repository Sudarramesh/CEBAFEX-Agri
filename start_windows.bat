@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3.12 -m venv .venv
  if errorlevel 1 py -3.11 -m venv .venv
  if errorlevel 1 goto fail
)
".venv\Scripts\python.exe" -c "import streamlit, pandas, plotly, sklearn, openpyxl" >nul 2>&1
if errorlevel 1 (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto fail
)
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 goto fail
exit /b 0
:fail
echo Could not start CEBAFEX. Read the error above and follow README.md.
pause
exit /b 1
