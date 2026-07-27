#!/usr/bin/env python3
"""
Diagnóstico detalhado por host no Zabbix.

Para cada host avalia:
  - Disponibilidade de cada interface (Agente Zabbix, SNMP)
  - Erros de coleta com mensagens específicas
  - Possível correção para cada problema
  - Hosts sem nenhuma conexão estabelecida
  - Hosts pendentes de configuração da nossa parte

Uso:
  python3 scripts/zabbix_audit_hosts.py
  python3 scripts/zabbix_audit_hosts.py --output diagnostico.csv
"""

import csv
import json
import argparse
import urllib.request
from collections import Counter
from datetime import datetime

ZABBIX_URL  = "http://172.17.2.51/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASS = "zabbix"

OUTPUT_DEFAULT = "docs/zabbix_diagnostico_{}.csv".format(
    datetime.now().strftime("%Y%m%d_%H%M%S")
)

AVAIL_MAP = {"0": "Desconhecido", "1": "OK", "2": "Indisponível"}
SNMP_VER  = {"1": "SNMPv1", "2": "SNMPv2c", "3": "SNMPv3"}

# Templates que NÃO usam agente nem SNMP — disponibilidade de interface é irrelevante
TMPL_ICMP      = "10564"   # Template Module ICMP Ping
TMPL_FORTIGATE = "10603"   # FortiGate by HTTP

GRUPOS_CONFIGURADOS = {
    "Switches Cisco", "UPS", "QNAP", "FortiGate", "Firewalls",
    "NAS", "NAS QNAP", "Access Points Aruba", "Servidores Windows",
    "Servidores Linux", "iDRAC Dell", "Equipamentos Especiais", "Hyper-V",
    "Monitoramento Web",
}


# ── API ────────────────────────────────────────────────────────────────────────

def api(token, method, params):
    payload = json.dumps({
        "jsonrpc": "2.0", "method": method,
        "params": params, "auth": token, "id": 1,
    }).encode()
    req = urllib.request.Request(
        ZABBIX_URL, data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    if "error" in result:
        raise RuntimeError(f"API [{method}]: {result['error']}")
    return result["result"]


def login():
    payload = json.dumps({
        "jsonrpc": "2.0", "method": "user.login",
        "params": {"username": ZABBIX_USER, "password": ZABBIX_PASS}, "id": 1,
    }).encode()
    req = urllib.request.Request(
        ZABBIX_URL, data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
    if "error" in result:
        raise RuntimeError(f"Login: {result['error']}")
    return result["result"]


def get_item_errors(token, hostids):
    """Retorna {hostid: [mensagem, ...]} para itens habilitados com falha."""
    items = api(token, "item.get", {
        "output": ["hostid", "name", "key_", "error", "state"],
        "hostids": hostids,
        "filter": {"state": 1, "status": 0},
        "limit": 10000,
    })
    errors = {}
    for item in items:
        hid = item["hostid"]
        msg = item.get("error") or "não suportado"
        errors.setdefault(hid, []).append(f"{item['name']}: {msg}")
    return errors


# ── Helpers ────────────────────────────────────────────────────────────────────

def extract_site(grupos_nomes):
    for g in grupos_nomes:
        for site in ("SCL", "SPO", "BGP", "DCT", "FIA"):
            if site in g:
                return site
    return ""


def extract_tipo(grupos_nomes):
    priority = [
        ("Switches Cisco", "Switch Cisco"),
        ("UPS",            "UPS"),
        ("QNAP",           "NAS QNAP"),
        ("FortiGate",      "Firewall FortiGate"),
        ("Firewalls",      "Firewall"),
        ("NAS",            "NAS"),
        ("iDRAC",          "iDRAC Dell"),
        ("Access Points",  "Access Point Aruba"),
        ("Em Classificação", "Em Classificação"),
        ("Hyper-V",        "Hyper-V"),
        ("Linux",          "Servidor Linux"),
        ("Windows",        "Servidor Windows"),
        ("Equipamentos",   "Equipamento Especial"),
    ]
    for g in grupos_nomes:
        for keyword, tipo in priority:
            if keyword in g:
                return tipo
    return "Outro"


def suggest_correction(grupos_nomes, agent_avail, snmp_avail,
                       tem_template, uses_agent, uses_snmp):
    """Retorna sugestão de correção com base no grupo e na disponibilidade."""
    grupos_str = " ".join(grupos_nomes)

    if not tem_template:
        if "Em Classificação" in grupos_nomes:
            return "Classificar: executar zabbix_classificar_planilha.py para atribuir template e grupo"
        if "Monitoramento Web" in grupos_nomes:
            return ""
        return "Sem template — aplicar template adequado ao tipo de equipamento"

    corrections = []

    if uses_agent and agent_avail == "2":
        if any(g in grupos_str for g in ("Servidores Linux", "Linux")):
            corrections.append(
                "Instalar agente Zabbix passivo no Linux "
                "(Server=172.17.2.51, porta 10050)"
            )
        elif any(g in grupos_str for g in ("Servidores Windows", "Windows")):
            corrections.append(
                "Instalar agente Zabbix passivo no Windows "
                "(Server=172.17.2.51, porta 10050)"
            )
        elif "Hyper-V" in grupos_str:
            corrections.append(
                "Verificar serviço do agente Zabbix no Hyper-V "
                "(Server=172.17.2.51, porta 10050)"
            )
        else:
            corrections.append(
                "Agente Zabbix inacessível — verificar serviço e firewall (porta TCP 10050)"
            )

    if uses_snmp and snmp_avail == "2":
        if "iDRAC" in grupos_str:
            corrections.append(
                "Habilitar SNMP no iDRAC: versão SNMPv2c, community=capri@123, "
                "porta UDP 161, permitir IP 172.17.2.51"
            )
        elif "UPS" in grupos_str:
            corrections.append(
                "UPS Phoenixtec: adicionar IP 172.17.2.51 na whitelist NMS do equipamento. "
                "UPS APC: verificar community SNMPv2c e acessibilidade UDP 161"
            )
        elif any(g in grupos_str for g in ("Switches Cisco", "Cisco")):
            corrections.append(
                "Habilitar SNMPv3 no switch: user=zabbix_snmp, "
                "auth=SHA1/ZbxAuth_2026@Net, priv=AES128/ZbxPriv_2026@Secure"
            )
        elif any(g in grupos_str for g in ("QNAP", "NAS")):
            corrections.append(
                "Habilitar SNMPv3 no QNAP: user=zabbix_snmp, "
                "auth=SHA1/ZbxAuth_2026@Net, priv=DES/ZbxPriv_2026@Secure"
            )
        elif any(g in grupos_str for g in ("Firewalls", "FortiGate")):
            corrections.append(
                "Verificar acesso SNMP/HTTP ao FortiGate (permitir 172.17.2.51)"
            )
        else:
            corrections.append(
                "SNMP indisponível — verificar configuração SNMPv3 e porta UDP 161"
            )

    return " | ".join(corrections) if corrections else ""


# ── Classificação principal ────────────────────────────────────────────────────

def classify_host(host, item_errors):
    """Retorna dict com todos os campos de diagnóstico para o host."""
    grupos_nomes  = [g["name"] for g in host["groups"]]
    tem_template  = len(host["parentTemplates"]) > 0
    template_ids  = {t["templateid"] for t in host["parentTemplates"]}
    templates_str = ", ".join(t["name"] for t in host["parentTemplates"])

    ifaces       = host.get("interfaces", [])
    snmp_ifaces  = [i for i in ifaces if i.get("type") == "2"]
    agent_ifaces = [i for i in ifaces if i.get("type") == "1"]

    main_iface = snmp_ifaces[0] if snmp_ifaces else (ifaces[0] if ifaces else {})
    ip = main_iface.get("ip", "")

    snmp_version = ""
    if snmp_ifaces:
        details = snmp_ifaces[0].get("details", {})
        snmp_version = SNMP_VER.get(str(details.get("version", "")), "")

    # Zabbix 7.0: availability moved to interface level — host.available is no longer returned
    agent_avail_raw = str(agent_ifaces[0].get("available", "0")) if agent_ifaces else "0"
    snmp_avail_raw  = str(snmp_ifaces[0].get("available", "0"))  if snmp_ifaces else "0"

    # Hosts com template ICMP-only ou HTTP não usam agente nem SNMP diretamente
    is_icmp_only  = bool(template_ids) and template_ids <= {TMPL_ICMP}
    is_http_based = TMPL_FORTIGATE in template_ids

    uses_snmp  = bool(snmp_ifaces) and not is_icmp_only and not is_http_based
    uses_agent = bool(agent_ifaces) and not is_icmp_only and not is_http_based

    # ── Status de conexão detalhado ──────────────────────────────────────────
    conn_parts = []
    if uses_snmp:
        conn_parts.append(f"SNMP:{AVAIL_MAP.get(snmp_avail_raw, '?')}")
    if uses_agent:
        conn_parts.append(f"Agente:{AVAIL_MAP.get(agent_avail_raw, '?')}")
    if is_icmp_only:
        conn_parts.append("ICMP only")
    if is_http_based and not uses_snmp:
        conn_parts.append("HTTP")
    conn_status = " | ".join(conn_parts) if conn_parts else "Desconhecido"

    # ── Erros de itens ───────────────────────────────────────────────────────
    erros        = item_errors.get(host["hostid"], [])
    erros_count  = len(erros)
    erros_detail = "; ".join(erros[:5])
    if erros_count > 5:
        erros_detail += f" [+{erros_count - 5} mais]"

    # ── Status de configuração ───────────────────────────────────────────────
    eh_configurado = any(
        any(gc in g for gc in GRUPOS_CONFIGURADOS) for g in grupos_nomes
    )

    sem_conexao = (
        (uses_snmp  and snmp_avail_raw  == "2") or
        (uses_agent and agent_avail_raw == "2")
    )

    # Hosts de monitoramento web são configurados por cenários/itens, sem template
    is_web_monitoring = "Monitoramento Web" in grupos_nomes

    if ("Em Classificação" in grupos_nomes) or (not tem_template and not is_web_monitoring):
        config_status = "PENDENTE CONFIG"
    elif sem_conexao:
        config_status = "SEM CONEXÃO"
    elif erros_count > 0 and eh_configurado:
        config_status = "OK (device-side)"
    elif erros_count > 0:
        config_status = "COM ERROS"
    else:
        config_status = "OK"

    correction = suggest_correction(
        grupos_nomes, agent_avail_raw, snmp_avail_raw,
        tem_template, uses_agent, uses_snmp,
    )

    return {
        "IP":                   ip,
        "Hostname":             host["host"],
        "Nome Visível":         host["name"],
        "Site":                 extract_site(grupos_nomes),
        "Tipo":                 extract_tipo(grupos_nomes),
        "Grupos":               "; ".join(grupos_nomes),
        "Templates":            templates_str,
        "SNMP Versão":          snmp_version,
        "Agente Disponível":    AVAIL_MAP.get(agent_avail_raw, "?") if uses_agent else "N/A",
        "SNMP Disponível":      AVAIL_MAP.get(snmp_avail_raw, "?")  if uses_snmp  else "N/A",
        "Status Conexão":       conn_status,
        "Status Configuração":  config_status,
        "Qtd Erros Itens":      erros_count,
        "Erros Itens":          erros_detail,
        "Possível Correção":    correction,
    }


def main():
    parser = argparse.ArgumentParser(description="Diagnóstico detalhado de hosts Zabbix → CSV")
    parser.add_argument("--output", "-o", default=OUTPUT_DEFAULT, help="Arquivo CSV de saída")
    args = parser.parse_args()

    print("Autenticando na API Zabbix...")
    token = login()

    print("Buscando todos os hosts...")
    hosts = api(token, "host.get", {
        "output": ["hostid", "host", "name", "description"],
        "selectGroups":          ["groupid", "name"],
        "selectInterfaces":      ["interfaceid", "ip", "type", "available", "details"],
        "selectParentTemplates": ["templateid", "name"],
        "limit": 10000,
    })
    print(f"  {len(hosts)} hosts encontrados.")

    hostids = [h["hostid"] for h in hosts]
    print("Buscando itens com erro...")
    item_errors = get_item_errors(token, hostids)
    print(f"  {len(item_errors)} hosts com erros em itens.")

    rows = [
        classify_host(h, item_errors)
        for h in sorted(hosts, key=lambda h: h.get("name", ""))
    ]

    ordem = {
        "PENDENTE CONFIG":  0,
        "SEM CONEXÃO":      1,
        "COM ERROS":        2,
        "OK (device-side)": 3,
        "OK":               4,
    }
    rows.sort(key=lambda r: (
        ordem.get(r["Status Configuração"], 5),
        r["Site"],
        r["IP"],
    ))

    fieldnames = [
        "IP", "Hostname", "Nome Visível", "Site", "Tipo", "Grupos",
        "Templates", "SNMP Versão",
        "Agente Disponível", "SNMP Disponível", "Status Conexão",
        "Status Configuração", "Qtd Erros Itens", "Erros Itens",
        "Possível Correção",
    ]

    print(f"Salvando em {args.output}...")
    with open(args.output, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # ── Resumo no terminal ───────────────────────────────────────────────────
    contagem    = Counter(r["Status Configuração"] for r in rows)
    sem_conexao = [r for r in rows if r["Status Configuração"] == "SEM CONEXÃO"]
    pendentes   = [r for r in rows if r["Status Configuração"] == "PENDENTE CONFIG"]
    com_erros   = [r for r in rows if r["Status Configuração"] == "COM ERROS"]

    print("\n══════════════════════════════════════════════════════")
    print(f"  Diagnóstico concluído — {len(rows)} hosts")
    print("══════════════════════════════════════════════════════")
    for status in ["PENDENTE CONFIG", "SEM CONEXÃO", "COM ERROS", "OK (device-side)", "OK"]:
        count = contagem.get(status, 0)
        if count:
            print(f"  {status:<25} {count:>4}")
    print("══════════════════════════════════════════════════════")

    if sem_conexao:
        print(f"\n  Hosts SEM CONEXÃO ({len(sem_conexao)}) — ação necessária:")
        for r in sem_conexao[:25]:
            corr = r["Possível Correção"][:65] if r["Possível Correção"] else "-"
            print(f"    {r['IP']:18s}  {r['Hostname']:35s}  {corr}")
        if len(sem_conexao) > 25:
            print(f"    ... e mais {len(sem_conexao) - 25} — veja o CSV")

    if com_erros:
        print(f"\n  Hosts COM ERROS inesperados ({len(com_erros)}):")
        for r in com_erros[:10]:
            print(f"    {r['IP']:18s}  {r['Hostname']:35s}  {r['Erros Itens'][:60]}")

    if pendentes:
        print(f"\n  Hosts PENDENTE CONFIG ({len(pendentes)}):")
        for r in pendentes[:10]:
            print(f"    {r['IP']:18s}  {r['Hostname']}")
        if len(pendentes) > 10:
            print(f"    ... e mais {len(pendentes) - 10} — veja o CSV")

    print(f"\n  CSV salvo: {args.output}")


if __name__ == "__main__":
    main()
