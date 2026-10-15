"""
Wrapper que lê credenciais do config.toml do MCP e do .env local,
depois chama o migrate.py sem expor tokens na linha de comando.

Uso: python run_migrate.py
"""
import subprocess
import sys
import os
import re
from pathlib import Path

HERE = Path(__file__).parent

# --- Ler URL e token do config.toml do MCP (somente leitura na produção) ---
CONFIG_TOML = Path(r"C:\Users\vinicius.galcez\OneDrive - Capricórnio Têxtil S.A\Script_Capri\Zabbix_Observality\zabbix-mcp-initmax\config.toml")

def parse_toml_simple(path: Path) -> dict:
    """Parser mínimo para extrair url do [zabbix.*] e token do env."""
    result = {}
    section = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        m = re.match(r'^\[(.+)\]$', line)
        if m:
            section = m.group(1)
            continue
        kv = re.match(r'^(\w+)\s*=\s*"?([^"#]+)"?', line)
        if kv and section:
            result.setdefault(section, {})[kv.group(1).strip()] = kv.group(2).strip()
    return result

toml = parse_toml_simple(CONFIG_TOML)
zabbix_section = next((v for k, v in toml.items() if k.startswith("zabbix.")), {})
prod_url = zabbix_section.get("url", "").rstrip("/")

# Token vem do .mcp.json via env var ZABBIX_TOKEN (já injetado quando o MCP inicia)
mcp_json = Path(r"C:\Users\vinicius.galcez\OneDrive - Capricórnio Têxtil S.A\Script_Capri\Zabbix_Observality\.mcp.json")
import json as _json
mcp_cfg = _json.loads(mcp_json.read_text(encoding="utf-8"))
prod_token = mcp_cfg.get("mcpServers", {}).get("zabbix", {}).get("env", {}).get("ZABBIX_TOKEN", "")

# --- Parâmetros locais ---
local_url  = "http://localhost:8090"
local_user = "Admin"
local_pass = "zabbix"
export_dir = str(HERE / "export")

if not prod_url or not prod_token:
    print("ERRO: não foi possível ler URL ou token da produção.")
    sys.exit(1)

print(f"Produção: {prod_url}")
print(f"Local:    {local_url}")
print(f"Export:   {export_dir}")
print()

# Injetar via env, não via argumento de linha de comando
env = os.environ.copy()
env["PROD_URL"]    = prod_url
env["PROD_TOKEN"]  = prod_token
env["LOCAL_URL"]   = local_url
env["LOCAL_USER"]  = local_user
env["LOCAL_PASS"]  = local_pass

python = sys.executable
migrate = str(HERE / "migrate.py")

result = subprocess.run(
    [python, migrate, "--export-dir", export_dir, "--batch-size", "15"],
    env=env,
)
sys.exit(result.returncode)
