@echo off
cd /d "%~dp0"

echo === Criando ambiente virtual Python (.venv) ===
REM Usa o "py launcher" (py -3) em vez de "python" para nao pegar por engano
REM o python.exe de outro .venv que esteja na frente no PATH (ex.: se o venv
REM do Planejamento_EDP_ES estiver ativo no terminal). Isso evita o erro
REM "Unable to copy ... venvlauncher.exe" ao criar um venv aninhado.
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r Backend\requirements.txt

if not exist Backend\.env (
    copy Backend\.env.example Backend\.env
    echo.
    echo Edite Backend\.env com o usuario e senha do Octagora, tanto SP quanto ES, antes de rodar.
)

echo.
echo === Instalando dependencias do Frontend ===
cd Frontend
call npm install
cd ..

echo.
echo Instalacao concluida. Use run_tudo.bat (ou run_backend.bat / run_frontend.bat separadamente).
pause
