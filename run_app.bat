@echo off
:: Change directory to the folder where this batch file lives
cd /d "%~dp0"
:: Run the app using the absolute Python module call
python -m streamlit run app.py
pause