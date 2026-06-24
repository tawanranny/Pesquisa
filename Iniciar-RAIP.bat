@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Organizador de Pesquisa - RAIP

echo ============================================================
echo    ORGANIZADOR DE PESQUISA - RAIP
echo ============================================================
echo.

REM Descobre o comando do Python (python ou py)
python --version >nul 2>&1
if %errorlevel%==0 goto usar_python
py --version >nul 2>&1
if %errorlevel%==0 goto usar_py

echo [ERRO] Python nao encontrado.
echo.
echo Instale o Python em https://www.python.org/downloads/
echo e marque a caixa "Add Python to PATH" durante a instalacao.
echo Depois rode este arquivo de novo.
echo.
pause
exit /b

:usar_py
set PY=py
goto instalar

:usar_python
set PY=python
goto instalar

:instalar
echo [1/2] Instalando os componentes necessarios...
echo       (Na PRIMEIRA vez demora alguns minutos. Depois e rapido.)
echo.
%PY% -m pip install --quiet --upgrade pip
%PY% -m pip install --quiet -r requirements.txt

echo.
echo [2/2] Abrindo o aplicativo no seu navegador...
echo       Endereco: http://127.0.0.1:5000
echo.
echo  ^>^>^> Para FECHAR o aplicativo depois, feche esta janela preta. ^<^<^<
echo.
%PY% servidor.py

pause
