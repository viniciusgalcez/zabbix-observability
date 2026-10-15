"""
Migração automatizada: Produção → Zabbix 8.0 local (POC)

Uso:
    python migrate.py --prod-url https://SEU_ZABBIX_PROD --prod-token SEU_TOKEN
                      --local-url http://localhost:8090
                      [--local-user Admin --local-pass zabbix]
                      [--export-dir ./export]
                      [--skip-templates] [--skip-dashboards]

O script:
  1. Autentica em produção com token de API (somente leitura)
  2. Exporta templates (XML) e dashboards (JSON) da produção
  3. Autentica no Zabbix local com usuário/senha
  4. Importa templates (com updateExisting=true para reaproveitar)
  5. Recria dashboards adaptados para o host 'Zabbix server' local
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

def _load_dotenv(path: Path):
    """Carrega variáveis de um arquivo .env simples (sem dependência de python-dotenv)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# ---------------------------------------------------------------------------
# Zabbix API client
# ---------------------------------------------------------------------------

class ZabbixAPI:
    def __init__(self, url: str, verify_ssl: bool = False):
        self.url = url.rstrip("/") + "/api_jsonrpc.php"
        self.verify = verify_ssl
        self.auth = None
        self._use_bearer = False  # True para Zabbix >= 6.4
        self._id = 1

    def _call(self, method: str, params: dict) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._id,
        }
        headers = {"Content-Type": "application/json"}
        if self.auth and method != "apiinfo.version":
            if self._use_bearer:
                headers["Authorization"] = f"Bearer {self.auth}"
            else:
                payload["auth"] = self.auth
        self._id += 1
        r = requests.post(self.url, json=payload, headers=headers,
                          verify=self.verify, timeout=30)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"Zabbix API error [{method}]: {data['error']}")
        return data["result"]

    def login_token(self, token: str):
        self.auth = token
        # Detecta versão para escolher o método de autenticação
        ver = self.version()
        major, minor = (int(x) for x in ver.split(".")[:2])
        self._use_bearer = (major > 6) or (major == 6 and minor >= 4)

    def login_user(self, user: str, password: str):
        # Detecta versão primeiro (sem auth)
        ver = self.version()
        major, minor = (int(x) for x in ver.split(".")[:2])
        self._use_bearer = (major > 6) or (major == 6 and minor >= 4)
        self.auth = self._call("user.login", {"username": user, "password": password})

    def version(self) -> str:
        return self._call("apiinfo.version", {})

    # --- Templates ---

    def template_list(self) -> list:
        return self._call("template.get", {
            "output": ["templateid", "host", "name"],
            "sortfield": "name",
        })

    def template_export_xml(self, template_ids: list) -> str:
        return self._call("configuration.export", {
            "format": "xml",
            "prettyprint": True,
            "options": {"templates": template_ids},
        })

    def host_list(self) -> list:
        return self._call("host.get", {
            "output": ["hostid", "host", "name", "status"],
            "sortfield": "host",
        })

    def host_export_xml(self, host_ids: list) -> str:
        return self._call("configuration.export", {
            "format": "xml",
            "prettyprint": True,
            "options": {"hosts": host_ids},
        })

    def host_import_xml(self, xml: str) -> bool:
        return self._call("configuration.import", {
            "format": "xml",
            "source": xml,
            "rules": {
                "hosts": {"createMissing": True, "updateExisting": True},
                "items": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
                "triggers": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
                "graphs": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
                "discoveryRules": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
                "httptests": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
                "templateLinkage": {"createMissing": True, "deleteMissing": False},
                "valueMaps": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
            },
        })

    def hostgroup_list_all(self) -> list:
        return self._call("hostgroup.get", {
            "output": ["groupid", "name"],
            "sortfield": "name",
        })

    def template_import_xml(self, xml: str) -> bool:
        return self._call("configuration.import", {
            "format": "xml",
            "source": xml,
            "rules": {
                "templates": {"createMissing": True, "updateExisting": True},
                "items": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
                "triggers": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
                "graphs": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
                "discoveryRules": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
                "httptests": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
                "templateDashboards": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
                "templateLinkage": {"createMissing": True, "deleteMissing": False},
                "valueMaps": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
            },
        })

    # --- Dashboards ---

    def dashboard_list(self) -> list:
        return self._call("dashboard.get", {
            "output": ["dashboardid", "name", "display_period", "auto_start"],
        })

    def dashboard_get(self, dashboard_id: str) -> dict:
        result = self._call("dashboard.get", {
            "dashboardids": [dashboard_id],
            "output": "extend",
            "selectPages": "extend",
        })
        return result[0] if result else {}

    def dashboard_create(self, payload: dict) -> str:
        result = self._call("dashboard.create", payload)
        return result.get("dashboardids", ["?"])[0]

    # --- Hostgroups ---

    def hostgroup_list(self) -> list:
        return self._call("hostgroup.get", {
            "output": ["groupid", "name"],
            "sortfield": "name",
        })

    def hostgroup_create_if_missing(self, name: str) -> str:
        existing = self._call("hostgroup.get", {
            "output": ["groupid"],
            "filter": {"name": [name]},
        })
        if existing:
            return existing[0]["groupid"]
        result = self._call("hostgroup.create", {"name": name})
        return result["groupids"][0]


# ---------------------------------------------------------------------------
# Migration helpers
# ---------------------------------------------------------------------------

def export_templates(prod: ZabbixAPI, export_dir: Path, batch_size: int = 20) -> list[Path]:
    print("\n[1/3] Listando templates da produção...")
    templates = prod.template_list()
    print(f"      {len(templates)} templates encontrados.")

    export_dir.mkdir(parents=True, exist_ok=True)
    files = []
    batches = [templates[i:i+batch_size] for i in range(0, len(templates), batch_size)]

    for idx, batch in enumerate(batches, 1):
        ids = [t["templateid"] for t in batch]
        names = [t["name"] for t in batch]
        print(f"      Exportando lote {idx}/{len(batches)}: {', '.join(names[:3])}{'...' if len(names)>3 else ''}")
        try:
            xml = prod.template_export_xml(ids)
            out = export_dir / f"templates_batch_{idx:03d}.xml"
            out.write_text(xml, encoding="utf-8")
            files.append(out)
        except Exception as e:
            print(f"      [AVISO] Lote {idx} falhou: {e}")
        time.sleep(0.2)

    print(f"      {len(files)} arquivo(s) XML salvos em {export_dir}/")
    return files


REQUIRED_TEMPLATE_GROUPS = [
    "Templates", "Templates/Applications", "Templates/Databases",
    "Templates/Modules", "Templates/Network devices", "Templates/Operating systems",
    "Templates/Server hardware", "Templates/Virtualization",
    "Templates/Roles", "Templates/Impressoras", "My Templates",
    "HyperV VM", "Windows", "Templates/Operating Systems",
]

def ensure_template_groups(local: ZabbixAPI):
    for name in REQUIRED_TEMPLATE_GROUPS:
        existing = local._call("templategroup.get", {
            "output": ["groupid"], "filter": {"name": [name]}
        })
        if not existing:
            try:
                local._call("templategroup.create", {"name": name})
            except Exception:
                pass  # pode já existir por corrida


def import_templates(local: ZabbixAPI, xml_files: list[Path]):
    print("\n[2/3] Importando templates no Zabbix local...")
    ensure_template_groups(local)
    ok = fail = 0
    failed = []
    for f in xml_files:
        try:
            local.template_import_xml(f.read_text(encoding="utf-8"))
            ok += 1
            print(f"      ✓ {f.name}")
        except Exception as e:
            failed.append(f)
            print(f"      ✗ {f.name}: {e}")
        time.sleep(0.1)
    # Segunda tentativa: strip de <dependencies> para resolver dependências cruzadas de triggers
    if failed:
        print(f"      Re-tentando {len(failed)} lote(s) sem dependências de trigger...")
        still_failed = []
        for f in failed:
            xml = f.read_text(encoding="utf-8")
            xml_no_deps = re.sub(r"<dependencies>.*?</dependencies>", "", xml, flags=re.DOTALL)
            try:
                local.template_import_xml(xml_no_deps)
                ok += 1
                print(f"      ✓ {f.name} (retry sem dependencies OK)")
            except Exception as e:
                still_failed.append(f)
                print(f"      ✗ {f.name} (retry1): {e}")
            time.sleep(0.1)
        failed = still_failed

    # Terceira tentativa: strip de dependencies + triggers (incompatibilidade 7→8)
    if failed:
        print(f"      Re-tentando {len(failed)} lote(s) sem triggers...")
        for f in failed:
            xml = f.read_text(encoding="utf-8")
            xml_clean = re.sub(r"<dependencies>.*?</dependencies>", "", xml, flags=re.DOTALL)
            xml_clean = re.sub(r"<triggers>.*?</triggers>", "", xml_clean, flags=re.DOTALL)
            try:
                local.template_import_xml(xml_clean)
                ok += 1
                print(f"      ✓ {f.name} (retry sem triggers OK)")
            except Exception as e:
                fail += 1
                print(f"      ✗ {f.name} (retry2): {e}")
            time.sleep(0.1)

    print(f"      Resultado: {ok} importados, {fail} com erro.")


def export_dashboards(prod: ZabbixAPI, export_dir: Path) -> Path:
    print("\n[2b] Exportando dashboards da produção...")
    dashboards = prod.dashboard_list()
    print(f"      {len(dashboards)} dashboards encontrados.")

    full = []
    for d in dashboards:
        try:
            detail = prod.dashboard_get(d["dashboardid"])
            full.append(detail)
        except Exception as e:
            print(f"      [AVISO] Dashboard {d['name']}: {e}")
        time.sleep(0.1)

    out = export_dir / "dashboards.json"
    out.write_text(json.dumps(full, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"      Salvo em {out}")
    return out


def export_hosts(prod: ZabbixAPI, export_dir: Path, batch_size: int = 10) -> list[Path]:
    print("\n[3b] Exportando hosts da produção...")
    hosts = prod.host_list()
    print(f"      {len(hosts)} hosts encontrados.")

    export_dir.mkdir(parents=True, exist_ok=True)
    files = []
    batches = [hosts[i:i+batch_size] for i in range(0, len(hosts), batch_size)]

    for idx, batch in enumerate(batches, 1):
        ids = [h["hostid"] for h in batch]
        names = [h["host"] for h in batch]
        print(f"      Lote {idx}/{len(batches)}: {', '.join(names[:3])}{'...' if len(names)>3 else ''}")
        try:
            xml = prod.host_export_xml(ids)
            out = export_dir / f"hosts_batch_{idx:03d}.xml"
            out.write_text(xml, encoding="utf-8")
            files.append(out)
        except Exception as e:
            print(f"      [AVISO] Lote {idx} falhou: {e}")
        time.sleep(0.2)

    print(f"      {len(files)} arquivo(s) XML de hosts salvos.")
    return files


def ensure_host_groups(prod: ZabbixAPI, local: ZabbixAPI):
    """Garante que todos os host groups da produção existam no local."""
    prod_groups = prod.hostgroup_list_all()
    for g in prod_groups:
        existing = local._call("hostgroup.get", {
            "output": ["groupid"], "filter": {"name": [g["name"]]}
        })
        if not existing:
            try:
                local._call("hostgroup.create", {"name": g["name"]})
            except Exception:
                pass


def import_hosts(local: ZabbixAPI, xml_files: list[Path]):
    print("\n[4/4] Importando hosts no Zabbix local...")
    ok = fail = 0
    failed = []
    for f in xml_files:
        try:
            local.host_import_xml(f.read_text(encoding="utf-8"))
            ok += 1
            print(f"      ✓ {f.name}")
        except Exception as e:
            failed.append(f)
            print(f"      ✗ {f.name}: {e}")
        time.sleep(0.1)
    # Retry 1: strip proxy + forçar monitoramento direto pelo servidor
    if failed:
        print(f"      Re-tentando {len(failed)} lote(s) sem proxies...")
        still_failed = []
        for f in failed:
            xml = f.read_text(encoding="utf-8")
            xml_clean = re.sub(r"<proxy>.*?</proxy>", "", xml, flags=re.DOTALL)
            xml_clean = xml_clean.replace("<monitored_by>PROXY</monitored_by>", "<monitored_by>SERVER</monitored_by>")
            try:
                local.host_import_xml(xml_clean)
                ok += 1
                print(f"      ✓ {f.name} (retry sem proxy OK)")
            except Exception as e:
                still_failed.append(f)
                print(f"      ✗ {f.name} (retry1): {e}")
            time.sleep(0.1)
        failed = still_failed

    # Retry 2: strip proxy + templates + graphs + triggers (importa estrutura mínima)
    if failed:
        print(f"      Re-tentando {len(failed)} lote(s) sem proxies, templates, grafos e triggers...")
        for f in failed:
            xml = f.read_text(encoding="utf-8")
            xml_clean = re.sub(r"<proxy>.*?</proxy>", "", xml, flags=re.DOTALL)
            xml_clean = xml_clean.replace("<monitored_by>PROXY</monitored_by>", "<monitored_by>SERVER</monitored_by>")
            xml_clean = re.sub(r"<templates>.*?</templates>", "", xml_clean, flags=re.DOTALL)
            xml_clean = re.sub(r"<graphs>.*?</graphs>", "", xml_clean, flags=re.DOTALL)
            xml_clean = re.sub(r"<triggers>.*?</triggers>", "", xml_clean, flags=re.DOTALL)
            try:
                local.host_import_xml(xml_clean)
                ok += 1
                print(f"      ✓ {f.name} (retry sem proxy+templates+grafos OK)")
            except Exception as e:
                fail += 1
                print(f"      ✗ {f.name} (retry2): {e}")
            time.sleep(0.1)

    print(f"      Resultado: {ok} importados, {fail} com erro.")


def import_dashboards(local: ZabbixAPI, dashboards_file: Path):
    print("\n[3/3] Importando dashboards no Zabbix local...")
    dashboards = json.loads(dashboards_file.read_text(encoding="utf-8"))

    # Campos que não devem ir no create
    strip_fields = {"dashboardid", "userid", "private", "editable", "uuid"}

    ok = fail = 0
    for d in dashboards:
        payload = {k: v for k, v in d.items() if k not in strip_fields}
        payload["name"] = f"[POC] {payload['name']}"
        payload.setdefault("display_period", 30)
        payload.setdefault("auto_start", 1)

        # Limpar IDs internos de páginas e referências externas
        # Tipos que referenciam objetos da produção (host, grupo, item, mapa, grafo...)
        EXTERNAL_REF_TYPES = {"2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"}
        for page in payload.get("pages", []):
            page.pop("dashboard_pageid", None)
            for widget in page.get("widgets", []):
                widget.pop("widgetid", None)
                # Remove fields de referência externa (IDs inválidos no ambiente local)
                widget["fields"] = [
                    f for f in widget.get("fields", [])
                    if f.get("type") not in EXTERNAL_REF_TYPES
                ]

        try:
            # Deletar se já existir com o mesmo nome (idempotência)
            existing = local._call("dashboard.get", {
                "output": ["dashboardid"], "filter": {"name": [payload["name"]]}
            })
            if existing:
                local._call("dashboard.delete", [existing[0]["dashboardid"]])
            new_id = local.dashboard_create(payload)
            ok += 1
            print(f"      ✓ {payload['name']} → id {new_id}")
        except Exception as e:
            fail += 1
            print(f"      ✗ {d.get('name', '?')}: {e}")
        time.sleep(0.1)

    print(f"      Resultado: {ok} criados, {fail} com erro.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Carregar .env do mesmo diretório do script, se existir
    _load_dotenv(Path(__file__).parent / ".env")

    ap = argparse.ArgumentParser(description="Migra templates e dashboards para a POC Zabbix 8.0 local.")
    ap.add_argument("--prod-url",   default=os.environ.get("PROD_URL"),   help="URL da produção")
    ap.add_argument("--prod-token", default=os.environ.get("PROD_TOKEN"), help="Token de API da produção")
    ap.add_argument("--local-url",  default=os.environ.get("LOCAL_URL",  "http://localhost:8090"))
    ap.add_argument("--local-user", default=os.environ.get("LOCAL_USER", "Admin"))
    ap.add_argument("--local-pass", default=os.environ.get("LOCAL_PASS", "zabbix"))
    ap.add_argument("--export-dir",    default="./export")
    ap.add_argument("--skip-templates",   action="store_true")
    ap.add_argument("--skip-dashboards",  action="store_true")
    ap.add_argument("--skip-hosts",       action="store_true")
    ap.add_argument("--batch-size",    type=int, default=20, help="Templates por lote de exportação")
    args = ap.parse_args()

    if not args.prod_url or not args.prod_token:
        ap.error("Defina PROD_URL e PROD_TOKEN no arquivo .env ou via argumentos.")

    export_dir = Path(args.export_dir)

    # Conectar produção (token)
    print(f"Conectando à produção: {args.prod_url}")
    prod = ZabbixAPI(args.prod_url)
    prod.login_token(args.prod_token)
    prod_ver = prod.version()
    print(f"  Produção: Zabbix {prod_ver}")

    # Conectar local (usuário/senha)
    print(f"Conectando ao local: {args.local_url}")
    local = ZabbixAPI(args.local_url)
    local.login_user(args.local_user, args.local_pass)
    local_ver = local.version()
    print(f"  Local: Zabbix {local_ver}")

    # Templates
    if not args.skip_templates:
        xml_files = export_templates(prod, export_dir, args.batch_size)
        import_templates(local, xml_files)
    else:
        # Importar arquivos já exportados se existirem
        xml_files = sorted(export_dir.glob("templates_batch_*.xml"))
        if xml_files:
            import_templates(local, xml_files)

    # Dashboards
    if not args.skip_dashboards:
        db_file = export_dashboards(prod, export_dir)
        import_dashboards(local, db_file)
    else:
        db_file = export_dir / "dashboards.json"
        if db_file.exists():
            import_dashboards(local, db_file)

    # Hosts
    if not args.skip_hosts:
        ensure_host_groups(prod, local)
        host_files = export_hosts(prod, export_dir, batch_size=10)
        import_hosts(local, host_files)
    else:
        host_files = sorted(export_dir.glob("hosts_batch_*.xml"))
        if host_files:
            import_hosts(local, host_files)

    print("\n✅ Migração concluída!")
    print(f"   Acesse: {args.local_url} (Admin / {args.local_pass})")


if __name__ == "__main__":
    main()
