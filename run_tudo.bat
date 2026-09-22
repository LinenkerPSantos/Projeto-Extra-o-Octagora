@echo off
REM Sobe Backend e Frontend cada um em sua propria janela.
cd /d "%~dp0"

start "Octagora - Backend" cmd /k call run_backend.bat
timeout /t 3 /nobreak >nul
start "Octagora - Frontend" cmd /k call run_frontend.bat
