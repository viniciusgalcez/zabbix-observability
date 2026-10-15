"""Padroniza nomes de hosts WEB, cenarios web e triggers de cenario.

Padrao adotado:
  - host tecnico  = nome canonico da aplicacao (sem sufixo)
  - host visivel  = "<App> (Web)"
  - cenario       = apenas a funcao (o host ja identifica a aplicacao)
  - passo         = igual a funcao do cenario
  - trigger       = "<funcao>: cenario web indisponivel"

Faz backup (configuration.export) antes de qualquer escrita.
"""
import requests
import json
import os
from datetime import datetime

ZABBIX_URL = os.environ.get("ZABBIX_URL", "http://172.17.2.51/api_jsonrpc.php")
ZABBIX_TOKEN = os.environ["ZABBIX_TOKEN"]  # exporte antes de rodar; nunca commitar

# host tecnico atual -> host tecnico novo
HOSTS = {
    "11030": "GLPI",
    "11138": "Fact",
}

# httptestid -> nome novo do cenario (= nome novo do passo unico)
CENARIOS = {
    "28": "Home",                 # Deps
    "27": "API",
    "26": "Vivo",
    "29": "Cross Connection",
    "58": "Home",                 # Deps Qa
    "59": "API",
    "32": "Instância 1",     # NodeRed
    "31": "Instância 2",
    "30": "Instância 3",
    "33": "Dashboard",            # Cisco
    "34": "Exchange Online",      # Microsoft 365
    "35": "SharePoint Online",
    "36": "Teams",
    "38": "ERP",                  # Systextil
    "37": "ERP via HAProxy",
    "40": "Folha",                # SinergyRH
    "41": "Ponto",
    "42": "SCL-ACA-UTL01",        # CLP
    "43": "SCL-TEC2-UTL01",
    "44": "SCL-TIN-UTL01",
    "45": "OMNI Capricórnio",  # Plusoft
    "46": "PicConnect",           # Picanol
    "47": "Home",                 # Paytrack
    "48": "Home",                 # NDD Print 360
    "49": "Home",                 # Lansweeper
    "50": "Site",                 # Capricornio
    "51": "Home",                 # Base-B
    "52": "Home",                 # Projuris
    "53": "Home",                 # GLPI
    "62": "Home",                 # Grafana
    "63": "Login",                # Portal de OS
    "64": "BGP",                  # Fact
    "65": "SCL",
    "70": "Home",                 # inPaaS
    "71": "API",                  # Arquivei
    "72": "Hook",                 # Make
}

# triggerid -> funcao do cenario correspondente
TRIGGERS = {
    "45793": "Home", "45795": "API", "45794": "Vivo", "45792": "Cross Connection",
    "50130": "Home", "50129": "API",
    "45796": "Instância 1", "45797": "Instância 2", "45798": "Instância 3",
    "45799": "Dashboard",
    "45810": "Exchange Online", "45806": "SharePoint Online", "45807": "Teams",
    "45804": "ERP", "45835": "ERP via HAProxy",
    "45803": "Folha", "45802": "Ponto",
    "45811": "SCL-ACA-UTL01", "45812": "SCL-TEC2-UTL01", "45813": "SCL-TIN-UTL01",
    "45815": "OMNI Capricórnio",
    "45816": "PicConnect",
    "45817": "Home", "45818": "Home", "45821": "Home",
    "45824": "Site",
    "45827": "Home", "45828": "Home", "45829": "Home",
    "50136": "Home", "50137": "Login",
    "50138": "BGP", "50139": "SCL",
    "50309": "Home", "50310": "API", "50311": "Hook",
}

TRIGGER_FMT = "{}: cenário web indisponível"


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
    hostids = sorted({t["hostid"] for t in zabbix_api("httptest.get", {"output": ["hostid"]})})
    export = zabbix_api("configuration.export",
                        {"format": "json", "options": {"hosts": hostids}})
    os.makedirs("backups", exist_ok=True)
    path = f"backups/backup_padroniza_web_{datetime.now():%Y%m%d_%H%M%S}.json"
    with open(path, "w", encoding="utf-8") as f:
        f.write(export)
    print(f"[backup] {path} ({len(hostids)} hosts)")


def main():
    backup()

    # 1) hosts
    for hostid, novo in HOSTS.items():
        atual = zabbix_api("host.get", {"hostids": [hostid], "output": ["host", "name"]})[0]
        if atual["host"] == novo:
            print(f"[host {hostid}] ja padronizado ({novo})")
            continue
        zabbix_api("host.update", {"hostid": hostid, "host": novo})
        print(f"[host {hostid}] '{atual['host']}' -> '{novo}'  (visivel: {atual['name']})")

    # 2) cenarios + passos
    tests = zabbix_api("httptest.get", {
        "httptestids": list(CENARIOS),
        "output": ["httptestid", "name"],
        "selectSteps": "extend",
        "selectHosts": ["name"],
    })
    for t in tests:
        novo = CENARIOS[t["httptestid"]]
        steps = []
        for s in sorted(t["steps"], key=lambda x: int(x["no"])):
            step = {k: s[k] for k in ("httpstepid", "name", "url", "no", "status_codes",
                                      "timeout", "required", "follow_redirects",
                                      "retrieve_mode") if k in s}
            # passo unico herda o nome do cenario; multi-step mantem o nome proprio
            if len(t["steps"]) == 1:
                step["name"] = novo
            steps.append(step)
        if t["name"] == novo and all(s["name"] == o["name"] for s, o in zip(steps, sorted(t["steps"], key=lambda x: int(x["no"])))):
            print(f"[cenario {t['httptestid']}] ja padronizado")
            continue
        zabbix_api("httptest.update", {"httptestid": t["httptestid"], "name": novo, "steps": steps})
        host = t["hosts"][0]["name"]
        print(f"[cenario {t['httptestid']}] '{t['name']}' -> '{novo}'   ({host} - {novo})")

    # 3) triggers
    trs = zabbix_api("trigger.get", {"triggerids": list(TRIGGERS), "output": ["triggerid", "description"]})
    for tr in trs:
        novo = TRIGGER_FMT.format(TRIGGERS[tr["triggerid"]])
        if tr["description"] == novo:
            print(f"[trigger {tr['triggerid']}] ja padronizado")
            continue
        zabbix_api("trigger.update", {"triggerid": tr["triggerid"], "description": novo})
        print(f"[trigger {tr['triggerid']}] '{tr['description']}' -> '{novo}'")

    print("\nOK.")


if __name__ == "__main__":
    main()
