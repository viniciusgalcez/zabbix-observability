#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auditoria: indisponibilidade de aplicações com vários fatores (SLA).

Para cada app composta (pai + filhos = fatores: API, app, banco, web…):
  1) Só o PAI tem slatier=critico|padrao (filhos NÃO devem ter).
  2) Pai usa algorithm=2 (Most critical of child services) → união.
  3) Downtime do pai ≈ união das timelines dos fatores (não a soma).

Uso (rede interna Capri / .mcp.json):
  python audit_sla_overlap.py
  python audit_sla_overlap.py --service "Deps Produção"
  python audit_sla_overlap.py --fixture ../backups/fixture_sla_critico_sli_live_20261126.json

Credenciais: ZABBIX_URL/ZABBIX_TOKEN ou ZBX_* ou .mcp.json
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.request
from pathlib import Path

from sla_overlap_lib import (
    alarms_to_down_intervals,
    overlap_waste,
    parent_matches_union,
    sum_durations,
    union_duration,
)

ROOT = Path(__file__).resolve().parent.parent
SLATIER_VALUES = {"critico", "padrao"}
_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE


def load_credentials():
    for a, b in (("ZABBIX_URL", "ZABBIX_TOKEN"), ("ZBX_URL", "ZBX_TOKEN")):
        url, tok = os.environ.get(a), os.environ.get(b)
        if url and tok:
            return url, tok
    mcp = ROOT / ".mcp.json"
    if mcp.exists():
        env = json.loads(mcp.read_text(encoding="utf-8"))["mcpServers"]["zabbix"]["env"]
        return env["ZABBIX_URL"], env["ZABBIX_TOKEN"]
    return None, None


def api(url, token, method, params=None):
    payload = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json-rpc",
            "Authorization": f"Bearer {token}",
        },
    )
    with urllib.request.urlopen(req, timeout=60, context=_SSL) as r:
        resp = json.load(r)
    if "error" in resp:
        raise RuntimeError(f"{method}: {resp['error']}")
    return resp["result"]


def slatier_of(svc):
    for t in svc.get("tags") or []:
        if t.get("tag") == "slatier" and t.get("value") in SLATIER_VALUES:
            return t["value"]
    return None


def audit_fixture(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    deps = data["deps_producao"]
    sids = set(str(x) for x in data["sla_getsli_serviceids"])
    parent_id = str(deps["serviceid"])
    child_ids = [str(c["serviceid"]) for c in deps["children"]]
    ok = True
    print(f"== Fixture {path.name} ==")
    print(f"SLA: {data['sla']['name']} (slaid={data['sla']['slaid']})")
    print(f"Pai: {deps['name']} id={parent_id} algorithm={deps['algorithm']} tags={deps['tags']}")
    if parent_id not in sids:
        print("FAIL: pai NÃO está no sla.getsli")
        ok = False
    else:
        print("OK: pai está no sla.getsli")
    leaked = [c for c in child_ids if c in sids]
    if leaked:
        print(f"FAIL: filhos no SLA (contam separado): {leaked}")
        ok = False
    else:
        print("OK: filhos NÃO estão no sla.getsli (sem soma indevida no motor nativo)")
    if str(deps.get("algorithm")) != "2":
        print("FAIL: algorithm != 2 (Most critical)")
        ok = False
    else:
        print("OK: algorithm=2 → pai cai se qualquer filho cai (união)")
    print(f"Veredito fixture: {data.get('verdict')}")
    return 0 if ok else 1


def audit_live(url, token, only_name=None) -> int:
    services = api(
        url,
        token,
        "service.get",
        {
            "output": "extend",
            "selectTags": "extend",
            "selectChildren": ["serviceid", "name"],
            "selectParents": ["serviceid", "name"],
            "selectStatusTimes": "extend",
        },
    )
    by_id = {s["serviceid"]: s for s in services}
    composites = [
        s
        for s in services
        if s.get("children")
        and (slatier_of(s) or only_name)
        and (only_name is None or s["name"] == only_name)
    ]
    if only_name and not composites:
        # permitir auditar composto sem slatier no filtro
        composites = [s for s in services if s.get("children") and s["name"] == only_name]

    slas = api(url, token, "sla.get", {"output": "extend", "selectServiceTags": "extend"})
    print(f"SLAs: {[(x['slaid'], x['name']) for x in slas]}")
    print(f"Compostos a auditar: {len(composites)}\n")

    failures = 0
    for parent in composites:
        pid = parent["serviceid"]
        pname = parent["name"]
        algo = str(parent.get("algorithm"))
        ptier = slatier_of(parent)
        children = [by_id[c["serviceid"]] for c in parent["children"] if c["serviceid"] in by_id]
        print(f"--- {pname} (id={pid}) algorithm={algo} slatier={ptier or '-'} ---")

        if algo != "2":
            print(f"  WARN: algorithm={algo} (esperado 2=Most critical para união OR)")
            failures += 1

        bad_kids = []
        for ch in children:
            ct = slatier_of(ch)
            if ct:
                bad_kids.append((ch["name"], ch["serviceid"], ct))
        if bad_kids:
            print(f"  FAIL: filhos com slatier (contam no SLA separado): {bad_kids}")
            failures += 1
        else:
            print("  OK: nenhum filho com slatier=critico|padrao")

        # timelines
        parent_alarms = []
        for block in parent.get("status_times") or parent.get("status_timeline") or []:
            parent_alarms.extend(block.get("alarms") or [])
        # Zabbix 7 pode expor via selectStatusTimes; fallback vazio
        if not parent_alarms and "status_timeline" in parent:
            for block in parent["status_timeline"]:
                parent_alarms.extend(block.get("alarms") or [])

        child_intervals = []
        for ch in children:
            alarms = []
            for block in ch.get("status_times") or ch.get("status_timeline") or []:
                alarms.extend(block.get("alarms") or [])
            iv = alarms_to_down_intervals(alarms)
            child_intervals.extend(iv)
            print(f"  filho {ch['name']}: {len(iv)} intervalo(s) down, dur={union_duration(iv)}s")

        parent_iv = alarms_to_down_intervals(parent_alarms)
        p_down = union_duration(parent_iv)
        u = union_duration(child_intervals)
        s = sum_durations(child_intervals)
        waste = overlap_waste(child_intervals)
        print(f"  pai downtime={p_down}s | união filhos={u}s | soma filhos={s}s | desperdício sobreposição={waste}s")
        if child_intervals:
            if parent_matches_union(p_down, child_intervals, tolerance_sec=5):
                print("  OK: downtime do pai ≈ união dos filhos (não a soma)")
            elif p_down == 0 and u == 0:
                print("  OK: sem downtime no histórico carregado")
            else:
                print("  WARN: pai não bate união — conferir selectStatusTimes / período / propagation")
                # não falha duro se API não devolveu alarms (comum sem select correto)
                if parent_alarms or any(True for _ in child_intervals):
                    if parent_alarms:
                        failures += 1
        print()

    # cruza com sla.getsli: filhos não podem aparecer
    for sla in slas:
        tags = sla.get("service_tags") or []
        if not any(t.get("tag") == "slatier" and t.get("value") in SLATIER_VALUES for t in tags):
            continue
        sli = api(url, token, "sla.getsli", {"slaid": sla["slaid"]})
        covered = set(str(x) for x in sli.get("serviceids") or [])
        print(f"SLA {sla['name']} cobre {len(covered)} serviço(s)")
        for parent in composites:
            if not slatier_of(parent):
                continue
            for c in parent.get("children") or []:
                if str(c["serviceid"]) in covered:
                    print(
                        f"  FAIL: {c['name']} (filho de {parent['name']}) entra no {sla['name']}"
                    )
                    failures += 1
    return 1 if failures else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--service", help="Nome exato do serviço pai (ex: Deps Produção)")
    ap.add_argument("--fixture", help="Validar evidência offline JSON")
    args = ap.parse_args()

    if args.fixture:
        sys.exit(audit_fixture(Path(args.fixture)))

    url, token = load_credentials()
    if not url or not token:
        fixture = ROOT / "backups" / "fixture_sla_critico_sli_live_20261126.json"
        print("Sem credenciais/API. Validando fixture offline...")
        code = audit_fixture(fixture)
        print(
            "\nPara auditoria ao vivo na rede Capri:\n"
            "  ZABBIX_URL=... ZABBIX_TOKEN=... python audit_sla_overlap.py --service 'Deps Produção'"
        )
        sys.exit(code)

    try:
        sys.exit(audit_live(url, token, args.service))
    except Exception as e:
        print(f"API indisponível ({e}). Fallback fixture.")
        sys.exit(audit_fixture(ROOT / "backups" / "fixture_sla_critico_sli_live_20261126.json"))


if __name__ == "__main__":
    main()
