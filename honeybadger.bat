@echo off
cd /d "%~dp0"
REM Start Ollama server if not already running
tasklist /fi "imagename eq ollama.exe" 2>nul | find /i "ollama.exe" >nul
if errorlevel 1 (
    echo Starting Ollama server...
    start "HoneyBadger Ollama" cmd /c "ollama serve"
    timeout /t 5 /nobreak >nul
) else (
    echo Ollama is already running.
)
echo Launching HoneyBadger...
"%~dp0.venv\Scripts\python.exe" "%~dp0src\honeybadger\main.py"
if errorlevel 1 (
    echo.
    echo ERROR: HoneyBadger failed to start. See message above.
    pause
)
