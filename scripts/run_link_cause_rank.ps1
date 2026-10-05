#Requires -Version 5.1
<#
.SYNOPSIS
  Executa o rank de sintomas link-cause no Zabbix (Fase 2 roadmap).

.DESCRIPTION
  Destinado ao servidor/automacao Capri (NAO a estacao do analista).
  Credenciais apenas por variaveis de ambiente — nunca hardcoded.

  Agendar (exemplo Task Scheduler, a cada 10 min):
    Program: powershell.exe
    Args: -NoProfile -ExecutionPolicy Bypass -File "C:\path\to\run_link_cause_rank.ps1" -Apply
    Env:  ZABBIX_URL, ZABBIX_TOKEN (ou ZABBIX_API_TOKEN)

.PARAMETER Apply
  Sem -Apply roda dry-run (so imprime plano).

.PARAMETER AllowHttp
  Necessario se ZABBIX_URL for http interno (lab Capri).
#>
param(
    [switch]$Apply,
    [switch]$AllowHttp = $true,
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
Set-Location $RepoRoot

if (-not $env:ZABBIX_URL) {
    throw "ZABBIX_URL nao definido"
}
if (-not ($env:ZABBIX_API_TOKEN -or $env:ZABBIX_TOKEN)) {
    throw "ZABBIX_API_TOKEN ou ZABBIX_TOKEN nao definido"
}

$pyCandidates = @(
    $env:ZABBIX_RANK_PYTHON,
    "C:\Users\vinicius.galcez\AppData\Local\miniconda3\envs\zabbix-mcp\python.exe",
    "python"
) | Where-Object { $_ }

$python = $null
foreach ($c in $pyCandidates) {
    if ($c -eq "python") {
        $python = "python"
        break
    }
    if (Test-Path $c) {
        $python = $c
        break
    }
}
if (-not $python) {
    throw "Python nao encontrado. Defina ZABBIX_RANK_PYTHON."
}

$argsList = @("scripts\link_cause_rank_worker.py")
if ($AllowHttp) { $argsList += "--allow-http" }
if ($Apply) { $argsList += "--apply" }

$logDir = Join-Path $RepoRoot "backups"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}
$stamp = Get-Date -Format "yyyyMMddTHHmmssZ"
$log = Join-Path $logDir "link_cause_rank_scheduled_$stamp.log"

& $python @argsList 2>&1 | Tee-Object -FilePath $log
$code = $LASTEXITCODE
if ($code -ne 0) {
    throw "link_cause_rank_worker saiu com codigo $code (log: $log)"
}
Write-Host "OK log=$log"
