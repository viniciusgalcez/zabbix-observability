#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Implanta o monitoramento Hyper-V para Zabbix Agent 2.
    Executar como Administrador em cada host Hyper-V:
      BGP-SRV-FHV01/02/03  SCL-SRV-FHV02/03  SPO-SRV-FAD01

.DESCRIPTION
    1. Copia os arquivos de monitoramento para o diretório do agente
    2. Instala o arquivo de configuração UserParameter
    3. Ajusta Timeout e UnsafeUserParameters no agente
    4. Configura a conta de serviço do Zabbix Agent 2 como Administrador local
    5. Configura ExecutionPolicy e desbloqueia o script PowerShell
    6. Reinicia o serviço e valida a coleta
#>

$AgentDir    = "C:\Program Files\Zabbix Agent 2"
$AgentConf   = "$AgentDir\zabbix_agent2.conf"
$ScriptSrc   = "$PSScriptRoot\hyper-v-monitoring2.ps1"
$ConfSrc     = "$PSScriptRoot\hyper-v.conf"
$ServiceName = "Zabbix Agent 2"

Write-Host "=== Deploy Hyper-V Monitoring ===" -ForegroundColor Cyan

# 1. Copiar arquivos
Write-Host "`n[1] Copiando arquivos de monitoramento..."
Copy-Item -Path $ScriptSrc -Destination "$AgentDir\hyper-v-monitoring2.ps1" -Force
Copy-Item -Path $ConfSrc   -Destination "$AgentDir\zabbix_agent2.d\hyper-v.conf" -Force
Write-Host "    OK: hyper-v-monitoring2.ps1 e hyper-v.conf copiados"

# 2. Desbloquear script (remove mark-of-the-web do Windows)
Write-Host "`n[2] Desbloqueando script PowerShell..."
Unblock-File -Path "$AgentDir\hyper-v-monitoring2.ps1"
Write-Host "    OK: script desbloqueado"

# 3. Ajustar Timeout e UnsafeUserParameters no zabbix_agent2.conf
Write-Host "`n[3] Ajustando configuração do agente..."
$conf = Get-Content $AgentConf -Raw

if ($conf -match '^\s*#?\s*Timeout\s*=') {
    $conf = $conf -replace '(?m)^\s*#?\s*Timeout\s*=.*', 'Timeout=30'
} else {
    $conf += "`nTimeout=30"
}

if ($conf -match '^\s*#?\s*UnsafeUserParameters\s*=') {
    $conf = $conf -replace '(?m)^\s*#?\s*UnsafeUserParameters\s*=.*', 'UnsafeUserParameters=1'
} else {
    $conf += "`nUnsafeUserParameters=1"
}

Set-Content -Path $AgentConf -Value $conf -NoNewline
Write-Host "    OK: Timeout=30, UnsafeUserParameters=1"

# 4. Configurar ExecutionPolicy
Write-Host "`n[4] Configurando PowerShell ExecutionPolicy..."
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force
Write-Host "    OK: RemoteSigned"

# 5. Verificar se a conta de serviço tem privilégios de Administrador local
Write-Host "`n[5] Verificando conta de serviço..."
$svc = Get-WmiObject Win32_Service -Filter "Name='$ServiceName'"
$svcAccount = $svc.StartName
Write-Host "    Conta de serviço: $svcAccount"

$admins = net localgroup Administrators 2>&1
if ($admins -match [regex]::Escape($svcAccount.Split('\')[-1])) {
    Write-Host "    OK: conta já é Administrador local"
} else {
    Write-Host "    AVISO: '$svcAccount' nao esta no grupo Administradores local." -ForegroundColor Yellow
    Write-Host "    -> Adicione manualmente: net localgroup Administrators '$svcAccount' /add" -ForegroundColor Yellow
    Write-Host "    -> Ou configure o servico para rodar como 'LocalSystem'" -ForegroundColor Yellow
}

# 6. Reiniciar serviço
Write-Host "`n[6] Reiniciando Zabbix Agent 2..."
Restart-Service -Name $ServiceName
Start-Sleep -Seconds 5
$status = (Get-Service -Name $ServiceName).Status
Write-Host "    Status: $status"

# 7. Validação rápida
Write-Host "`n[7] Validando coleta..."
try {
    $result = & powershell.exe -file "$AgentDir\hyper-v-monitoring2.ps1" "host" 2>&1
    if ($result -match '"vms"' -or $result -match 'data') {
        Write-Host "    OK: script retornou dados" -ForegroundColor Green
    } else {
        Write-Host "    Resultado: $($result | Select-Object -First 3)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    ERRO ao executar script: $_" -ForegroundColor Red
}

Write-Host "`n=== Deploy concluído em $env:COMPUTERNAME ===" -ForegroundColor Green
Write-Host "Aguarde ~30 min para o primeiro ciclo de discovery no Zabbix."
