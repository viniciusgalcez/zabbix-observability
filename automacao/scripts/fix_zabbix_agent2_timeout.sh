#!/usr/bin/env bash
#
# fix_zabbix_agent2_timeout.sh
# -----------------------------------------------------------------------------
# Aumenta o Timeout do Zabbix Agent 2 (Linux) para resolver o erro da descoberta
# de servicos systemd:  "Timeout occurred while gathering data."
#
# O plugin Systemd do agent2 enumera as units via DBus; com muitas units e o
# Timeout padrao (3s) a coleta estoura. Subir o Timeout (ate 30s) resolve.
#
# Aplica-se SOMENTE ao agent2 (o monitoramento systemd e exclusivo do agent2).
#
# O script:
#   1. Detecta /etc/zabbix/zabbix_agent2.conf
#   2. Le o Timeout atual
#   3. Faz backup, define/substitui Timeout= (default 30)
#   4. Reinicia o servico e valida; se nao subir, restaura o backup
#
# Uso:
#   sudo ./fix_zabbix_agent2_timeout.sh        # define Timeout=30
#   sudo ./fix_zabbix_agent2_timeout.sh 20     # define Timeout=20
#   sudo DRY_RUN=1 ./fix_zabbix_agent2_timeout.sh
#
# IMPORTANTE: garanta quebra de linha LF (Unix). Se copiou do Windows:
#   sed -i 's/\r$//' fix_zabbix_agent2_timeout.sh
# -----------------------------------------------------------------------------
set -euo pipefail

log() { echo ">> $*"; }
err() { echo "ERRO: $*" >&2; }

# ---- 1. Root ----
if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  err "rode como root (sudo)."
  exit 1
fi

# ---- 2. Config do agent2 (este fix e exclusivo do agent2) ----
CONF="/etc/zabbix/zabbix_agent2.conf"
SERVICE="zabbix-agent2"
if [[ ! -f "$CONF" ]]; then
  err "$CONF nao existe. A descoberta systemd e exclusiva do agent2; nada a fazer."
  exit 1
fi

# ---- 3. Timeout alvo (1..30) ----
TARGET="${1:-30}"
if ! [[ "$TARGET" =~ ^[0-9]+$ ]] || (( TARGET < 1 || TARGET > 30 )); then
  err "Timeout invalido: '$TARGET'. Use um inteiro de 1 a 30."
  exit 1
fi

CURRENT="$(grep -E '^[[:space:]]*Timeout=' "$CONF" | tail -n1 | cut -d= -f2- | tr -d '[:space:]' || true)"
log "Config:         $CONF"
log "Timeout atual:  ${CURRENT:-<nao definido (padrao 3)>}"
log "Timeout alvo:   $TARGET"

if [[ "$CURRENT" == "$TARGET" ]]; then
  log "Ja esta em $TARGET. Nada a fazer."
  exit 0
fi

# ---- 4. Dry-run ----
if [[ "${DRY_RUN:-0}" == "1" ]]; then
  log "[DRY-RUN] definiria Timeout=$TARGET e reiniciaria $SERVICE. Nenhuma alteracao feita."
  exit 0
fi

# ---- 5. Backup ----
BACKUP="${CONF}.bak.$(date +%Y%m%d%H%M%S)"
cp -p "$CONF" "$BACKUP"
log "Backup: $BACKUP"

# ---- 6. Aplicar Timeout (substitui linha ativa ou adiciona) ----
if grep -qE '^[[:space:]]*Timeout=' "$CONF"; then
  sed -i -E "s|^[[:space:]]*Timeout=.*|Timeout=$TARGET|" "$CONF"
else
  printf '\nTimeout=%s\n' "$TARGET" >> "$CONF"
fi
log "Linha aplicada: $(grep -E '^Timeout=' "$CONF")"

# ---- 7. Reiniciar e validar ----
if ! command -v systemctl >/dev/null 2>&1; then
  log "AVISO: systemctl ausente. Config alterado; reinicie o agente manualmente."
  exit 0
fi

systemctl restart "$SERVICE"
sleep 1
if systemctl is-active --quiet "$SERVICE"; then
  log "$SERVICE reiniciado com sucesso."
else
  err "$SERVICE nao subiu apos a alteracao. Restaurando backup."
  cp -p "$BACKUP" "$CONF"
  systemctl restart "$SERVICE" || true
  exit 1
fi

log "Concluido. A descoberta 'Service units discovery' deve sair de 'nao suportado'"
log "no proximo ciclo (force em: Data collection > Hosts > Discovery > Check now)."
