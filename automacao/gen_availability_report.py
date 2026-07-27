#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Relatorio de indisponibilidade com MOTIVO inferido (todos os SLAs / todo o ambiente).

Para cada queda de disponibilidade no periodo (eventos com tag scope=availability),
reconstroi o intervalo (inicio/fim/duracao) e infere a causa por correlacao:

  - Reboot/energia .... o host disparou "restarted / uptime < 10m" perto da recuperacao
                        (o uptime zerou = reinicio; queda longa costuma ser falta de energia).
  - Energia (UPS) ..... um UPS do mesmo site teve problema sobrepondo a janela.
  - Colateral ......... um switch do mesmo site caiu antes e cobre a janela deste host
                        (equipamento atras do switch; causa raiz = o switch).
  - Rede/ICMP ......... nenhuma das anteriores; indisponibilidade sem causa determinada.

Saidas: HTML estilizado + Excel (.xlsx). Se openpyxl nao estiver instalado, gera .csv.

Uso:
  python gen_availability_report.py                      # mes corrente ate agora
  python gen_availability_report.py --from 2026-06-01 --to 2026-07-01
  python gen_availability_report.py --group "Switches Cisco/BGP"   # filtra por grupo

Credenciais: le ZABBIX_URL / ZABBIX_TOKEN do ambiente; senao, do .mcp.json do projeto.
"""
import os
import sys
import json
import ssl
import html
import argparse
import datetime as dt
import urllib.request
from pathlib import Path

# ----------------------------------------------------------------------------- config
ROOT = Path(__file__).resolve().parent.parent


def load_credentials():
    url = os.environ.get("ZABBIX_URL")
    token = os.environ.get("ZABBIX_TOKEN")
    if url and token:
        return url, token
    mcp = ROOT / ".mcp.json"
    if mcp.exists():
        env = json.loads(mcp.read_text(encoding="utf-8"))["mcpServers"]["zabbix"]["env"]
        return env["ZABBIX_URL"], env["ZABBIX_TOKEN"]
    sys.exit("Defina ZABBIX_URL e ZABBIX_TOKEN (ou tenha .mcp.json na raiz).")


URL, TOKEN = load_credentials()
_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE


def api(method, params=None):
    payload = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": 1}
    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json-rpc",
                 "Authorization": f"Bearer {TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=60, context=_SSL) as r:
        resp = json.load(r)
    if "error" in resp:
        raise RuntimeError(f"{method}: {resp['error']}")
    return resp["result"]


# ----------------------------------------------------------------------------- helpers
def fmt_ts(ts):
    return dt.datetime.fromtimestamp(int(ts)).strftime("%d/%m/%Y %H:%M:%S")


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


def site_of(host, tags):
    for t in tags:
        if t.get("tag") == "site":
            return t["value"].upper()
    # fallback: prefixo antes do primeiro '-'
    return host.split("-")[0].upper() if "-" in host else "?"


def tipo_of(host, tags):
    for t in tags:
        if t.get("tag") == "infra":
            return t["value"]
    up = host.upper()
    if "-SW" in up:
        return "switch"
    if "-AP" in up:
        return "ap"
    if "-FW" in up:
        return "firewall"
    return "outro"


# ----------------------------------------------------------------------------- coleta
def collect(time_from, time_till, group=None):
    common = dict(source=0, object=0, time_from=time_from, time_till=time_till,
                  selectHosts=["hostid", "host"], selectTags="extend",
                  sortfield=["clock"], sortorder="ASC")
    if group:
        gids = [g["groupid"] for g in api("hostgroup.get",
                {"output": ["groupid"], "filter": {"name": group}})]
        if not gids:
            sys.exit(f"Grupo nao encontrado: {group}")
        common["groupids"] = gids

    # eventos de disponibilidade (problema + recuperacao)
    avail = api("event.get", dict(common, value=1,
                tags=[{"tag": "scope", "value": "availability", "operator": 0}],
                output=["eventid", "clock", "name", "severity", "r_eventid"]))
    # tempos de recuperacao
    rec_ids = [e["r_eventid"] for e in avail if e["r_eventid"] != "0"]
    rec = {}
    if rec_ids:
        for e in api("event.get", {"output": ["eventid", "clock"], "eventids": rec_ids}):
            rec[e["eventid"]] = int(e["clock"])

    # eventos de reboot ("restarted" / "reiniciad" / "uptime")
    restarts = {}
    for kw in ("restarted", "reiniciad", "uptime <"):
        for e in api("event.get", dict(common, value=1, search={"name": kw},
                     output=["eventid", "clock", "name"])):
            hid = e["hosts"][0]["hostid"] if e["hosts"] else None
            restarts.setdefault(hid, []).append(int(e["clock"]))

    # janelas de problema em UPS (energia) por site
    ups_events = api("event.get", dict(common, value=1, search={"name": "UPS"},
                     output=["eventid", "clock", "name", "r_eventid"]))
    # tambem hosts de grupos UPS
    ups_gids = [g["groupid"] for g in api("hostgroup.get",
                {"output": ["groupid"], "search": {"name": "UPS"}})]
    ups_host_events = []
    if ups_gids:
        ups_host_events = api("event.get", dict(source=0, object=0, time_from=time_from,
                              time_till=time_till, groupids=ups_gids, value=1,
                              selectHosts=["hostid", "host"], selectTags="extend",
                              output=["eventid", "clock", "name", "r_eventid"],
                              sortfield=["clock"], sortorder="ASC"))
    power_windows = []  # (site, start, end)
    for e in (ups_events + ups_host_events):
        if not e.get("hosts"):
            continue
        h = e["hosts"][0]["host"]
        tags = e.get("tags", [])
        start = int(e["clock"])
        end = rec.get(e.get("r_eventid", "0"), time_till)
        power_windows.append((site_of(h, tags), start, end))

    return avail, rec, restarts, power_windows


def build_outages(avail, rec, restarts, power_windows, time_till):
    outages = []
    for e in avail:
        if not e.get("hosts"):
            continue
        host = e["hosts"][0]["host"]
        hid = e["hosts"][0]["hostid"]
        tags = e.get("tags", [])
        start = int(e["clock"])
        end = rec.get(e["r_eventid"], None)
        ongoing = end is None
        if ongoing:
            end = time_till
        outages.append({
            "host": host, "hostid": hid, "site": site_of(host, tags),
            "tipo": tipo_of(host, tags), "start": start, "end": end,
            "dur": end - start, "ongoing": ongoing,
            "name": e["name"], "severity": int(e["severity"]),
        })

    # indice de quedas de switch por site (para detectar colateral)
    sw_out = [o for o in outages if o["tipo"] == "switch"]

    for o in outages:
        o["cause"], o["cause_cls"] = infer_cause(o, restarts, power_windows, sw_out)
    outages.sort(key=lambda x: x["start"], reverse=True)
    return outages


def infer_cause(o, restarts, power_windows, sw_out):
    rebooted = any(o["start"] - 120 <= ts <= o["end"] + 600
                   for ts in restarts.get(o["hostid"], []))
    # switch do mesmo site que ja estava/ficou fora quando este host caiu (causa raiz)
    root_sw = None
    for s in sorted(sw_out, key=lambda x: x["start"]):
        if s["hostid"] == o["hostid"]:
            continue
        if s["site"] == o["site"] and s["start"] <= o["start"] + 120 and s["end"] >= o["start"] - 120:
            root_sw = s
            break
    power = any(site == o["site"] and ps <= o["end"] and pe >= o["start"]
                for site, ps, pe in power_windows)

    # equipamento atras de um switch que caiu = colateral (a raiz e o switch)
    if o["tipo"] != "switch" and root_sw:
        extra = "reboot do site" if rebooted else "switch fora"
        return (f"Colateral — {root_sw['host']} ({extra})", "warn")
    if rebooted:
        return ("Reboot / energia (uptime zerou)", "bad")
    if power:
        return ("Energia (UPS do site)", "bad")
    return ("Rede/ICMP — causa nao determinada", "pend")


# ----------------------------------------------------------------------------- saidas
def write_html(path, outages, meta):
    rows = []
    cls_map = {"bad": "b-bad", "warn": "b-warn", "pend": "b-pend", "ok": "b-ok"}
    for o in outages:
        badge = cls_map.get(o["cause_cls"], "b-pend")
        estado = '<span class="badge b-warn">EM ABERTO</span>' if o["ongoing"] else ""
        rows.append(f"""<tr>
          <td>{html.escape(o['host'])} {estado}</td>
          <td>{html.escape(o['tipo'])}</td>
          <td>{html.escape(o['site'])}</td>
          <td>{fmt_ts(o['start'])}</td>
          <td>{'—' if o['ongoing'] else fmt_ts(o['end'])}</td>
          <td>{fmt_dur(o['dur'])}</td>
          <td><span class="badge {badge}">{html.escape(o['cause'])}</span></td>
        </tr>""")
    total_dur = sum(o["dur"] for o in outages)
    doc = f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
<title>Relatorio de Indisponibilidade — Capricornio Textil</title><style>
:root{{--bg:#f4f6f9;--card:#fff;--ink:#1f2937;--muted:#6b7280;--line:#e5e7eb;--brand:#b1271b;--brand2:#7a1a12;}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 Segoe UI,Roboto,Arial,sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:24px}}
header{{background:linear-gradient(135deg,var(--brand),var(--brand2));color:#fff;border-radius:14px;padding:26px 30px}}
header h1{{margin:0 0 6px;font-size:23px}}.sub{{opacity:.92;font-size:13px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin:18px 0}}
.stat{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;text-align:center}}
.stat b{{display:block;font-size:26px;color:var(--brand)}}.stat span{{color:var(--muted);font-size:12px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin:16px 0}}
h2{{margin:0 0 12px;font-size:17px;border-left:4px solid var(--brand);padding-left:10px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}}
th{{background:#fafafa;color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase}}
tr:hover td{{background:#fafbfc}}
.badge{{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11px;font-weight:600}}
.b-bad{{background:#fee2e2;color:#991b1b}}.b-warn{{background:#fef3c7;color:#92400e}}
.b-pend{{background:#f3f4f6;color:#374151}}.b-ok{{background:#dcfce7;color:#166534}}
footer{{color:var(--muted);font-size:12px;text-align:center;padding:16px}}</style></head><body><div class="wrap">
<header><h1>Relatorio de Indisponibilidade</h1>
<div class="sub">Capricornio Textil S.A. — quedas de disponibilidade com motivo inferido</div></header>
<div class="stats">
<div class="stat"><b>{len(outages)}</b><span>Quedas no periodo</span></div>
<div class="stat"><b>{fmt_dur(total_dur)}</b><span>Downtime somado</span></div>
<div class="stat"><b>{html.escape(meta['periodo'])}</b><span>Periodo</span></div>
<div class="stat"><b>{html.escape(meta['gerado'])}</b><span>Gerado em</span></div>
</div>
<section><h2>Incidentes</h2>
<table><thead><tr><th>Host</th><th>Tipo</th><th>Site</th><th>Inicio</th><th>Fim</th><th>Duracao</th><th>Motivo (inferido)</th></tr></thead>
<tbody>{''.join(rows) or '<tr><td colspan="7">Nenhuma queda no periodo.</td></tr>'}</tbody></table>
<p style="color:var(--muted);font-size:12px;margin-top:10px">Motivo inferido por correlacao (uptime/reboot, UPS do site, switch raiz). Revise casos "causa nao determinada".</p>
</section>
<footer>Zabbix 7.0 — gerado por gen_availability_report.py</footer>
</div></body></html>"""
    Path(path).write_text(doc, encoding="utf-8")


def write_xlsx(path, outages):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
    except ImportError:
        csv_path = str(path).rsplit(".", 1)[0] + ".csv"
        import csv
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Host", "Tipo", "Site", "Inicio", "Fim", "Duracao(s)", "Duracao", "Motivo", "Em aberto"])
            for o in outages:
                w.writerow([o["host"], o["tipo"], o["site"], fmt_ts(o["start"]),
                            "" if o["ongoing"] else fmt_ts(o["end"]), o["dur"],
                            fmt_dur(o["dur"]), o["cause"], "SIM" if o["ongoing"] else ""])
        return csv_path
    wb = Workbook()
    ws = wb.active
    ws.title = "Indisponibilidade"
    headers = ["Host", "Tipo", "Site", "Inicio", "Fim", "Duracao", "Duracao (s)", "Motivo", "Em aberto"]
    ws.append(headers)
    hf = Font(bold=True, color="FFFFFF")
    fill = PatternFill("solid", fgColor="B1271B")
    for c in ws[1]:
        c.font = hf
        c.fill = fill
    for o in outages:
        ws.append([o["host"], o["tipo"], o["site"], fmt_ts(o["start"]),
                   "" if o["ongoing"] else fmt_ts(o["end"]), fmt_dur(o["dur"]),
                   o["dur"], o["cause"], "SIM" if o["ongoing"] else ""])
    widths = [22, 10, 8, 20, 20, 12, 12, 34, 10]
    for i, wd in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = wd
    ws.freeze_panes = "A2"
    wb.save(path)
    return path


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="dfrom", help="YYYY-MM-DD (default: 1o do mes)")
    ap.add_argument("--to", dest="dto", help="YYYY-MM-DD (default: agora)")
    ap.add_argument("--group", help="filtra por grupo de hosts")
    ap.add_argument("--out", default=str(ROOT / "relatorio-indisponibilidade"),
                    help="prefixo dos arquivos de saida")
    a = ap.parse_args()

    now = dt.datetime.now()
    if a.dfrom:
        d0 = dt.datetime.strptime(a.dfrom, "%Y-%m-%d")
    else:
        d0 = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    d1 = dt.datetime.strptime(a.dto, "%Y-%m-%d") if a.dto else now
    tf, tt = int(d0.timestamp()), int(d1.timestamp())

    print(f"Coletando eventos de {d0:%d/%m/%Y} a {d1:%d/%m/%Y %H:%M}"
          + (f" (grupo {a.group})" if a.group else "") + " ...")
    avail, rec, restarts, power = collect(tf, tt, a.group)
    outages = build_outages(avail, rec, restarts, power, tt)
    print(f"  {len(outages)} quedas encontradas.")

    meta = {"periodo": f"{d0:%d/%m/%Y}–{d1:%d/%m/%Y}", "gerado": now.strftime("%d/%m/%Y %H:%M")}
    html_path = a.out + ".html"
    xlsx_path = a.out + ".xlsx"
    write_html(html_path, outages, meta)
    saved = write_xlsx(xlsx_path, outages)
    print(f"HTML : {html_path}")
    print(f"Plan.: {saved}")


if __name__ == "__main__":
    main()
