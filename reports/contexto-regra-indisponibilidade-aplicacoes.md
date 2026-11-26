# Contexto — regra de indisponibilidade de aplicações com vários fatores

**Para:** sistema de relatórios / KPI de disponibilidade que consome dados do Zabbix  
**De:** validação observabilidade Zabbix  
**Data:** 2026-11-26  
**Objetivo:** em aplicações com **vários fatores** de indisponibilidade (API, app, banco, web, home, etc.), o total da **aplicação** é a **união** dos intervalos — nunca a soma das durações dos fatores.

---

## Regra (vale para qualquer app multi-fator)

1. Cada fator (componente) pode gerar um intervalo de indisponibilidade.
2. Enquanto **qualquer** fator mantém a app fora, a app está indisponível.
3. Tempo em que dois ou mais fatores coincidem conta **uma vez**.
4. Tempo em que um fator continua fora depois dos outros voltarem **entra** no total.

```text
indisponibilidade_app = UNIÃO(intervalos dos fatores)
                     ≠ SOMA(duração de cada fator)
```

### Exemplo (Deps — 2 fatores)

- Fator API: 10:00–11:00 (1h)  
- Fator Banco: 10:40–11:40 (1h)  
- Overlap: 20 min  

| Cálculo | Resultado | Correto? |
|---------|-----------|----------|
| Soma dos fatores | **2h** | Não |
| União | **1h40** | Sim |
| Só um fator | **1h** | Não (perde o restante do outro) |

A mesma lógica escala para 3+ fatores (API + Home + Banco, App + Banco + dependência, etc.): merge de **todos** os intervalos.

---

## Onde aplicar no Capri (apps compostas no Zabbix)

Aplicações com **pai + filhos** (vários fatores). O KPI da app usa o **pai**; os filhos são os fatores.

| Aplicação (pai) | Fatores típicos (filhos) | SLA (tag no pai) |
|-----------------|--------------------------|------------------|
| Deps Produção | API, Home, Banco | `slatier=critico` |
| Deps Homolog | API, Home, Banco | `slatier=padrao` |
| Totvs | App, Banco | `slatier=critico` |
| Portal de OS | App, Banco | `slatier=padrao` |
| Dimep | App, Banco | (composto) |
| EAS Cozinha | App, Banco | (composto) |
| Veeam Backup | App, Banco | (composto) |
| GLPI / Lansweeper | Web, Banco (quando modelados como compostos) | conforme tag do pai |

Apps **folha** (um único serviço, sem filhos de disponibilidade) não precisam de união entre fatores — o próprio serviço já é o KPI.

**Padrão Zabbix já adotado:** pai com algorithm **Most critical of child services**; tag `slatier` **só no pai**.

---

## Fonte preferida no relatório

Para cada aplicação multi-fator:

1. Resolver o serviço **pai** no Zabbix.
2. KPI / downtime / SLI = resposta de `sla.getsli` (ou timeline de status) desse pai.
3. Fatores (filhos) podem aparecer como detalhe; **não** somar as durações deles no total da app.

```text
method: sla.getsli
params: { "slaid": "<SLA>", "serviceids": ["<id do pai>"] }
→ downtime / uptime / sli   // já é união
```

### Se o relatório monta o total só com eventos dos fatores

```text
intervalos = todos os [início, fim) de todos os fatores da app
merged = união (merge overlapping/adjacentes)
total_app = duração(merged)
```

Lib de referência neste repo: `automacao/sla_overlap_lib.py` (`union_intervals`, `union_duration`).

---

## Errado (evitar)

- `total = sum(duração de cada fator)`  
- `total = max(durações)` quando os fatores não estão aninhados  
- média dos SLIs dos filhos como “SLA da aplicação”  
- colocar `slatier` também nos filhos (faz o SLA nativo medir cada fator separado)

---

## Critérios de aceite

1. Para **toda** app composta (vários fatores), o KPI de indisponibilidade da app = união, não soma.  
2. Cenário Deps (API 1h + Banco 1h, 20 min overlap) → **1h40**.  
3. Com N fatores, overlap entre qualquer subconjunto conta uma vez.  
4. Quedas **sem** overlap entre fatores: a união soma os períodos inteiros (aí a “soma” coincide com a união).  
5. Fonte preferida: `sla.getsli` / timeline do **pai**.

---

## Referências

- `reports/validacao-sla-sobreposicao-deps.md`
- `automacao/sla_overlap_lib.py` / `test_sla_overlap.py`
- `automacao/audit_sla_overlap.py` (audita compostos; use sem `--service` para varrer os pais com `slatier`)
- `automacao/gen_sla_app_report.py`
- `backups/fixture_sla_critico_sli_live_20261126.json`

---

## Resumo

**Aplicações com vários fatores de indisponibilidade:** o relatório deve tratar a app como o serviço pai (união). Soma de fatores só serve para detalhe operacional, nunca como downtime oficial da aplicação.
