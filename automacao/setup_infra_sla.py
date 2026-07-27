#!/usr/bin/env python3
"""
setup_infra_sla.py
-----------------------------------------------------------------------------
Monta o SLA de Infraestrutura de Rede (firewall, switch, AP, UPS, NAS) no Zabbix.
Tudo idempotente. Faz, em ordem:

  A) TUNING das macros (reduz ruido):
       Cisco IOS by SNMP / FortiGate by SNMP : {$IF.ERRORS.WARN}=10
       Aruba IAP by SNMPv3                   : {$ICMP_LOSS_WARN}=30, {$ICMP_RESPONSE_TIME_WARN}=0.30
  B) TAG scope=availability nos triggers de disponibilidade dos templates oficiais
       (Unavailable by ICMP ping / No SNMP data collection).
  C) TAG nos hosts: infra=<tipo> + site=<bgp|scl|spo>  (por host group).
  D) SERVICOS (BSM): "Infraestrutura de Rede" -> 5 filhos por tipo (problem tags),
       cada filho com service-tag slatier=infra.
  E) SLA "Infraestrutura de Rede" (99,5%, mensal, 24x7) mapeado por slatier=infra.

Precisa de TOKEN ADMIN com escrita (o usuario MCP e read-only).

Uso:
  ZBX_URL=http://172.17.2.51/api_jsonrpc.php ZBX_TOKEN=<token_admin> python setup_infra_sla.py --dry-run
  ZBX_URL=http://172.17.2.51/api_jsonrpc.php ZBX_TOKEN=<token_admin> python setup_infra_sla.py
-----------------------------------------------------------------------------
"""
import os, sys, json, time, urllib.request

URL = os.environ.get("ZBX_URL", "http://172.17.2.51/api_jsonrpc.php")
TOKEN = os.environ.get("ZBX_TOKEN", "")
DRY = "--dry-run" in sys.argv

SLO = "99.5"                       # meta de disponibilidade (%)
SLA_NAME = "SLA Infraestrutura de Rede"
ROOT_SERVICE = "Infraestrutura de Rede"
SLATIER = "infra"                  # service-tag que o SLA enxerga

# ---- A) macros a tunar por template -----------------------------------------
TUNE = {
    "Cisco IOS by SNMP":  {"{$IF.ERRORS.WARN}": "10"},
    "FortiGate by SNMP":  {"{$IF.ERRORS.WARN}": "10"},
    "Aruba IAP by SNMPv3": {"{$ICMP_LOSS_WARN}": "30", "{$ICMP_RESPONSE_TIME_WARN}": "0.30"},
}

# ---- B) templates onde marcar scope=availability nos triggers de disponibilidade
#       (casa por substring na descricao, robusto a variacoes de nome) ---------
AVAIL_TEMPLATES = ["Template Module ICMP Ping", "Cisco IOS by SNMP",
                   "FortiGate by SNMP", "SNMP QNAP", "Aruba IAP by SNMPv3"]
AVAIL_MATCH = ["icmp ping", "no snmp data"]   # lower-case substrings

# ---- C) host group -> (infra, site) -----------------------------------------
GROUP_INFRA = {
    "Firewalls": "firewall",
    "Switches Cisco": "switch",
    "Access Points Aruba": "ap",
    "UPS": "ups",
    "NAS QNAP": "nas",
}
# correcoes pontuais (host fora do padrao do grupo)
HOST_INFRA_OVERRIDE = {"BGP-CPD-SW05": "switch"}   # esta no grupo NAS mas e switch

# ---- D) tipos -> rotulo do servico ------------------------------------------
TYPES = [
    ("firewall", "Firewalls"),
    ("switch",   "Switches"),
    ("ap",       "Access Points"),
    ("ups",      "No-breaks (UPS)"),
    ("nas",      "NAS QNAP"),
]


def call(method, params):
    body = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Content-Type": "application/json-rpc", "Authorization": f"Bearer {TOKEN}"})
    r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    if "error" in r:
        raise RuntimeError(f"{method}: {r['error']}")
    return r["result"]


def site_of(group_name):
    for s in ("BGP", "SCL", "SPO"):
        if group_name.upper().endswith("/" + s):
            return s.lower()
    return None


# =============================================================================
def step_A_tuning():
    print("\n== A) Tuning de macros ==")
    tpls = call("template.get", {"output": ["templateid", "host"],
                                 "filter": {"host": list(TUNE)}})
    tid = {t["host"]: t["templateid"] for t in tpls}
    for tname, macros in TUNE.items():
        if tname not in tid:
            print(f"   [skip] template ausente: {tname}"); continue
        cur = call("usermacro.get", {"output": ["hostmacroid", "macro", "value"],
                                     "hostids": tid[tname]})
        curmap = {m["macro"]: m for m in cur}
        for macro, val in macros.items():
            if macro in curmap:
                if curmap[macro]["value"] == val:
                    continue
                print(f"   ~ {tname}: {macro} {curmap[macro]['value']} -> {val}")
                if not DRY:
                    call("usermacro.update", {"hostmacroid": curmap[macro]["hostmacroid"], "value": val})
            else:
                print(f"   + {tname}: {macro} = {val}")
                if not DRY:
                    call("usermacro.create", {"hostid": tid[tname], "macro": macro, "value": val})


def step_B_trigger_tags():
    print("\n== B) Tag scope=availability nos triggers de disponibilidade ==")
    trg = call("trigger.get", {"output": ["triggerid", "description"],
                               "selectTags": ["tag", "value"],
                               "filter": {"host": AVAIL_TEMPLATES}})
    done = 0
    for t in trg:
        d = t["description"].lower()
        if not any(m in d for m in AVAIL_MATCH):
            continue
        tags = t.get("tags", [])
        if any(x["tag"] == "scope" and x["value"] == "availability" for x in tags):
            continue
        print(f"   + [{t['description']}] -> scope=availability")
        done += 1
        if not DRY:
            newtags = [{"tag": x["tag"], "value": x["value"]} for x in tags]
            newtags.append({"tag": "scope", "value": "availability"})
            call("trigger.update", {"triggerid": t["triggerid"], "tags": newtags})
    if not done:
        print("   (nada a fazer - ja marcados)")


def step_C_host_tags():
    print("\n== C) Tags infra/site nos hosts ==")
    groups = call("hostgroup.get", {"output": ["groupid", "name"]})
    # grupo -> (infra, site)
    plan = {}   # groupid -> (infra, site)
    for g in groups:
        prefix = g["name"].split("/")[0]
        infra = GROUP_INFRA.get(prefix)
        if infra:
            plan[g["groupid"]] = (infra, site_of(g["name"]))
    if not plan:
        print("   [skip] nenhum host group de infra encontrado"); return
    hosts = call("host.get", {"output": ["hostid", "host"], "groupids": list(plan),
                              "selectHostGroups": ["groupid"], "selectTags": ["tag", "value"]})
    changed = 0
    for h in hosts:
        # infra/site a partir do 1o grupo de infra que casar (override tem prioridade)
        infra = site = None
        for grp in h.get("hostgroups", h.get("groups", [])):
            if grp["groupid"] in plan:
                infra, site = plan[grp["groupid"]]; break
        if h["host"] in HOST_INFRA_OVERRIDE:
            infra = HOST_INFRA_OVERRIDE[h["host"]]
        if not infra:
            continue
        want = {("infra", infra)}
        if site:
            want.add(("site", site))
        cur = {(x["tag"], x["value"]) for x in h.get("tags", [])}
        miss = want - cur
        if not miss:
            continue
        print(f"   + {h['host']}: {sorted(miss)}")
        changed += 1
        if not DRY:
            newtags = [{"tag": t, "value": v} for (t, v) in cur | want]
            call("host.update", {"hostid": h["hostid"], "tags": newtags})
    print(f"   ({changed} host(s) atualizado(s))")


def _get_service(name):
    r = call("service.get", {"output": ["serviceid", "name"], "filter": {"name": [name]}})
    return r[0]["serviceid"] if r else None


def step_D_services():
    print("\n== D) Arvore de Servicos ==")
    root = _get_service(ROOT_SERVICE)
    if root:
        print(f"   = raiz ja existe: {ROOT_SERVICE} ({root})")
    else:
        print(f"   + raiz: {ROOT_SERVICE}")
        if not DRY:
            root = call("service.create", {"name": ROOT_SERVICE, "algorithm": 2, "sortorder": 0})["serviceids"][0]
        else:
            root = "<root>"
    for i, (infra, label) in enumerate(TYPES):
        if _get_service(label):
            print(f"   = filho ja existe: {label}"); continue
        print(f"   + filho: {label}  (scope=availability + infra={infra}, slatier={SLATIER})")
        if not DRY:
            call("service.create", {
                "name": label, "algorithm": 2, "sortorder": i,
                "problem_tags": [
                    {"tag": "scope", "operator": 0, "value": "availability"},
                    {"tag": "infra", "operator": 0, "value": infra},
                ],
                "tags": [{"tag": "slatier", "value": SLATIER}],
                "parents": [{"serviceid": root}],
            })


def step_E_sla():
    print("\n== E) Definicao de SLA ==")
    if call("sla.get", {"output": ["slaid"], "filter": {"name": [SLA_NAME]}}):
        print(f"   = SLA ja existe: {SLA_NAME}"); return
    print(f"   + SLA: {SLA_NAME}  ({SLO}%, mensal, 24x7, tag slatier={SLATIER})")
    if not DRY:
        call("sla.create", {
            "name": SLA_NAME, "slo": float(SLO), "period": 2,      # 2 = mensal
            "effective_date": int(time.mktime(time.strptime("2026-06-01", "%Y-%m-%d"))),
            "timezone": "America/Sao_Paulo", "status": 1,
            "service_tags": [{"tag": "slatier", "operator": 0, "value": SLATIER}],
        })


def main():
    if not TOKEN:
        sys.exit("ERRO: defina ZBX_TOKEN (token admin com escrita).")
    print(f">> Zabbix: {URL} | {'DRY-RUN (nada sera alterado)' if DRY else 'APLICANDO'}")
    step_A_tuning()
    step_B_trigger_tags()
    step_C_host_tags()
    step_D_services()
    step_E_sla()
    print("\n>> Concluido." + (" (DRY-RUN)" if DRY else ""))


if __name__ == "__main__":
    main()
