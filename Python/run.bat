@echo off
cd /d "%~dp0"
if not exist ".venv" (
  py -m venv .venv
  call .venv\Scripts\activate.bat
  python -m pip install --upgrade pip
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate.bat
)
start "" http://localhost:8501
python -m streamlit run app.py
