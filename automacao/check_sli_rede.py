#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
    services = api("service.get", {"output": ["serviceid", "name"], "selectProblemTags": "extend"})
    leaf = [s for s in services if any(t.get("tag") == "sla" and t.get("value") == "hostdown"
                                        for t in s.get("problem_tags", []))]
    print(f"Total de folhas no SLA Rede: {len(leaf)}")

    sids = [s["serviceid"] for s in leaf]
    names = {s["serviceid"]: s["name"] for s in leaf}

    sli = api("sla.getsli", {"slaid": "7", "serviceids": sids, "periods": 1})
    period = sli["periods"][0]
    rows = list(zip(sli["serviceids"], sli["sli"][0]))
    below = [(sid, d) for sid, d in rows if d["sli"] < 99]
    below.sort(key=lambda x: x[1]["sli"])

    print(f"Periodo: {period}")
    print(f"Abaixo de 99% (fora da meta): {len(below)} de {len(rows)}")
    print()
    for sid, d in below:
        nm = names[str(sid)]
        print(f"{nm:25s} SLI={d['sli']:.2f}%  downtime={d['downtime']}s  budget={d['error_budget']}")


if __name__ == "__main__":
    main()
