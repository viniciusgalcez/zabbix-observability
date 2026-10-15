"""Corrige flapping identificado no SLA (Dimep/EAS Cozinha, Sinergy - Folha/Ponto).

Contexto: triggers disparavam com um unico poll acima do normal (last(item)>X),
sem histerese. Historico mostrou blips de exatos 60-120s (1 ciclo de coleta)
que nao representam indisponibilidade real, mas contavam contra o SLA.

Correcoes:
  1. Trigger prototype "MSSQL: DB '{#DBNAME}': State is {ITEM.VALUE}"
     (template "MSSQL by Zabbix agent 2", triggerid 23570): last(item)>1
     -> min(item,#2)>1. Exige 2 leituras consecutivas antes de abrir o
     problema. Afeta as 24 triggers "DB State" discovered nos 3 hosts MSSQL
     (11003, 11004, 11005) — nao ha como escopar so 2 instancias porque
     triggers vindos de LLD/template so podem ser editados no prototype.

  2. Triggers "Folha: cenario web indisponivel" (45803) e "Ponto: cenario
     web indisponivel" (45802), host SinergyRH: last(web.test.fail[..])>0
     -> min(web.test.fail[..],#2)>0.

  3. Tag duplicada no host SCL-SRV-VAPP02-DB: tinha negocio=dimep E
     negocio=eas-cozinha ao mesmo tempo, fazendo cada flap da base MAESTRO
     contar 2x no SLA (Dimep e EAS Cozinha). Nenhuma base nesse host
     pertence de fato a EAS Cozinha (confirmado: servico "EAS Cozinha Banco"
     nao tem problem_tags configuradas). Tag removida, mantendo so
     negocio=dimep.

Backup em backups/backup_flapping_fix_<timestamp>.json antes de qualquer
alteracao.
"""
import os
import requests
from datetime import datetime

ZABBIX_URL = os.environ.get("ZABBIX_URL", "http://172.17.2.51/api_jsonrpc.php")
ZABBIX_TOKEN = os.environ["ZABBIX_TOKEN"]


def zabbix_api(method, params=None):
    payload = {"jsonrpc": "2.0", "method": method, "params": params or {},
               "auth": ZABBIX_TOKEN, "id": 1}
    r = requests.post(ZABBIX_URL, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise Exception(f"{method}: {data['error']}")
    return data["result"]


def backup():
    export = zabbix_api("configuration.export", {
        "format": "json",
        "options": {"hosts": ["11005", "11020"]},
    })
    os.makedirs("backups", exist_ok=True)
    path = f"backups/backup_flapping_fix_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(path, "w", encoding="utf-8") as f:
        f.write(export)
    print(f"[backup] {path}")


def main():
    backup()

    zabbix_api("triggerprototype.update", {
        "triggerid": "23570",
        "expression": 'min(/MSSQL by Zabbix agent 2/mssql.db.state["{#DBNAME}"],#2)>1',
    })
    print("[triggerprototype 23570] histerese aplicada (propaga em ate 1h via LLD)")

    zabbix_api("trigger.update", {
        "triggerid": "45803",
        "expression": "min(/SinergyRH/web.test.fail[Folha],#2)>0",
    })
    print("[trigger 45803] Folha: histerese aplicada")

    zabbix_api("trigger.update", {
        "triggerid": "45802",
        "expression": "min(/SinergyRH/web.test.fail[Ponto],#2)>0",
    })
    print("[trigger 45802] Ponto: histerese aplicada")

    zabbix_api("host.update", {
        "hostid": "11005",
        "tags": [{"tag": "negocio", "value": "dimep"}],
    })
    print("[host 11005] tag 'eas-cozinha' removida (duplicidade no SLA)")

    print("\nOK.")


if __name__ == "__main__":
    main()
