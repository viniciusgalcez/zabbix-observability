#!/usr/bin/env bash
#
# fix_zabbix_hostname.sh
# -----------------------------------------------------------------------------
# Ajusta o parametro Hostname do Zabbix Agent (Linux) para MAIUSCULAS.
# Motivo: as maquinas Linux estavam registrando/enviando o hostname em minusculo
# (o agente usa system.hostname por padrao), divergindo do padrao do ambiente.
#
# O script:
#   1. Detecta o config (zabbix_agent2.conf ou zabbix_agentd.conf)
#   2. Calcula o Hostname alvo (hostname curto em MAIUSCULO) ou usa o argumento
#   3. Faz backup do config
#   4. Define/substitui a linha Hostname= (e comenta HostnameItem= se existir)
#   5. Reinicia o servico e valida; se nao subir, restaura o backup
#
# Uso:
#   sudo ./fix_zabbix_hostname.sh                 # usa o hostname curto em MAIUSCULO
#   sudo ./fix_zabbix_hostname.sh BGP-SRV-APP01   # define um hostname especifico
#   sudo DRY_RUN=1 ./fix_zabbix_hostname.sh       # so mostra o que faria, sem alterar
#
# IMPORTANTE: salve este arquivo com quebra de linha LF (Unix). Se copiou do
# Windows, rode antes:  sed -i 's/\r$//' fix_zabbix_hostname.sh
# -----------------------------------------------------------------------------
set -euo pipefail

log() { echo ">> $*"; }
err() { echo "ERRO: $*" >&2; }

# ---- 1. Precisa ser root (editar config + reiniciar servico) ----
if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  err "rode como root (sudo)."
  exit 1
fi

# ---- 2. Descobrir o arquivo de configuracao do agente ----
CONF=""
for c in /etc/zabbix/zabbix_agent2.conf /etc/zabbix/zabbix_agentd.conf; do
  [[ -f "$c" ]] && CONF="$c" && break
done
if [[ -z "$CONF" ]]; then
  err "nenhum config do Zabbix agent encontrado em /etc/zabbix/."
  exit 1
fi
if [[ "$CONF" == *agent2* ]]; then SERVICE="zabbix-agent2"; else SERVICE="zabbix-agent"; fi

# ---- 3. Definir o hostname alvo (MAIUSCULO) ----
if [[ $# -ge 1 && -n "${1:-}" ]]; then
  TARGET="$1"
else
  TARGET="$(hostname -s | tr '[:lower:]' '[:upper:]')"
fi

log "Config:          $CONF"
log "Servico:         $SERVICE"
log "Hostname alvo:   $TARGET"

# ---- 4. Valor atual no config ----
CURRENT="$(grep -E '^[[:space:]]*Hostname=' "$CONF" | tail -n1 | cut -d= -f2- || true)"
log "Hostname atual:  ${CURRENT:-<nao definido>}"

if [[ "$CURRENT" == "$TARGET" ]]; then
  log "Ja esta correto. Nada a fazer."
  exit 0
fi

# ---- 5. Dry-run ----
if [[ "${DRY_RUN:-0}" == "1" ]]; then
  log "[DRY-RUN] definiria Hostname=$TARGET e reiniciaria $SERVICE. Nenhuma alteracao feita."
  exit 0
fi

# ---- 6. Backup ----
BACKUP="${CONF}.bak.$(date +%Y%m%d%H%M%S)"
cp -p "$CONF" "$BACKUP"
log "Backup: $BACKUP"

# ---- 7. Aplicar Hostname (substitui linha ativa ou adiciona) ----
if grep -qE '^[[:space:]]*Hostname=' "$CONF"; then
  sed -i -E "s|^[[:space:]]*Hostname=.*|Hostname=$TARGET|" "$CONF"
else
  printf '\nHostname=%s\n' "$TARGET" >> "$CONF"
fi
# HostnameItem ativo causaria ambiguidade (Hostname tem prioridade); comenta se houver
sed -i -E 's|^[[:space:]]*(HostnameItem=)|# \1|' "$CONF"

log "Linha aplicada:  $(grep -E '^Hostname=' "$CONF")"

# ---- 8. Reiniciar e validar ----
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

log "Concluido. Confira no Zabbix se o host passou a aparecer como '$TARGET'."
