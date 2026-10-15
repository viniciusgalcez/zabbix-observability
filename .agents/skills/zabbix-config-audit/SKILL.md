---
name: zabbix-config-audit
description: >-
  Audita o Zabbix da Capricórnio (configuração + saúde de coleta) contra a
  documentação oficial Zabbix 7 e as decisões locais: itens/LLD unsupported,
  triggers Unknown, proxies, SNMP, hosts, correlação de links, tags/SLA,
  ações/Teams, discovery e ruído de alertas. Use quando o usuário pedir
  auditoria, revisão, saúde do ambiente, erros de coleta, itens não suportados,
  triggers unknown, LLD quebrada, tendência/capacidade/SLA, ou "o que precisa
  corrigir antes de virar dor de cabeça". Não aplica mudanças — para corrigir,
  use zabbix-senior-analyst.
---

# Auditoria Zabbix Capricórnio

Consultor de observabilidade: **somente leitura**. Diagnóstico priorizado com
evidência da API — sem inventar números e sem aplicar `create`/`update`/`delete`.

## Esta skill vs mudança

| Pedido | Skill |
| --- | --- |
| Auditar / revisar / saúde / coleta / ruído / SLA / "o que está errado" | **Esta** → relatório `.md` |
| Corrigir / aplicar / ranquear / alterar trigger | `zabbix-senior-analyst` (backup → mudança → validação) |

Se o usuário pedir "corrige isso" no meio da auditoria, **pare** e mude para
`zabbix-senior-analyst`.

## Referências (ler sob demanda)

1. Sempre: [best-practices.md](references/best-practices.md) — oficiais + decisões Capri
2. Checklist API: [audit-checklist.md](references/audit-checklist.md)
3. Coleta (P0): [collection-health.md](references/collection-health.md)
4. Dados/tendência/SLA: [data-analysis-patterns.md](references/data-analysis-patterns.md)
5. Modelo de relatório: [report-template.md](references/report-template.md)
6. Conexão MCP: [../zabbix-senior-analyst/references/environment.md](../zabbix-senior-analyst/references/environment.md)

Docs oficiais âncora (Zabbix 7.x): unsupported items / internal events, triggers
Unknown, LLD guidelines, network device templates (SNMP OID + filtros).

## Fluxo obrigatório

```
Progresso:
- [ ] 1. Escopo definido
- [ ] 2. Convenções lidas (best-practices)
- [ ] 3. Módulo P0 — saúde de coleta executado
- [ ] 4. Módulos do escopo executados
- [ ] 5. Achados classificados com IDs
- [ ] 6. Relatório em reports/auditoria-zabbix-YYYYMMDD.md
```

### 1. Escopo

Se o usuário não especificar, pergunte ou assuma **full** e declare isso no
relatório. Escopos válidos:

| Escopo | Módulos |
| --- | --- |
| `full` | P0 + todos os P1 |
| `coleta` / `collection` | Só P0 |
| `firewalls` / `links` | P0 (hosts FW) + correlação + problemas FW |
| `rede` | P0 + SNMP + discovery de rede + switches |
| `servidores` | P0 + agent + LLD Hyper-V/disk + unsupported |
| `web` / `ssl` | httptest + certs + hosts Monitoramento Web |
| `dados` | Só data-analysis-patterns (pergunta pontual) |

### 2. Execução via API

- Use MCP `zabbix` / `scripts/dashboard_mcp_session.py` + JSON em `zabbix-requests/`.
- Salve evidências em `backups/` com sufixo de data (`YYYYMMDD`).
- **Paginação:** `limit` + lotes por `hostids` (40–50). Nunca confie num único
  `limit=1000` como total — confirme com `countOutput` quando existir.
- Em Zabbix 7, `proxy.get` usa `name` (não `host`). Confirme campos com
  `zabbix_api_docs` se a chamada falhar.
- Separe **enabled** (`status=0`) de **disabled** (`status=1`): unsupported
  desabilitado em massa pode ser limpeza intencional — reporte como Informativo
  com contagem, não como Crítico.

### 3. Classificação de achados

| Nível | Critério |
| --- | --- |
| **Crítico** | Coleta/detecção quebrada agora, ou causa raiz de alerta sem vínculo, ou gap que esconde indisponibilidade |
| **Atenção** | Dívida que vira dor em semanas (LLD timeout, SNMP v1/v2 em equipamento v3-capable, fila antiga, proxy drift) |
| **Informativo** | Observação / exceção conhecida / disabled legado |

Todo achado cita **objeto** (`host` + `itemid`/`triggerid`/`eventid`/`correlationid`)
+ **evidência** (erro da API / contagem) + **por que importa**.

### 4. Relatório

Grave em `reports/auditoria-zabbix-YYYYMMDD.md` (ou sufixo `-coleta`, `-firewalls`
se escopo parcial). Siga [report-template.md](references/report-template.md).

No chat: 2–4 frases com o veredito + caminho do arquivo. Não despeje tabelas
gigantes no chat se o `.md` já as contém.

### 5. Próximos passos

Ordene por risco → esforço. Cada correção aponta explicitamente:
"aplicar via `zabbix-senior-analyst` com backup".

## Módulos

### P0 — Saúde de coleta (sempre em `full` e `coleta`)

Siga [collection-health.md](references/collection-health.md):

1. Itens enabled unsupported (`state=1`, `status=0`) — lista completa por host
2. LLD rules unsupported enabled
3. Triggers em Unknown (`state=1`, `status=0`) — contagem + top hosts/erros
4. Proxies (`lastaccess`, `state`, `version`, `compatibility`)
5. Interfaces `available=2` (agent/SNMP) + erros
6. Problemas de reachability (ICMP / agent / No SNMP data)
7. Cascata: unsupported → Unknown trigger (não reporte a trigger sem a causa do item)

### P1 — Configuração e governança

Execute conforme escopo; detalhes em [audit-checklist.md](references/audit-checklist.md):

- Hosts sem template (respeitar exceção Web)
- SNMP version (v3 preferido; UPS v2c OK)
- Network discovery + fila Em Classificação
- Correlação de links (status 16/45 piloto; roots vs symptoms FW)
- Tags `scope` dual capacity+availability
- Ações Teams (`notify=teams`, recovery, `pause_symptoms`, `esc_period`)
- Internal actions para unsupported/Unknown (doc oficial)
- httptest `verify_peer` / certificados
- Macros divergentes
- Fila de problems antigos (≥7d) sem ack

### P2 — Análise de dados (sob demanda)

[data-analysis-patterns.md](references/data-analysis-patterns.md): tendência,
ruído de eventos, `sla.getsli`.

## Anti-padrões

- Não recomendar "aumentar timeout em massa" para limpar unsupported
- Não recomendar correlacionar switch→AP (decisão local revertida)
- Não tratar hosts Web sem template como dívida automática
- Não marcar close_new 16/45 disabled como bug sem citar o piloto anti-storm
- Não inventar hosts/IDs que a API não devolveu
- Não aplicar correção nesta skill
