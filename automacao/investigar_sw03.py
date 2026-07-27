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
    for hostname in ["BGP-EXP-SW03", "BGP-EXP-SW02"]:
        h = api("host.get", {"filter": {"host": hostname}, "output": ["hostid", "host"]})
        hostid = h[0]["hostid"]
        evs = api("event.get", {"output": ["eventid", "clock", "value", "name"], "hostids": [hostid],
                                "source": 0, "object": 0, "time_from": 1782874800,
                                "tags": [{"tag": "scope", "value": "availability", "operator": 0}],
                                "sortfield": ["clock"], "sortorder": "ASC"})
        print(f"=== {hostname} ===")
        for e in evs:
            print(" ", ts(e["clock"]), "PROBLEMA" if e["value"] == "1" else "RESOLVIDO", "-", e["name"])
        print()


if __name__ == "__main__":
    main()
