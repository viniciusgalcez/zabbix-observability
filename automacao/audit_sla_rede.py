#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditoria: equipamentos de rede (Switches Cisco, APs Aruba, Firewalls FortiGate)
que existem nos host groups mas NAO tem Service correspondente no SLA de rede.

Compara:
  A) hosts nos host groups de rede (Switches Cisco/*, Access Points Aruba/*, Firewalls FortiGate/*)
  B) hosts com Service folha sob a arvore "Rede" (problem_tags: sla=hostdown, slahost=<host>)

Le ZABBIX_URL / ZABBIX_TOKEN do .mcp.json (mesmo caminho usado pelo MCP, so leitura).
"""
import json
import ssl
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
env = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["zabbix"]["env"]
URL, TOKEN = env["ZABBIX_URL"], env["ZABBIX_TOKEN"]

_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE


def api(method, params=None):
    payload = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1}
    req = urllib.request.Request(
        URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json-rpc",
                 "Authorization": f"Bearer {TOKEN}"})
    with urllib.request.urlopen(req, timeout=30, context=_SSL) as r:
        resp = json.load(r)
    if "error" in resp:
        raise RuntimeError(f"{method}: {resp['error']}")
    return resp["result"]


def main():
    # 1) host groups de rede (qualquer grupo cujo nome comece com os 3 prefixos)
    all_groups = api("hostgroup.get", {"output": ["groupid", "name"]})
    net_prefixes = ("Switches Cisco", "Access Points Aruba", "Firewalls/")
    net_groups = [g for g in all_groups if g["name"].startswith(net_prefixes)]
    print(f"Host groups de rede encontrados: {len(net_groups)}")
    for g in sorted(net_groups, key=lambda x: x["name"]):
        print(f"  - {g['name']} (id {g['groupid']})")

    gids = [g["groupid"] for g in net_groups]
    hosts = api("host.get", {"groupids": gids, "output": ["hostid", "host", "name"],
                              "selectHostGroups": ["name"]})
    hosts_by_name = {h["host"]: h for h in hosts}
    print(f"\nTotal de hosts nos grupos de rede: {len(hosts)}")

    # 2) services da arvore "Rede" -> problem_tags slahost
    services = api("service.get", {"output": ["serviceid", "name"], "selectProblemTags": "extend"})
    slahosts = set()
    dup = {}
    for s in services:
        for t in s.get("problem_tags", []):
            if t.get("tag") == "slahost":
                v = t["value"]
                slahosts.add(v)
                dup.setdefault(v, []).append(s["name"])

    # 3) comparacao
    missing = sorted(h["host"] for h in hosts if h["host"] not in slahosts)
    orphan_services = sorted(slahosts - set(hosts_by_name.keys()))
    duplicated = {k: v for k, v in dup.items() if len(v) > 1}

    print(f"\n=== RESULTADO ===")
    print(f"Hosts nos grupos de rede : {len(hosts)}")
    print(f"Hosts com Service no SLA : {len(slahosts & set(hosts_by_name.keys()))}")
    print(f"FALTANDO no SLA          : {len(missing)}")
    print(f"Services orfaos (host nao existe mais no grupo): {len(orphan_services)}")
    print(f"Services duplicados para o mesmo host: {len(duplicated)}")

    if missing:
        print(f"\n--- Hosts SEM Service no SLA ({len(missing)}) ---")
        for h in missing:
            hh = hosts_by_name[h]
            grps = ", ".join(g["name"] for g in hh.get("hostgroups", []))
            print(f"  {h:30s}  [{grps}]")

    if orphan_services:
        print(f"\n--- Services com slahost sem host correspondente no grupo ({len(orphan_services)}) ---")
        for h in orphan_services:
            print(f"  {h}  -> services: {dup.get(h)}")

    if duplicated:
        print(f"\n--- slahost duplicado em mais de 1 Service ---")
        for h, names in duplicated.items():
            print(f"  {h}: {names}")

    out = {
        "total_hosts_grupos": len(hosts),
        "total_com_service": len(slahosts & set(hosts_by_name.keys())),
        "faltando": missing,
        "services_orfaos": orphan_services,
        "duplicados": duplicated,
    }
    out_path = ROOT / "backups" / "audit_sla_rede_resultado.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultado salvo em: {out_path}")


if __name__ == "__main__":
    main()
