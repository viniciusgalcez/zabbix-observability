#!/usr/bin/env bash
# Rank de sintomas link-cause no Zabbix (Fase 2 roadmap).
# Destinado ao servidor Capri / host com acesso à API — não à estação do analista.
#
# Credenciais só por ambiente (nunca no arquivo):
#   export ZABBIX_URL="http://127.0.0.1/api_jsonrpc.php"   # ou https interno
#   export ZABBIX_TOKEN="<api-token>"                      # ou ZABBIX_API_TOKEN
#
# Uso:
#   ./run_link_cause_rank.sh              # dry-run (só plano JSON)
#   ./run_link_cause_rank.sh --apply      # aplica rank + backup em backups/
#
# Cron (dry-run a cada 10 min, só log):
#   */10 * * * * . /etc/zabbix/link_cause_rank.env; /opt/zabbix-observality/scripts/run_link_cause_rank.sh >>/var/log/zabbix/link_cause_rank.log 2>&1
#
# Cron (produção — apply):
#   */10 * * * * . /etc/zabbix/link_cause_rank.env; /opt/zabbix-observality/scripts/run_link_cause_rank.sh --apply >>/var/log/zabbix/link_cause_rank.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

APPLY=0
ALLOW_HTTP=1
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --no-allow-http) ALLOW_HTTP=0 ;;
    -h|--help)
      sed -n '1,20p' "$0"
      exit 0
      ;;
  esac
done

: "${ZABBIX_URL:?Defina ZABBIX_URL}"
if [[ -z "${ZABBIX_API_TOKEN:-}${ZABBIX_TOKEN:-}" ]]; then
  echo "Defina ZABBIX_API_TOKEN ou ZABBIX_TOKEN" >&2
  exit 1
fi

PYTHON="${ZABBIX_RANK_PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python nao encontrado (${PYTHON}). Defina ZABBIX_RANK_PYTHON." >&2
  exit 1
fi

ARGS=(scripts/link_cause_rank_worker.py)
if [[ "$ALLOW_HTTP" -eq 1 ]]; then
  ARGS+=(--allow-http)
fi
if [[ "$APPLY" -eq 1 ]]; then
  ARGS+=(--apply)
fi

mkdir -p backups
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="backups/link_cause_rank_scheduled_${STAMP}.log"

echo "[$(date -Is)] start mode=$([ "$APPLY" -eq 1 ] && echo apply || echo dry-run)" | tee -a "$LOG"
set +e
"$PYTHON" "${ARGS[@]}" 2>&1 | tee -a "$LOG"
CODE=${PIPESTATUS[0]}
set -e
echo "[$(date -Is)] end exit=${CODE} log=${LOG}" | tee -a "$LOG"
exit "$CODE"
