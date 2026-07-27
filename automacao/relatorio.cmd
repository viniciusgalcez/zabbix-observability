@echo off
REM Atalho para gerar o relatorio de indisponibilidade usando o Python correto (env zabbix-mcp).
REM Uso:
REM   relatorio.cmd                              (mes corrente ate agora)
REM   relatorio.cmd --from 2026-06-01 --to 2026-07-01
REM   relatorio.cmd --group "Switches Cisco/BGP"
setlocal
set "PY=C:\Users\vinicius.galcez\AppData\Local\anaconda3\envs\zabbix-mcp\python.exe"
if not exist "%PY%" (
  echo [ERRO] Interpretador Python nao encontrado em: %PY%
  echo Ajuste a variavel PY neste .cmd para o python do env zabbix-mcp.
  exit /b 1
)
"%PY%" "%~dp0gen_availability_report.py" %*
endlocal
