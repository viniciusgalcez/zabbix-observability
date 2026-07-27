#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import ssl
import datetime as dt
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


def ts(clock):
    return dt.datetime.fromtimestamp(int(clock)).strftime("%d/%m %H:%M:%S")


def main():
    h = api("host.get", {"filter": {"host": "BGP-EXP-SW02"}, "output": ["hostid", "host"],
                          "selectParentTemplates": ["name"]})
    print("HOST:", json.dumps(h, ensure_ascii=False))
    hostid = h[0]["hostid"]

    # todos os eventos de disponibilidade deste mes (qualquer tag scope=availability)
    evs = api("event.get", {"output": ["eventid", "clock", "value", "name"], "hostids": [hostid],
                            "source": 0, "object": 0, "time_from": 1782874800,
                            "tags": [{"tag": "scope", "value": "availability", "operator": 0}],
                            "sortfield": ["clock"], "sortorder": "ASC"})
    print(f"\n--- Eventos de disponibilidade (scope=availability) : {len(evs)} ---")
    for e in evs:
        print(ts(e["clock"]), "PROBLEMA" if e["value"] == "1" else "RESOLVIDO", "-", e["name"])

    # TODOS os problemas deste host no periodo (nao so availability) para achar pistas
    all_ev = api("event.get", {"output": ["eventid", "clock", "value", "name", "severity"],
                               "hostids": [hostid], "source": 0, "object": 0,
                               "time_from": 1782874800,
                               "sortfield": ["clock"], "sortorder": "ASC"})
    print(f"\n--- TODOS os eventos deste host no mes : {len(all_ev)} ---")
    for e in all_ev:
        print(ts(e["clock"]), "PROBLEMA" if e["value"] == "1" else "RESOLVIDO",
              f"(sev {e['severity']})", "-", e["name"])

    # uptime do switch (hardware / network) - achar reset
    items = api("item.get", {"hostids": [hostid], "output": ["itemid", "name", "key_"],
                             "search": {"key_": "uptime"}})
    print("\n--- Items de uptime ---")
    for it in items:
        print(it["itemid"], it["name"], it["key_"])

    for it in items:
        hist = api("history.get", {"itemids": [it["itemid"]], "history": 3,
                                   "time_from": 1782874800, "time_till": 1785553200,
                                   "sortfield": "clock", "sortorder": "ASC", "output": "extend"})
        # procura quedas bruscas de valor (reset de uptime)
        drops = []
        for i in range(1, len(hist)):
            prev, cur = int(hist[i-1]["value"]), int(hist[i]["value"])
            if cur < prev - 300:  # caiu mais que o esperado entre coletas -> reset
                drops.append((hist[i-1], hist[i]))
        print(f"\n{it['name']}: {len(hist)} pontos de historico, {len(drops)} reset(s) detectado(s)")
        for prev, cur in drops:
            print(f"  RESET: {ts(prev['clock'])} (uptime={prev['value']}) -> {ts(cur['clock'])} (uptime={cur['value']})")


if __name__ == "__main__":
    main()
