#!/usr/bin/env python3
"""
link_roles.py
-----------------------------------------------------------------------------
Linka as roles/templates em cada host conforme o mapeamento (tabela + correcoes).
- Idempotente: adiciona SO o que falta (nao duplica, nao remove o que ja existe).
- UNLINK: remove (e limpa) templates errados de hosts especificos.
- Os "avisos" sao as triggers que ja vem nos templates:
    * Interface caiu      -> Windows/Linux by Zabbix agent (link down)
    * Cluster / Hyper-V    -> Role - Servidor Hyper-V (ClusSvc, vmms)
    * Servico/app parado   -> roles de aplicacao

Precisa de TOKEN ADMIN com escrita (o usuario MCP e read-only).

Uso:
  ZBX_URL=http://172.17.2.51/api_jsonrpc.php ZBX_TOKEN=<token_admin> python link_roles.py --dry-run
  ZBX_URL=http://172.17.2.51/api_jsonrpc.php ZBX_TOKEN=<token_admin> python link_roles.py
-----------------------------------------------------------------------------
"""
import os, sys, json, urllib.request

URL = os.environ.get("ZBX_URL", "http://172.17.2.51/api_jsonrpc.php")
TOKEN = os.environ.get("ZBX_TOKEN", "")
DRY = "--dry-run" in sys.argv

# host -> templates que devem estar linkados (adiciona se faltar)
LINK = {
    "BGP-SRV-FHV01": ["Role - Servidor Hyper-V"],
    "BGP-SRV-FHV02": ["Role - Servidor Hyper-V"],
    "BGP-SRV-FHV03": ["Role - Servidor Hyper-V"],
    "BGP-SRV-FREP":  ["Role - Veeam Repository Linux"],
    "BGP-SRV-V02":   ["Role - Controlador de Dominio Primario On-Prem"],
    "BGP-SRV-V03":   ["Role - Veeam ONE"],
    "BGP-SRV-V04":   ["Role - SQL Server"],   # ja monitorado (Veeam ONE/Lansweeper cobertos a parte)
    "BGP-SRV-V06":   ["Role - Clipnet"],      # banco Firebird do Clipnet
    "BGP-SRV-VAD01": ["Role - Controlador de Dominio Secundario com CA"],
    "BGP-SRV-VAPP02": ["Role - Veeam Backup"],
    "BGP-SRV-VAPP04": ["Role - Fact Teares"],
    "BGP-SRV-VAPP06": ["Role - SQL Server"],
    "BGP-SRV-VAPP10": ["Role - Servidor IIS"],
    "BGP-SRV-VAPP11": ["Role - Totvs"],
    "BGP-SRV-VAPP12": ["Role - Servidor IIS"],
    "BGP-SRV-VAPP28": ["Role - Entra Connect e Gateways"],
    "BGP-SRV-VAPP29": ["Role - Deps Homolog"],   # DepsIntegrador (homolog); banco ja monitorado a parte
    "SCL-SRV-FHV02": ["Role - Servidor Hyper-V"],
    "SCL-SRV-FHV03": ["Role - Servidor Hyper-V"],
    "SCL-SRV-FREP":  ["Role - Veeam Repository Linux"],
    "SCL-SRV-V02":   ["Role - Controlador de Dominio Primario On-Prem"],
    "SCL-SRV-V03":   ["Role - Controlador de Dominio Secundario"],
    "SCL-SRV-V04":   ["Role - Cisco Dashboard e Oxidized Linux"],
    "SCL-SRV-V05":   ["Role - Clickhouse Linux", "Role - Docker Linux"],
    "SCL-SRV-V06":   ["Role - Clipnet"],      # banco Firebird do Clipnet (SCL)
    # SCL-SRV-V07: proxy Zabbix de TERCEIRO (sem acesso) -> nao gerenciamos
    "SCL-SRV-VAPP01": ["Role - Dimep"],
    # SCL-SRV-VAPP02: so o banco do Dimep, ja monitorado pelo template PostgreSQL
    "SCL-SRV-VAPP02": ["Role - SQL Server"],
    "SCL-SRV-VAPP03": ["Role - NodeRed"],
    "SCL-SRV-VAPP13": ["Role - Entra Connect e Gateways"],
    "SCL-SRV-VAPP14": ["Role - EAS Cozinha"],
    # SCL-SRV-VAPP15: HOMOLOGACAO (apps off de proposito) -> sem monitoramento de disponibilidade
    "SPO-SRV-FAD01": ["Role - Controlador de Dominio Primario On-Prem",
                      "Role - Servidor Hyper-V", "Role - Entra Connect e Gateways"],
    "SPO-SRV-V02":   ["Role - PostgreSQL Linux"],
    "SPO-SRV-V03":   ["Role - Grafana Linux"],
    "SPO-SRV-V05":   ["Role - Fastweb Linux"],
    "SPO-SRV-VAPP04": ["Role - Veeam Repository Linux"],
    "AZ-VM-APP-03":  ["Role - GLPI Linux"],
    "AZ-VM-DC-01":   ["Role - Controlador de Dominio Azure"],
    "AZ-VM-DC-02":   ["Role - Controlador de Dominio Azure"],
}

# host -> templates ERRADOS a remover (unlink + clear)
UNLINK = {
    "BGP-SRV-V08":   ["Role - Zabbix Proxy"],          # host e Linux, role e Windows
    "SCL-SRV-VAPP12": ["Role - Fact Teares"],          # SCL nao tem Portal Teares/Agent Fact
}


def call(method, params):
    body = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {TOKEN}",
    })
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if "error" in r:
        raise RuntimeError(f"{method}: {r['error']}")
    return r["result"]


def main():
    if not TOKEN:
        sys.exit("ERRO: defina ZBX_TOKEN (token admin com escrita).")
    print(f">> Zabbix: {URL} | {'DRY-RUN (nada sera alterado)' if DRY else 'APLICANDO'}")

    # 1) Resolver template name -> id
    names = sorted({t for ts in LINK.values() for t in ts} | {t for ts in UNLINK.values() for t in ts})
    tpls = call("template.get", {"output": ["templateid", "host"], "filter": {"host": names}})
    tid = {t["host"]: t["templateid"] for t in tpls}
    faltando = [n for n in names if n not in tid]
    if faltando:
        print("   AVISO: templates nao encontrados (importe o YAML antes):", faltando)

    # 2) Resolver host name -> id + templates atuais
    hostnames = sorted(set(LINK) | set(UNLINK))
    hosts = call("host.get", {"output": ["hostid", "host"], "filter": {"host": hostnames},
                              "selectParentTemplates": ["name"]})
    hmap = {h["host"]: h for h in hosts}

    add_count = rm_count = 0
    # 3) LINK (adiciona o que falta)
    for host, want in LINK.items():
        h = hmap.get(host)
        if not h:
            print(f"   [skip] host nao encontrado: {host}")
            continue
        atual = {p["name"] for p in h.get("parentTemplates", [])}
        falta = [t for t in want if t in tid and t not in atual]
        if not falta:
            continue
        print(f"   + {host}: {falta}")
        add_count += len(falta)
        if not DRY:
            call("host.massadd", {"hosts": [{"hostid": h["hostid"]}],
                                  "templates": [{"templateid": tid[t]} for t in falta]})

    # 4) UNLINK (remove + limpa os errados)
    for host, bad in UNLINK.items():
        h = hmap.get(host)
        if not h:
            continue
        atual = {p["name"] for p in h.get("parentTemplates", [])}
        rm = [t for t in bad if t in tid and t in atual]
        if not rm:
            continue
        print(f"   - {host}: {rm} (unlink + clear)")
        rm_count += len(rm)
        if not DRY:
            call("host.massremove", {"hostids": [h["hostid"]],
                                     "templateids_clear": [tid[t] for t in rm]})

    print(f">> Resultado: +{add_count} link(s), -{rm_count} unlink(s)." +
          (" (DRY-RUN)" if DRY else ""))


if __name__ == "__main__":
    main()
