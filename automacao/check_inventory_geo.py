#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifica se os hosts tem inventario habilitado e coordenadas (location_lat/lon)
preenchidas -- exatamente o que o noc_geomap.php precisa para plotar marcadores.
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
    hosts = api("host.get", {
        "output": ["hostid", "host", "status", "inventory_mode"],
        "filter": {"status": "0"},
        "selectInventory": ["location_lat", "location_lon"],
    })
    total = len(hosts)
    inv_on = [h for h in hosts if h["inventory_mode"] != "-1"]
    with_coords = [h for h in hosts if h.get("inventory") and h["inventory"].get("location_lat")
                   and h["inventory"].get("location_lon")]

    print(f"Total de hosts habilitados (status=0): {total}")
    print(f"Com inventario ligado (inventory_mode != -1): {len(inv_on)}")
    print(f"Com location_lat E location_lon preenchidos : {len(with_coords)}")

    if with_coords:
        print("\n--- Hosts com coordenadas ---")
        for h in with_coords[:20]:
            print(f"  {h['host']:25s} lat={h['inventory']['location_lat']} lon={h['inventory']['location_lon']}")
    else:
        print("\n=> NENHUM host tem coordenadas. O noc_geomap.php nao vai plotar nenhum marcador hoje.")


if __name__ == "__main__":
    main()
