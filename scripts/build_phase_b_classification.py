"""Phase B classification of open firewall problems."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(".")
EVENTS = json.loads((ROOT / "backups/phase_b_open_problem_events_hosts_20260930.json").read_text(encoding="utf-8"))
CANON = list(csv.DictReader((ROOT / "reports/mapa-links-alertas-canonico-20260930.csv").open(encoding="utf-8")))
OUT_CSV = ROOT / "reports/phase-b-classificacao-problemas-fw-20260930.csv"
OUT_MD = ROOT / "reports/phase-b-classificacao-problemas-fw-20260930.md"

NOW = datetime.now(timezone.utc).timestamp()
DAY = 86400

spo_vivo = next(r for r in CANON if r["link_id_canonico"] == "spo.vivo.isp1")
spo_deps = set(spo_vivo["depends_on_prefixes_correlacao"].split(";"))


def tags_of(event):
    out = defaultdict(list)
    for tag in event.get("tags", []):
        out[tag["tag"]].append(tag["value"])
    return out


def age_hours(clock):
    return (NOW - int(clock)) / 3600


rows = []
for event in EVENTS:
    host = ",".join(h["host"] for h in event.get("hosts", []))
    tags = tags_of(event)
    cause = str(event.get("cause_eventid") or "0")
    link_causes = tags.get("link-cause", [])
    deps = tags.get("depends-on", [])
    name = event.get("name", "")
    age_h = age_hours(event["clock"])

    if cause == "18116214":
        classe = "sintoma_ranqueado_spo_vivo"
    elif event["eventid"] == "18116214" or "SPO_VIVO" in link_causes:
        classe = "causa_spo_vivo"
    elif link_causes:
        classe = "causa_link_ou_agregado"
    elif cause != "0":
        classe = "sintoma_outra_causa"
    elif any(k in name.lower() for k in ("tunnel", "health", "packets", "link down", "vpn", "sd-wan")):
        # check if would match spo vivo deps
        vals = deps + tags.get("interface", []) + tags.get("sdwan-if", [])
        matched = False
        for value in vals:
            for dep in spo_deps:
                if dep and dep in value:
                    matched = True
                    break
        classe = "sintoma_solto_candidato" if matched else "independente_rede"
    else:
        classe = "outro"

    stale = "yes" if age_h >= 24 and classe in {"independente_rede", "sintoma_solto_candidato", "sintoma_outra_causa"} else "no"
    rows.append(
        {
            "eventid": event["eventid"],
            "host": host,
            "name": name,
            "severity": event.get("severity", ""),
            "clock_local": datetime.fromtimestamp(int(event["clock"])).strftime("%d/%m/%Y %H:%M:%S"),
            "age_hours": f"{age_h:.1f}",
            "cause_eventid": cause,
            "link_cause": ",".join(link_causes),
            "depends_on": ",".join(deps),
            "classe": classe,
            "stale_gt_24h": stale,
        }
    )

fields = list(rows[0].keys())
with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

counts = Counter(r["classe"] for r in rows)
stale_rows = [r for r in rows if r["stale_gt_24h"] == "yes"]
independents = [r for r in rows if r["classe"] == "independente_rede"]
candidates = [r for r in rows if r["classe"] == "sintoma_solto_candidato"]

lines = [
    "# Fase B — classificação dos problemas abertos nos firewalls",
    "",
    "Data: 30/09/2026",
    "",
    "## Decisão de topologia",
    "",
    "`BGPISP2_MTZISP1` e `SCLISP2_MTZISP1` permanecem sob `spo.vivo.isp1`.",
    "Motivo: a matriz de correlação usa o prefixo `MTZISP1` (ponta na saída 1 da matriz),",
    "e no incidente atual esses sintomas já acompanharam a queda da Vivo.",
    "",
    "## Resumo",
    "",
    f"- Problemas abertos nos 7 firewalls: **{len(rows)}**",
    f"- Causa `spo.vivo.isp1`: **{counts.get('causa_spo_vivo', 0)}**",
    f"- Sintomas já ranqueados sob Vivo: **{counts.get('sintoma_ranqueado_spo_vivo', 0)}**",
    f"- Sintomas soltos candidatos: **{counts.get('sintoma_solto_candidato', 0)}**",
    f"- Independentes de rede: **{counts.get('independente_rede', 0)}**",
    f"- Outra causa: **{counts.get('sintoma_outra_causa', 0)}**",
    f"- Stale >24h (independentes/outra causa): **{len(stale_rows)}**",
    "",
    "## Ranker",
    "",
    "Dry-run de `scripts/link_cause_rank_worker.py`: **0 candidatos**, **0 ambíguos**.",
    " Evidência: `backups/phase_b_link_cause_rank_dryrun_20260930.json`.",
    " Nenhum `event.acknowledge` adicional foi necessário.",
    "",
    "## Independentes (não ranquear sob Vivo)",
    "",
]
for row in independents:
    lines.append(
        f"- `{row['eventid']}` `{row['host']}` — {row['name']} "
        f"(desde {row['clock_local']}, {row['age_hours']}h, depends-on=`{row['depends_on']}`)"
    )
if not independents:
    lines.append("- nenhum")

lines.extend(["", "## Stale >24h a documentar", ""])
for row in stale_rows:
    lines.append(
        f"- `{row['eventid']}` `{row['host']}` — {row['name']} "
        f"({row['age_hours']}h, classe `{row['classe']}`)"
    )
if not stale_rows:
    lines.append("- nenhum")

lines.extend(
    [
        "",
        "## Aceite da Fase B",
        "",
        "- [x] Problemas classificados",
        "- [x] Ranker dry-run sem pendência comprovada",
        "- [x] Independentes documentados (não forçar sob Vivo)",
        "- [x] Stale >24h listados para tratamento posterior (sem fechar às cegas)",
        "",
        f"Planilha: `{OUT_CSV.as_posix()}`",
        "",
        "## Próximo (Fase C)",
        "",
        "Padronizar tags canônicas no piloto `spo.vivo.isp1` ",
        "(`link-id=spo.vivo.isp1`, `depends-on` nos sintomas, `scope=performance` em loss).",
        "",
    ]
)
OUT_MD.write_text("\n".join(lines), encoding="utf-8")
print(json.dumps({"rows": len(rows), "counts": counts, "stale": len(stale_rows), "independents": len(independents)}, ensure_ascii=False, default=str))
