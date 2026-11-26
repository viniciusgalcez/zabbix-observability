#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Relatório de SLA de *aplicação* via sla.getsli do Zabbix.

Usa o SLI do serviço PAI (slatier=critico|padrao). O motor nativo já aplica
união de indisponibilidade quando o pai tem algorithm=Most critical e só ele
tem a tag slatier — não some Deps API + Deps Banco.

Uso:
  python gen_sla_app_report.py
  python gen_sla_app_report.py --sla "SLA Crítico" --out ../relatorio-sla-apps
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import ssl
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
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
    sys.exit("Defina ZABBIX_URL e ZABBIX_TOKEN (ou .mcp.json).")


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


def fmt_dur(secs):
    secs = int(secs)
    d, r = divmod(secs, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    out = []
    if d:
        out.append(f"{d}d")
    if h:
        out.append(f"{h}h")
    if m:
        out.append(f"{m}m")
    if s and not d:
        out.append(f"{s}s")
    return " ".join(out) or "0s"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sla", default=None, help="Nome do SLA (default: todos critico/padrao)")
    ap.add_argument("--out", default=str(ROOT / "relatorio-sla-apps"))
    args = ap.parse_args()
    url, token = load_credentials()

    slas = api(url, token, "sla.get", {"output": "extend", "selectServiceTags": "extend"})
    if args.sla:
        slas = [s for s in slas if s["name"] == args.sla]
        if not slas:
            sys.exit(f"SLA não encontrado: {args.sla}")

    services = api(
        url,
        token,
        "service.get",
        {"output": ["serviceid", "name", "algorithm"], "selectTags": "extend", "selectChildren": ["serviceid"]},
    )
    names = {s["serviceid"]: s["name"] for s in services}
    algo = {s["serviceid"]: s.get("algorithm") for s in services}
    has_children = {s["serviceid"]: bool(s.get("children")) for s in services}

    sections = []
    for sla in slas:
        sli = api(url, token, "sla.getsli", {"slaid": sla["slaid"]})
        periods = sli.get("periods") or []
        if not periods:
            continue
        # último período completo se o atual estiver curto; usa o penúltimo se existir
        idx = -1
        period = periods[idx]
        rows_data = list(zip(sli["serviceids"], sli["sli"][idx]))
        rows_html = []
        usable = []
        for sid, d in rows_data:
            sid = str(sid)
            sli_v = d.get("sli", -1)
            if sli_v < 0:
                continue
            usable.append((sid, d, float(sli_v)))
        usable.sort(key=lambda x: x[2])
        for sid, d, sli_v in usable:
            slo = float(sla.get("slo", 0))
            ok = sli_v >= slo
            badge = "b-ok" if ok else "b-bad"
            tip = ""
            if has_children.get(sid) and str(algo.get(sid)) == "2":
                tip = " (pai composto / união)"
            rows_html.append(
                f"<tr><td>{html.escape(names.get(sid, sid))}{tip}</td>"
                f"<td>{sli_v:.4f}%</td><td>{slo}%</td>"
                f"<td>{fmt_dur(d.get('downtime', 0))}</td>"
                f"<td>{fmt_dur(d.get('uptime', 0))}</td>"
                f"<td><span class='badge {badge}'>{'OK' if ok else 'ABAIXO'}</span></td></tr>"
            )
        pf = dt.datetime.fromtimestamp(period["period_from"]).strftime("%d/%m/%Y")
        pt = dt.datetime.fromtimestamp(period["period_to"]).strftime("%d/%m/%Y")
        sections.append(
            f"<section><h2>{html.escape(sla['name'])} — {pf} a {pt}</h2>"
            f"<p class='mut'>SLI por serviço com tag do SLA. Cada linha já é união interna do serviço "
            f"(não some filhos). Filhos sem slatier não aparecem.</p>"
            f"<table><thead><tr><th>Serviço</th><th>SLI</th><th>SLO</th>"
            f"<th>Downtime</th><th>Uptime</th><th>Meta</th></tr></thead>"
            f"<tbody>{''.join(rows_html) or '<tr><td colspan=6>Sem dados</td></tr>'}</tbody></table></section>"
        )

    now = dt.datetime.now().strftime("%d/%m/%Y %H:%M")
    doc = f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<title>SLA Aplicações — Capricórnio</title>
<style>
:root{{--bg:#f4f6f9;--card:#fff;--ink:#1f2937;--muted:#6b7280;--line:#e5e7eb;--brand:#b1271b;}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 Segoe UI,Roboto,Arial,sans-serif}}
.wrap{{max-width:1100px;margin:0 auto;padding:24px}}
header{{background:linear-gradient(135deg,#b1271b,#7a1a12);color:#fff;border-radius:14px;padding:22px 26px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:14px 0}}
h2{{margin:0 0 10px;font-size:16px;border-left:4px solid var(--brand);padding-left:8px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line)}}
th{{background:#fafafa;color:var(--muted);font-size:11px;text-transform:uppercase}}
.badge{{padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600}}
.b-ok{{background:#dcfce7;color:#166534}}.b-bad{{background:#fee2e2;color:#991b1b}}
.mut{{color:var(--muted);font-size:12px}}
</style></head><body><div class="wrap">
<header><h1 style="margin:0 0 6px;font-size:22px">SLA de Aplicações (serviço pai)</h1>
<div style="opacity:.92;font-size:13px">Gerado {now} — fonte: sla.getsli (Zabbix nativo, união no pai)</div></header>
{''.join(sections)}
<p class="mut">Não some downtime de Deps API + Banco: use a linha do pai (Deps Produção).</p>
</div></body></html>"""
    out = Path(args.out + ".html")
    out.write_text(doc, encoding="utf-8")
    print(f"HTML: {out}")


if __name__ == "__main__":
    main()
