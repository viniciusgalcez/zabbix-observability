@echo off
REM Sobe um servidor HTTP local e abre o NOC Geomap NO CHROME/EDGE (Chromium).
REM Importante: NAO abrir no Internet Explorer / Edge legado -> a pagina fica preta
REM (o JavaScript moderno nao roda neles). Servir por http:// tambem evita o erro
REM de "file: URLs are unique security origins" que bloqueia os tiles do mapa.
cd /d "%~dp0"
set "PY=C:\Users\vinicius.galcez\AppData\Local\anaconda3\envs\zabbix-mcp\python.exe"
if not exist "%PY%" (
  echo [ERRO] Python do env zabbix-mcp nao encontrado em: %PY%
  pause
  exit /b 1
)

REM escolhe um navegador Chromium (Chrome preferido, senao Edge)
set "BROWSER=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist "%BROWSER%" set "BROWSER=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not exist "%BROWSER%" set "BROWSER=C:\Program Files\Microsoft\Edge\Application\msedge.exe"

start "NOC Geomap server" "%PY%" -m http.server 8899
timeout /t 2 >nul
if exist "%BROWSER%" (
  start "" "%BROWSER%" "http://localhost:8899/noc-geomap.html"
) else (
  echo [AVISO] Chrome/Edge nao encontrado; abrindo no navegador padrao.
  start "" "http://localhost:8899/noc-geomap.html"
)
echo.
echo NOC Geomap: http://localhost:8899/noc-geomap.html
echo Navegador: %BROWSER%
echo Deixe a janela "NOC Geomap server" aberta. Feche-a para parar o servidor.
echo.
