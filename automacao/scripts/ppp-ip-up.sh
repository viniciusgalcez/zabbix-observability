#!/bin/bash
# Hook pppd — executado automaticamente quando qualquer interface ppp sobe.
# Instalar em: /etc/ppp/ip-up.d/99-capricornio
#
# Argumentos passados pelo pppd:
#   $1 = interface (ex: ppp0)
#   $2 = tty device
#   $3 = velocidade
#   $4 = IP local
#   $5 = IP remoto (gateway do túnel)
#   $6 = ipparam

IFACE="$1"
REMOTE_IP="$5"

# Aplica apenas para a VPN Capricórnio (gateway 169.254.2.1)
[ "$REMOTE_IP" != "169.254.2.1" ] && exit 0

HOSTS=(
    "172.17.2.51"
    "172.17.2.52"
    "172.17.2.53"
    "172.17.2.54"
    "172.18.2.51"
)

for HOST in "${HOSTS[@]}"; do
    ip route replace "${HOST}/32" dev "$IFACE"
done
