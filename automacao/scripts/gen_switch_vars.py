#!/usr/bin/env python3
"""
Gera vars/switches_excel.yml a partir de docs/Sws_Capricornio.xlsx.
Execute sempre que atualizar a planilha:
    python3 scripts/gen_switch_vars.py
"""
import json
import sys
from pathlib import Path

try:
    import openpyxl
except ImportError:
    print("Instale: pip3 install openpyxl", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).parent.parent
XLSX = ROOT / "docs" / "Sws_Capricornio.xlsx"
OUT  = ROOT / "vars" / "switches_excel.yml"

SITE_MAP = {"16": "SCL", "17": "SPO", "18": "BGP"}

wb = openpyxl.load_workbook(XLSX)
ws = wb.active

sw_map = {}
for row in ws.iter_rows(min_row=3, values_only=True):
    nome   = (row[0] or "").strip()
    ip     = (row[1] or "").strip()
    modelo = (row[2] or "").strip().lstrip("\t")
    local  = (row[3] or "").strip()
    if not ip or not nome or nome == "NOME":
        continue
    base_nome = nome.split("(")[0].strip()
    oct2 = ip.split(".")[1]
    site = SITE_MAP.get(oct2, "")
    if ip not in sw_map:
        sw_map[ip] = {"name": base_nome, "model": modelo, "location": local, "site": site}

OUT.parent.mkdir(exist_ok=True)
with open(OUT, "w") as f:
    f.write("---\n# Gerado automaticamente por scripts/gen_switch_vars.py\n")
    f.write("# NÃO EDITE MANUALMENTE — edite o Excel e regenere\n")
    f.write("switch_inventory:\n")
    for ip, data in sorted(sw_map.items()):
        f.write(f"  '{ip}':\n")
        for k, v in data.items():
            f.write(f"    {k}: '{v}'\n")

print(f"Gerado: {OUT} ({len(sw_map)} switches únicos)")
