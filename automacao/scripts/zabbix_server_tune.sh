#!/usr/bin/env bash
# Ajusta ValueCacheSize e StartPingers no zabbix_server.conf e reinicia o serviço.
# Executar como root no servidor Zabbix (172.17.2.51).

set -euo pipefail

CONF="/etc/zabbix/zabbix_server.conf"
BACKUP="${CONF}.bak.$(date +%Y%m%d_%H%M%S)"

echo "==> Backup: $BACKUP"
cp "$CONF" "$BACKUP"

# ValueCacheSize: se já existe (comentado ou não), substitui; senão, acrescenta
if grep -qE '^\s*#?\s*ValueCacheSize\s*=' "$CONF"; then
    sed -i 's|^\s*#\?\s*ValueCacheSize\s*=.*|ValueCacheSize=64M|' "$CONF"
else
    echo "ValueCacheSize=64M" >> "$CONF"
fi

# StartPingers: idem
if grep -qE '^\s*#?\s*StartPingers\s*=' "$CONF"; then
    sed -i 's|^\s*#\?\s*StartPingers\s*=.*|StartPingers=3|' "$CONF"
else
    echo "StartPingers=3" >> "$CONF"
fi

echo "==> Configuração aplicada:"
grep -E 'ValueCacheSize|StartPingers' "$CONF"

echo "==> Reiniciando zabbix-server..."
systemctl restart zabbix-server

echo "==> Aguardando serviço subir (10s)..."
sleep 10

systemctl is-active zabbix-server && echo "==> zabbix-server: OK" || echo "==> ERRO: serviço não subiu — verifique: journalctl -u zabbix-server -n 50"
