@echo off
echo ========================================
echo   LexAssist Combined - RAG Enhanced
echo   Indian Legal & Tax AI Assistant
echo ========================================
echo.

set ROOT=%~dp0
set VENV=%ROOT%.venv
set PYTHON=%VENV%\Scripts\python.exe
set PIP=%VENV%\Scripts\pip.exe
set STREAMLIT=%VENV%\Scripts\streamlit.exe

echo Checking virtual environment...
if not exist "%PYTHON%" (
    echo Virtual environment not found. Creating one...
    python -m venv "%VENV%"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment. Make sure Python 3.10+ is installed.
        pause
        exit /b 1
    )
    echo Installing dependencies...
    "%PIP%" install -r "%ROOT%requirements.txt"
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies.
        pause
        exit /b 1
    )
    echo.
)

echo [1/2] Starting Backend Server (FastAPI + RAG)...
start "LexAssist Backend" cmd /k ""%PYTHON%" "%ROOT%backend\main.py""
timeout /t 3 /nobreak > nul
echo Backend started at http://localhost:8000
echo.

echo [2/2] Starting Frontend Application (Streamlit)...
timeout /t 2 /nobreak > nul
start "LexAssist Frontend" cmd /k ""%STREAMLIT%" run "%ROOT%frontend\app.py""
echo Frontend will open in your browser at http://localhost:8501
echo.

echo ========================================
echo Both servers are starting...
echo.
echo Backend API:   http://localhost:8000
echo API Docs:      http://localhost:8000/docs
echo Frontend UI:   http://localhost:8501
echo.
echo Press any key to close this window
echo ========================================
pause > nul
