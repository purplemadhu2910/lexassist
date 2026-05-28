@echo off
echo ========================================
echo   LexAssist Combined - RAG Enhanced
echo   Indian Legal & Tax AI Assistant
echo ========================================
echo.

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)
echo.

echo Starting LexAssist Combined servers...
echo.

echo [1/2] Starting Backend Server (FastAPI + RAG)...
start "LexAssist Backend" cmd /k "cd backend && python main.py"
timeout /t 3 /nobreak > nul
echo Backend started at http://localhost:8000
echo.

echo [2/2] Starting Frontend Application (Streamlit)...
timeout /t 2 /nobreak > nul
start "LexAssist Frontend" cmd /k "cd frontend && streamlit run app.py"
echo Frontend will open in your browser at http://localhost:8501
echo.

echo ========================================
echo Both servers are starting...
echo.
echo Backend API:   http://localhost:8000
echo API Docs:      http://localhost:8000/docs
echo Frontend UI:   http://localhost:8501
echo.
echo RAG Knowledge Base: 217 chunks from Indian legal docs
echo.
echo Press any key to close this window
echo ========================================
pause > nul
