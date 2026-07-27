#!/usr/bin/env python3
"""
Classifica todos os hosts do Zabbix com base na planilha opmanager.

Para cada entrada da planilha:
  - Se já está no Zabbix (por IP) → renomeia e move para o grupo correto
  - Se não está → cria com template e grupo adequados

Uso:
  python3 scripts/zabbix_classificar_planilha.py
  python3 scripts/zabbix_classificar_planilha.py --dry-run
"""

import json, urllib.request, openpyxl, argparse
from collections import defaultdict

ZABBIX_URL    = "http://172.17.2.51/api_jsonrpc.php"
ZABBIX_USER   = "Admin"
ZABBIX_PASS   = "zabbix"
PLANILHA      = "docs/relação opmanager.xlsx"

SNMPv3 = {
    "version": 3, "bulk": 1,
    "securityname": "zabbix_snmp",
    "securitylevel": 2,
    "authprotocol": 1,  "authpassphrase": "ZbxAuth_2026@Net",
    "privprotocol": 1,  "privpassphrase": "ZbxPriv_2026@Secure",
    "contextname": "",
}

SNMPv2C_IDRAC = {"version": 2, "bulk": 1, "community": "capri@123"}

# templateid → nome (verificados no Zabbix)
TMPL_ICMP    = "10564"  # Template Module ICMP Ping
TMPL_CISCO   = "10218"  # Cisco IOS by SNMP
TMPL_IDRAC   = "10255"  # Dell iDRAC by SNMP
TMPL_LINUX   = "10001"  # Linux by Zabbix agent
TMPL_WIN     = "10081"  # Windows by Zabbix agent
TMPL_QNAP    = "10693"  # SNMP QNAP
TMPL_FORTIGATE  = "10603"  # FortiGate by HTTP
TMPL_PHOENIXTEC = "10863"  # Phoenixtec UPS by SNMP
TMPL_APC        = "10395"  # APC UPS by SNMP
TMPL_ARUBA      = "10943"  # Aruba IAP by SNMPv3

# ── Mapeamento tipo → (grupo_base, templateid, interface) ────────────────────
# interface: "agent" = tipo 1 porta 10050 | "snmp" = tipo 2 porta 161 SNMPv3
TYPE_CONFIG = {
    "Aruba IAP":                    ("Access Points Aruba", TMPL_ARUBA,    "snmp"),
    "Aruba IAP Virtual Controller": ("Access Points Aruba", TMPL_ARUBA,    "snmp"),
    "Aruba Device_1":               ("Access Points Aruba", TMPL_ARUBA,    "snmp"),
    "Dell PowerEdge iDRAC":         ("iDRAC Dell",          TMPL_IDRAC,    "snmpv2c_idrac"),
    "Linux":                        ("Servidores Linux",     TMPL_LINUX,    "agent"),
    "Windows 2022":                 ("Servidores Windows",   TMPL_WIN,      "agent"),
    "Windows 2016":                 ("Servidores Windows",   TMPL_WIN,      "agent"),
    "Windows 10":                   ("Servidores Windows",   TMPL_WIN,      "agent"),
    "Qnap QTS Storage":             ("NAS QNAP",             TMPL_QNAP,     "snmp"),
    "QNAP-Storage":                 ("NAS QNAP",             TMPL_QNAP,     "snmp"),
    "Fortinet FortiGate 100F":      ("Firewalls",            TMPL_ICMP,     "agent"),
    "Fortinet fw60EI":              ("Firewalls",            TMPL_ICMP,     "agent"),
    "Fortinet fgt40F":              ("Firewalls",            TMPL_ICMP,     "agent"),
    "Cisco CBS350-48P-4X":          ("Switches Cisco",       TMPL_CISCO,    "snmp"),
    "Cisco CBS350-24P-4X":          ("Switches Cisco",       TMPL_CISCO,    "snmp"),
    "Cisco CBS350 Series":          ("Switches Cisco",       TMPL_CISCO,    "snmp"),
    "Cisco Device_2":               ("Switches Cisco",       TMPL_CISCO,    "snmp"),
    "Phoenixtec UPS":               ("UPS",                  TMPL_PHOENIXTEC, "snmp"),
    "APC Smart-UPS 1500":           ("UPS",                  TMPL_APC,      "snmp"),
    "APC Smart-UPS SRC 6000":       ("UPS",                  TMPL_APC,      "snmp"),
    # Tudo mais → Equipamentos Especiais com ping
    "EVO":                          ("Equipamentos Especiais", TMPL_ICMP,   "agent"),
    "BioPoint II":                  ("Equipamentos Especiais", TMPL_ICMP,   "agent"),
    "Term-1S":                      ("Equipamentos Especiais", TMPL_ICMP,   "agent"),
    "WAGO Kontakttechnik Device_1": ("Equipamentos Especiais", TMPL_ICMP,   "agent"),
    "RICOH":                        ("Equipamentos Especiais", TMPL_ICMP,   "agent"),
    "Zebra Printer":                ("Equipamentos Especiais", TMPL_ICMP,   "agent"),
    "SS 3530 MF FACE W":            ("Equipamentos Especiais", TMPL_ICMP,   "agent"),
}
DEFAULT_CONFIG = ("Equipamentos Especiais", TMPL_ICMP, "agent")

# Grupos sem divisão por site
GRUPOS_SEM_SITE = {"Equipamentos Especiais"}


def api_call(method, params, token=None):
    payload = json.dumps({"jsonrpc":"2.0","method":method,"params":params,"auth":token,"id":1}).encode()
    req = urllib.request.Request(ZABBIX_URL, data=payload, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read())
    if "error" in result:
        raise RuntimeError(f"{method}: {result['error']}")
    return result["result"]


def login():
    token = api_call("user.login", {"username": ZABBIX_USER, "password": ZABBIX_PASS})
    return token


def extract_site(hostname):
    name = hostname.upper()
    for site in ("BGP", "SCL", "SPO", "DCT", "FIA"):
        if name.startswith(site + "-") or name.startswith("IDRAC-" + site + "-"):
            return site
    return None


def resolve_group(group_base, site, group_map):
    """Retorna groupid, criando o grupo se necessário."""
    if group_base in GRUPOS_SEM_SITE:
        key = group_base
    elif site:
        key = f"{group_base}/{site}"
    else:
        key = group_base

    if key not in group_map:
        print(f"  [+] Criando grupo: {key}")
        result = api_call("hostgroup.create", {"name": key})
        group_map[key] = result["groupids"][0]

    return group_map[key]


def build_interface(iface_type, ip):
    base = {"main": 1, "useip": 1, "ip": ip, "dns": ""}
    if iface_type == "snmp":
        return {**base, "type": 2, "port": "161", "details": SNMPv3}
    if iface_type == "snmpv2c_idrac":
        return {**base, "type": 2, "port": "161", "details": SNMPv2C_IDRAC}
    return {**base, "type": 1, "port": "10050"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Mostrar o que seria feito sem executar")
    args = parser.parse_args()
    dry = args.dry_run

    if dry:
        print("=== DRY RUN — nenhuma alteração será feita ===\n")

    print("Carregando planilha...")
    wb = openpyxl.load_workbook(PLANILHA, data_only=True)
    ws = wb["Planilha1"]
    sheet_rows = [(str(r[0]).strip(), str(r[1]).strip(), str(r[2]).strip())
                  for r in ws.iter_rows(values_only=True)
                  if r[0] and r[1] and r[2]]
    print(f"  {len(sheet_rows)} entradas na planilha")

    print("Conectando ao Zabbix...")
    token = login()

    # Carregar estado atual do Zabbix
    zabbix_hosts = api_call("host.get", {
        "output": ["hostid","host","name"],
        "selectInterfaces": ["interfaceid","ip","type"],
        "selectGroups": ["groupid","name"],
        "selectParentTemplates": ["templateid","name"],
        "limit": 10000,
    }, token)

    zabbix_by_ip = {}
    for h in zabbix_hosts:
        for iface in h.get("interfaces", []):
            zabbix_by_ip[iface["ip"]] = h

    # Carregar grupos existentes
    groups_raw = api_call("hostgroup.get", {"output": ["groupid","name"],"limit": 500}, token)
    group_map = {g["name"]: g["groupid"] for g in groups_raw}

    # Pré-criar todos os grupos necessários antes de processar hosts
    # Detectar nomes duplicados na planilha — Virtual Controller recebe sufixo -VC
    name_count = defaultdict(int)
    for name, _, _ in sheet_rows:
        name_count[name] += 1
    vc_types = {"Aruba IAP Virtual Controller", "Aruba Device_1"}

    def resolve_name(sheet_name, tipo):
        if name_count[sheet_name] > 1 and tipo in vc_types:
            return sheet_name + "-VC"
        return sheet_name

    print("Verificando grupos necessários...")
    needed_groups = set()
    for sheet_name, ip, tipo in sheet_rows:
        resolved_name = resolve_name(sheet_name, tipo)
        cfg = TYPE_CONFIG.get(tipo, DEFAULT_CONFIG)
        group_base = cfg[0]
        site = extract_site(resolved_name)
        key = group_base if group_base in GRUPOS_SEM_SITE else (f"{group_base}/{site}" if site else group_base)
        needed_groups.add(key)

    for key in sorted(needed_groups):
        if key not in group_map:
            print(f"  [+] Criando grupo: {key}")
            if not dry:
                result = api_call("hostgroup.create", {"name": key}, token)
                group_map[key] = result["groupids"][0]

    # Rastreia nomes já atribuídos nesta execução para evitar colisões
    used_names = {h["host"] for h in zabbix_hosts}

    # Processar
    stats = defaultdict(int)
    already_fine = []
    updated = []
    created = []

    for sheet_name, ip, tipo in sheet_rows:
        sheet_name = resolve_name(sheet_name, tipo)
        cfg = TYPE_CONFIG.get(tipo, DEFAULT_CONFIG)
        group_base, template_id, iface_type = cfg
        site = extract_site(sheet_name)

        group_key = group_base if group_base in GRUPOS_SEM_SITE else (f"{group_base}/{site}" if site else group_base)
        group_id = group_map.get(group_key)

        if ip in zabbix_by_ip:
            h = zabbix_by_ip[ip]
            zbx_hostname = h["host"]
            groups_now = {g["name"] for g in h.get("groups", [])}
            tmpls_now = {t["templateid"] for t in h.get("parentTemplates", [])}
            em_classificacao = "Em Classificação" in groups_now

            # Já está configurado corretamente?
            name_ok = (zbx_hostname == sheet_name)
            # Para hosts que já têm template e não estão em Em Classificação
            group_ok = not em_classificacao and any(
                (group_base in g) for g in groups_now
            )
            tmpl_ok = template_id in tmpls_now

            if name_ok and group_ok and tmpl_ok:
                already_fine.append((ip, sheet_name, tipo))
                stats["already_ok"] += 1
                continue

            # Precisa atualizar
            changes = []
            update_params = {"hostid": h["hostid"]}

            if not name_ok:
                update_params["host"] = sheet_name
                update_params["name"] = sheet_name
                changes.append(f"rename: {zbx_hostname} → {sheet_name}")

            if not group_ok or em_classificacao:
                update_params["groups"] = [{"groupid": group_id}]
                changes.append(f"grupo → {group_base}/{site or ''}")

            if not tmpl_ok:
                # Adiciona template mantendo os existentes (que fazem sentido)
                existing_good_tmpls = [
                    {"templateid": t["templateid"]}
                    for t in h.get("parentTemplates", [])
                    if t["templateid"] not in ("57",)  # não manter Em Classificação
                ]
                update_params["templates"] = existing_good_tmpls + [{"templateid": template_id}]
                changes.append(f"template → {template_id}")

            # Evitar colisão de nome com outro host já processado nesta execução
            if not name_ok and sheet_name in used_names:
                print(f"  [!] {ip:18s}  {sheet_name:35s} | SKIP — nome já existe, verifique duplicata na planilha")
                stats["skipped"] += 1
                continue

            print(f"  [U] {ip:18s}  {sheet_name:35s} | {'; '.join(changes)}")

            if not dry:
                api_call("host.update", update_params, token)
            used_names.add(sheet_name)

            updated.append((ip, sheet_name, tipo, changes))
            stats["updated"] += 1

        else:
            # Criar novo host
            if sheet_name in used_names:
                print(f"  [!] {ip:18s}  {sheet_name:35s} | SKIP — nome já existe, verifique duplicata na planilha")
                stats["skipped"] += 1
                continue

            iface = build_interface(iface_type, ip)
            print(f"  [C] {ip:18s}  {sheet_name:35s} | {tipo}")

            if not dry:
                api_call("host.create", {
                    "host": sheet_name,
                    "name": sheet_name,
                    "interfaces": [iface],
                    "groups": [{"groupid": group_id}],
                    "templates": [{"templateid": template_id}],
                }, token)

            if not dry:
                used_names.add(sheet_name)
            created.append((ip, sheet_name, tipo))
            stats["created"] += 1

    print("\n══════════════════════════════════════════════════════")
    print(f"  Classificação{'  [DRY RUN]' if dry else ''} concluída")
    print("══════════════════════════════════════════════════════")
    print(f"  Já corretos (sem alteração): {stats['already_ok']}")
    print(f"  Atualizados (rename/grupo):  {stats['updated']}")
    print(f"  Criados (novos):             {stats['created']}")
    if stats["skipped"]:
        print(f"  Ignorados (nome duplicado):  {stats['skipped']}")
    print("══════════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
