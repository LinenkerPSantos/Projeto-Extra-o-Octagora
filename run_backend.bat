@echo off
cd /d "%~dp0"
cd Backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

echo.
echo O Backend foi encerrado ou falhou ao iniciar. Veja a mensagem acima.
pause
