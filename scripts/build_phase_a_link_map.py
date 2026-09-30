"""Phase A: build canonical link-alert map from live Zabbix exports."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(".")
CAUSE_FILE = ROOT / "backups/phase_a_all_cause_triggers_detail_20260930.json"
TUNNEL_FILE = ROOT / "backups/phase_a_all_fw_tunnel_down_triggers_20260930.json"
MATRIX_FILE = ROOT / "reports/link-correlation-matrix-20260930.csv"
OUT_CSV = ROOT / "reports/mapa-links-alertas-canonico-20260930.csv"
OUT_MD = ROOT / "reports/mapa-links-alertas-fase-a-20260930.md"

# Canonical link-id and metadata for each current link-cause.
CANON = {
    "SPO_VIVO": {
        "link_id": "spo.vivo.isp1",
        "carrier": "vivo",
        "site": "spo",
        "saida": "isp1",
        "parent_link_id": "",
        "notify_desired": "teams",
    },
    "SPO_ALGAR": {
        "link_id": "spo.algar.isp2",
        "carrier": "algar",
        "site": "spo",
        "saida": "isp2",
        "parent_link_id": "",
        "notify_desired": "teams",
    },
    "HK_VIVO": {
        "link_id": "scl.vivo.isp1",
        "carrier": "vivo",
        "site": "scl",
        "saida": "isp1",
        "parent_link_id": "",
        "notify_desired": "teams",
    },
    "SCL_ALGAR": {
        "link_id": "scl.algar.isp2",
        "carrier": "algar",
        "site": "scl",
        "saida": "isp2",
        "parent_link_id": "",
        "notify_desired": "teams",
    },
    "BGP_ISP1": {
        "link_id": "bgp.crosscnt.isp1",
        "carrier": "crosscnt",
        "site": "bgp",
        "saida": "isp1",
        "parent_link_id": "",
        "notify_desired": "teams",
    },
    "BGP_ISP2": {
        "link_id": "bgp.vivo.isp2",
        "carrier": "vivo",
        "site": "bgp",
        "saida": "isp2",
        "parent_link_id": "",
        "notify_desired": "teams",
    },
    "BRAS_ISP1": {
        "link_id": "bras.claro.isp1",
        "carrier": "claro",
        "site": "bras",
        "saida": "isp1",
        "parent_link_id": "",
        "notify_desired": "teams",
    },
    "FIA_ISP1": {
        "link_id": "fia.claro.isp1",
        "carrier": "claro",
        "site": "fia",
        "saida": "isp1",
        "parent_link_id": "",
        "notify_desired": "teams",
    },
    "FIA_ISP2": {
        "link_id": "fia.claro.isp2",
        "carrier": "claro",
        "site": "fia",
        "saida": "isp2",
        "parent_link_id": "",
        "notify_desired": "teams",
    },
    "DENIM_ISP1": {
        "link_id": "denim.flexus.isp1",
        "carrier": "flexus",
        "site": "denim",
        "saida": "isp1",
        "parent_link_id": "",
        "notify_desired": "teams",
    },
    "DENIM_ISP2": {
        "link_id": "denim.algar.isp2",
        "carrier": "algar",
        "site": "denim",
        "saida": "isp2",
        "parent_link_id": "",
        "notify_desired": "teams",
    },
    "SPO_ISP1_VPN": {
        "link_id": "spo.vivo.isp1.vpn-agg",
        "carrier": "vivo",
        "site": "spo",
        "saida": "isp1",
        "parent_link_id": "spo.vivo.isp1",
        "notify_desired": "no",
    },
    "SPO_ISP2_VPN": {
        "link_id": "spo.algar.isp2.vpn-agg",
        "carrier": "algar",
        "site": "spo",
        "saida": "isp2",
        "parent_link_id": "spo.algar.isp2",
        "notify_desired": "no",
    },
    "SCL_ISP1_VPN": {
        "link_id": "scl.vivo.isp1.vpn-agg",
        "carrier": "vivo",
        "site": "scl",
        "saida": "isp1",
        "parent_link_id": "scl.vivo.isp1",
        "notify_desired": "no",
    },
    "SCL_ISP2_VPN": {
        "link_id": "scl.algar.isp2.vpn-agg",
        "carrier": "algar",
        "site": "scl",
        "saida": "isp2",
        "parent_link_id": "scl.algar.isp2",
        "notify_desired": "no",
    },
    "BGP_ISP1_VPN": {
        "link_id": "bgp.crosscnt.isp1.vpn-agg",
        "carrier": "crosscnt",
        "site": "bgp",
        "saida": "isp1",
        "parent_link_id": "bgp.crosscnt.isp1",
        "notify_desired": "no",
    },
    "BGP_ISP2_VPN": {
        "link_id": "bgp.vivo.isp2.vpn-agg",
        "carrier": "vivo",
        "site": "bgp",
        "saida": "isp2",
        "parent_link_id": "bgp.vivo.isp2",
        "notify_desired": "no",
    },
    "BRAS_WAN1_VPN": {
        "link_id": "bras.claro.isp1.vpn-agg",
        "carrier": "claro",
        "site": "bras",
        "saida": "isp1",
        "parent_link_id": "bras.claro.isp1",
        "notify_desired": "no",
    },
    "BRAS_WAN2_VPN": {
        "link_id": "bras.isp2.vpn-agg",
        "carrier": "unknown",
        "site": "bras",
        "saida": "isp2",
        "parent_link_id": "",
        "notify_desired": "no",
    },
    "FIA_WAN1_VPN": {
        "link_id": "fia.claro.isp1.vpn-agg",
        "carrier": "claro",
        "site": "fia",
        "saida": "isp1",
        "parent_link_id": "fia.claro.isp1",
        "notify_desired": "no",
    },
    "FIA_WAN2_VPN": {
        "link_id": "fia.claro.isp2.vpn-agg",
        "carrier": "claro",
        "site": "fia",
        "saida": "isp2",
        "parent_link_id": "fia.claro.isp2",
        "notify_desired": "no",
    },
    "DENIM_WAN1_VPN": {
        "link_id": "denim.flexus.isp1.vpn-agg",
        "carrier": "flexus",
        "site": "denim",
        "saida": "isp1",
        "parent_link_id": "denim.flexus.isp1",
        "notify_desired": "no",
    },
    "DENIM_WAN2_VPN": {
        "link_id": "denim.algar.isp2.vpn-agg",
        "carrier": "algar",
        "site": "denim",
        "saida": "isp2",
        "parent_link_id": "denim.algar.isp2",
        "notify_desired": "no",
    },
}


def tags_of(obj: dict) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for tag in obj.get("tags", []):
        out[tag["tag"]].append(tag["value"])
    return out


def first_tag(tags: dict[str, list[str]], name: str, default: str = "") -> str:
    values = tags.get(name) or []
    return values[0] if values else default


def has_notify_teams(tags: dict[str, list[str]]) -> bool:
    return "teams" in tags.get("notify", [])


def load_cause_deps() -> dict[str, set[str]]:
    deps: dict[str, set[str]] = defaultdict(set)
    with MATRIX_FILE.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            for cause in row["causes"].split(";"):
                cause = cause.strip()
                if not cause:
                    continue
                for dep in row["dependencies"].split(";"):
                    dep = dep.strip()
                    if dep:
                        deps[cause].add(dep)
    return deps


def load_correlations() -> dict[str, list[str]]:
    corr: dict[str, list[str]] = defaultdict(list)
    with MATRIX_FILE.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            for cause in row["causes"].split(";"):
                cause = cause.strip()
                if cause:
                    corr[cause].append(f"{row['correlation_id']}:{row['operation']}")
    return corr


def extract_item_refs(expression: str) -> list[str]:
    # /HOST/key[params]
    return sorted(set(re.findall(r"/[^/\s]+/([^\s\),]+)", expression or "")))


def extract_health_members(expression: str) -> list[str]:
    # Prefer readable member names from comments/items; fallback to SNMP indexes in keys.
    keys = extract_item_refs(expression)
    members = []
    for key in keys:
        if "sdwan_health" in key or "fgVWLHealthCheck" in key:
            members.append(key)
    return members


def match_dep(value: str, deps: set[str]) -> str | None:
    """Match depends-on/interface value to the longest safe dependency prefix."""
    if not value:
        return None
    exact = [dep for dep in deps if dep and value == dep]
    if exact:
        return max(exact, key=len)

    candidates: list[str] = []
    for dep in deps:
        if not dep:
            continue
        boundary = re.search(rf"(^|[_-]){re.escape(dep)}($|[_-])", value)
        concat = re.match(rf"^{re.escape(dep)}[A-Za-z0-9]", value)
        if boundary or concat:
            candidates.append(dep)
    if not candidates:
        return None

    best = max(candidates, key=len)
    longer = [dep for dep in deps if dep.startswith(best) and dep != best and value.startswith(dep)]
    if longer:
        return max(longer, key=len)

    # Reject cross-variant absorption: AZ_MTZ_W1 must not absorb AZ_MTZ_W1_W2.
    if value != best and value.startswith(best):
        rest = value[len(best) :]
        variant = re.match(r"^[_-]W(\d)", rest)
        if variant:
            best_variant = re.search(r"W(\d)$", best)
            if best_variant and best_variant.group(1) != variant.group(1):
                return None
        elif re.match(r"^[_-]ISP", rest, re.I):
            return None
    return best


def match_tunnels(tunnels: list[dict], deps: set[str]) -> list[dict]:
    matched = []
    for tunnel in tunnels:
        tags = tags_of(tunnel)
        values = tags.get("depends-on", []) + tags.get("interface", []) + tags.get("sdwan-if", [])
        hit = None
        for value in values:
            hit = match_dep(value, deps)
            if hit:
                break
        if not hit:
            continue
        host = ",".join(h["host"] for h in tunnel.get("hosts", []))
        matched.append(
            {
                "host": host,
                "triggerid": tunnel["triggerid"],
                "name": tunnel.get("event_name") or tunnel.get("description") or "",
                "depends_on": ",".join(tags.get("depends-on", [])),
                "matched_dep": hit,
                "value": tunnel.get("value"),
            }
        )
    matched.sort(key=lambda row: (row["host"], row["name"]))
    return matched


def main() -> None:
    causes = json.loads(CAUSE_FILE.read_text(encoding="utf-8"))
    tunnels = json.loads(TUNNEL_FILE.read_text(encoding="utf-8"))
    cause_deps = load_cause_deps()
    correlations = load_correlations()

    rows = []
    markdown_sections = []

    for trigger in sorted(causes, key=lambda t: (t.get("hosts", [{}])[0].get("host", ""), t["triggerid"])):
        tags = tags_of(trigger)
        link_cause = first_tag(tags, "link-cause")
        if not link_cause:
            # try to recover from known inventory by triggerid via CANON keys later
            continue
        meta = CANON.get(link_cause)
        if not meta:
            meta = {
                "link_id": f"unknown.{link_cause.lower()}",
                "carrier": first_tag(tags, "carrier"),
                "site": first_tag(tags, "site"),
                "saida": first_tag(tags, "link"),
                "parent_link_id": "",
                "notify_desired": "teams",
            }
        host = ",".join(h["host"] for h in trigger.get("hosts", []))
        tipo = "agregado_vpn" if "vpn" in link_cause.lower() or "WAN" in link_cause else "causa_link"
        if link_cause.endswith("_VPN") or "WAN" in link_cause:
            tipo = "agregado_vpn"
        else:
            tipo = "causa_link"

        deps = cause_deps.get(link_cause, set())
        # For VPN aggregates, also include parent physical cause deps.
        parent_cause = None
        if meta.get("parent_link_id"):
            for lc, info in CANON.items():
                if info["link_id"] == meta["parent_link_id"]:
                    parent_cause = lc
                    deps = deps | cause_deps.get(lc, set())
                    break

        matched = match_tunnels(tunnels, deps) if deps else []
        item_names = []
        for item in trigger.get("items", []):
            item_names.append(item.get("name") or item.get("key_") or "")
        health_keys = extract_health_members(trigger.get("expression", ""))

        notify_now = "yes" if has_notify_teams(tags) else "no"
        mapeado = "sim" if meta.get("link_id") and not meta["link_id"].startswith("unknown.") and (matched or tipo == "causa_link") else "parcial"
        if tipo == "causa_link" and not item_names and not health_keys:
            mapeado = "parcial"

        tunnel_summary = "; ".join(
            f"{m['host']}:{m['depends_on'] or m['name']}[{m['matched_dep']}]"
            for m in matched
        )
        if len(tunnel_summary) > 900:
            tunnel_summary = tunnel_summary[:897] + "..."

        row = {
            "link_id_canonico": meta["link_id"],
            "parent_link_id": meta.get("parent_link_id", ""),
            "site_host": host,
            "site": meta.get("site") or first_tag(tags, "site"),
            "carrier": meta.get("carrier") or first_tag(tags, "carrier"),
            "saida": meta.get("saida") or first_tag(tags, "link"),
            "tipo": tipo,
            "link_cause_atual": link_cause,
            "triggerid": trigger["triggerid"],
            "event_name": trigger.get("event_name") or "",
            "description": trigger.get("description") or "",
            "severity": trigger.get("priority") or "",
            "status_value": trigger.get("value") or "",
            "notify_teams_atual": notify_now,
            "notify_teams_desejado": meta.get("notify_desired", "teams"),
            "health_items": " | ".join(item_names[:12]),
            "expression_item_keys": " | ".join(health_keys[:12]),
            "depends_on_prefixes_correlacao": ";".join(sorted(deps)),
            "tunnels_matched_count": str(len(matched)),
            "tunnels_dependentes": tunnel_summary,
            "correlacoes": ";".join(correlations.get(link_cause, [])),
            "mapeado": mapeado,
            "observacao": (
                "Agregado: sintoma do parent_link_id; nao deve ser causa primaria no Teams."
                if tipo == "agregado_vpn"
                else (
                    "Causa fisica ativa em 30/09; sintomas ja ranqueados nos 7 firewalls."
                    if link_cause == "SPO_VIVO" and trigger.get("value") == "1"
                    else ""
                )
            ),
        }
        rows.append(row)

        markdown_sections.append(
            {
                "link_id": meta["link_id"],
                "host": host,
                "link_cause": link_cause,
                "tipo": tipo,
                "triggerid": trigger["triggerid"],
                "event_name": trigger.get("event_name") or trigger.get("description"),
                "value": trigger.get("value"),
                "notify_now": notify_now,
                "notify_desired": meta.get("notify_desired"),
                "items": item_names,
                "deps": sorted(deps),
                "matched": matched,
                "parent": meta.get("parent_link_id", ""),
                "correlations": correlations.get(link_cause, []),
            }
        )

    # Ensure we didn't drop any CANON entries missing from API result.
    present = {r["link_cause_atual"] for r in rows}
    missing = [k for k in CANON if k not in present]
    if missing:
        print("MISSING_FROM_API", missing)

    fields = list(rows[0].keys())
    with OUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    # Markdown report
    lines = [
        "# Mapa de links e alertas — Fase A (30/09/2026)",
        "",
        "Inventário canônico gerado a partir das triggers de causa/agregado, tags `depends-on` dos `Tunnel down` e da matriz de correlação.",
        "",
        f"- Planilha: `{OUT_CSV.as_posix()}`",
        f"- Circuitos mapeados: **{len(rows)}**",
        f"- Causas físicas: **{sum(1 for r in rows if r['tipo']=='causa_link')}**",
        f"- Agregados VPN: **{sum(1 for r in rows if r['tipo']=='agregado_vpn')}**",
        f"- Tunnel downs inventariados: **{len(tunnels)}**",
        "",
        "## Convenção `link-id`",
        "",
        "`site.operadora.saida` para causa física; agregados usam sufixo `.vpn-agg` e apontam `parent_link_id`.",
        "",
        "## Circuitos",
        "",
    ]

    for section in sorted(markdown_sections, key=lambda s: (s["tipo"], s["link_id"])):
        lines.append(f"### `{section['link_id']}` — {section['host']}")
        lines.append("")
        lines.append(f"- Tipo: `{section['tipo']}`")
        lines.append(f"- `link-cause` atual: `{section['link_cause']}`")
        lines.append(f"- Trigger: `{section['triggerid']}` — {section['event_name']}")
        lines.append(f"- Estado: `{'PROBLEM' if section['value']=='1' else 'OK'}`")
        lines.append(f"- Teams atual/desejado: `{section['notify_now']}` / `{section['notify_desired']}`")
        if section["parent"]:
            lines.append(f"- Parent: `{section['parent']}`")
        if section["correlations"]:
            lines.append(f"- Correlações: {', '.join(section['correlations'])}")
        if section["items"]:
            lines.append("- Itens da expressão:")
            for item in section["items"][:10]:
                lines.append(f"  - {item}")
        if section["deps"]:
            lines.append(f"- Prefixos `depends-on` (correlação): `{'; '.join(section['deps'])}`")
        lines.append(f"- Túneis casados: **{len(section['matched'])}**")
        for tunnel in section["matched"][:20]:
            state = "PROBLEM" if tunnel["value"] == "1" else "OK"
            lines.append(
                f"  - `{tunnel['host']}` `{tunnel['depends_on'] or tunnel['name']}` "
                f"(match `{tunnel['matched_dep']}`, {state})"
            )
        if len(section["matched"]) > 20:
            lines.append(f"  - … +{len(section['matched']) - 20} túneis")
        lines.append("")

    lines.extend(
        [
            "## Lacunas remanescentes",
            "",
            "1. `AZ-VM-FW-01` não tem causa `Saida de internet`; entra só como ponta VPN dos hubs.",
            "2. `BRAS_WAN2_VPN` sem parent físico claro no inventário (carrier `unknown`).",
            "3. Health-checks SD-WAN e `High packets loss` ainda não foram listados linha a linha neste CSV (só túneis `Tunnel down` + itens das causas).",
            "4. Casos com `depends-on` vazio (`dmz`, `lan2`) ficam fora do casamento automático.",
            "",
            "## Próximo passo (Fase B)",
            "",
            "1. Revisar a tabela de `spo.vivo.isp1` (circuito ativo).",
            "2. Confirmar se todos os túneis listados devem depender desse link.",
            "3. Rodar `scripts/link_cause_rank_worker.py` contra a matriz preenchida.",
            "4. Em seguida padronizar `notify=teams` só nas causas físicas (Fase D).",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"csv": str(OUT_CSV), "md": str(OUT_MD), "rows": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
