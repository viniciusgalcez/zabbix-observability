#!/bin/bash
# Adiciona rotas /32 específicas para os servidores Capricórnio via ppp0.
# Necessário porque Docker cria rotas /16 mais específicas que a rota VPN /12,
# impedindo o tráfego para 172.17.x.x e 172.18.x.x de sair pela VPN.
#
# Uso manual:   sudo bash scripts/vpn-routes-up.sh
# Uso automático via pppd: ver scripts/ppp-ip-up.sh

IFACE="${1:-ppp0}"

HOSTS=(
    "172.17.2.51"   # SPO-SRV-V01 — Zabbix Server
    "172.17.2.52"   # SPO-SRV-V02 — PostgreSQL
    "172.17.2.53"   # SPO-SRV-V03 — Grafana
    "172.17.2.54"   # SPO-SRV-V04 — Zabbix Proxy
    "172.18.2.51"   # BGP-SRV-V08 — Zabbix Proxy
    "172.16.2.51"   # SCL-SRV-V08 - Zabbix Proxy
)

echo "Adicionando rotas Capricórnio via $IFACE..."
for HOST in "${HOSTS[@]}"; do
    ip route replace "${HOST}/32" dev "$IFACE"
    echo "  -> ${HOST}/32 via $IFACE"
done
echo "Pronto."
