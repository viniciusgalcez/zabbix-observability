#!/bin/bash
# Hook pppd — remove rotas Capricórnio quando a VPN desconecta.
# Instalar em: /etc/ppp/ip-down.d/99-capricornio

IFACE="$1"
REMOTE_IP="$5"

[ "$REMOTE_IP" != "169.254.2.1" ] && exit 0

HOSTS=(
    "172.17.2.51"
    "172.17.2.52"
    "172.17.2.53"
    "172.17.2.54"
    "172.18.2.51"
)

for HOST in "${HOSTS[@]}"; do
    ip route del "${HOST}/32" dev "$IFACE" 2>/dev/null
done
