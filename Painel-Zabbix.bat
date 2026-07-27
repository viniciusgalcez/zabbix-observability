@echo off
chcp 65001 >nul
title Zabbix - Painel ao vivo
setlocal enabledelayedexpansion

rem ==========================================================================
rem  Sobe o painel local do Zabbix (puxa dados ao vivo via API, somente leitura)
rem  Duplo clique para iniciar. Abre http://localhost:8077 no navegador.
rem ==========================================================================

rem Python do ambiente anaconda 'zabbix-mcp'
set "PY=C:\Users\vinicius.galcez\AppData\Local\anaconda3\envs\zabbix-mcp\python.exe"

rem Pasta onde esta o .bat (raiz do projeto)
set "RAIZ=%~dp0"
set "APP=%RAIZ%automacao"

echo ============================================================
echo   Zabbix - Painel ao vivo
echo ============================================================

if not exist "%PY%" (
  echo.
  echo [ERRO] Python nao encontrado em:
  echo        %PY%
  echo Ajuste a variavel PY neste .bat com o caminho correto.
  echo.
  pause
  exit /b 1
)

if not exist "%APP%\zabbix_dashboard.py" (
  echo.
  echo [ERRO] Nao achei automacao\zabbix_dashboard.py ao lado deste .bat.
  echo.
  pause
  exit /b 1
)

cd /d "%APP%"

echo.
echo  Iniciando... o navegador abre sozinho em alguns segundos.
echo  Acesse:  http://localhost:8077
echo  Para PARAR: feche esta janela ou pressione Ctrl+C.
echo ============================================================
echo.

"%PY%" zabbix_dashboard.py

echo.
echo Painel encerrado.
pause
