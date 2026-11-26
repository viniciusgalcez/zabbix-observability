# Contexto para correção — Gantt de indisponibilidade (Deps / apps compostas)

**Para:** sistema de relatórios (Gantt) que consome dados do Zabbix  
**De:** validação observabilidade Zabbix (Deps API + Banco)  
**Data:** 2026-11-26  
**Objetivo:** o total de indisponibilidade da aplicação deve ser a **união** dos intervalos dos componentes, nunca a soma das barras.

---

## Problema

No Gantt aparecem barras separadas, por exemplo:

- **Deps API** indisponível por **1 hora** (ex.: 10:00–11:00)
- **Deps Banco** cai aos **40 min** dessa janela e fica **1 hora** fora (ex.: 10:40–11:40)

Há **20 minutos** de sobreposição (10:40–11:00).

| Cálculo | Resultado | Correto? |
|---------|-----------|----------|
| Soma das barras (1h + 1h) | **2h** | Não — conta a sobreposição duas vezes |
| União dos intervalos | **1h40** | Sim — impacto real na aplicação |
| Só a barra da API | **1h** | Não — ignora os 40 min em que só o banco ficou fora depois |

**Regra de negócio:** enquanto a aplicação já está indisponível por um componente, o tempo sobreposto de outro componente **não** se soma de novo. O tempo que um componente fica fora **depois** que o outro voltou **entra** no total.

---

## O que o Zabbix já faz (não reimplementar no motor de SLA)

No Zabbix Services/BSM:

- Serviço pai: **`Deps Produção`**
- Filhos: `Deps API`, `Deps Home`, `Deps Produção Banco`
- Pai com algorithm **Most critical of child services**
- Tag SLA **`slatier=critico` só no pai** (filhos sem essa tag)

O SLI/downtime do **pai** via API já é a união.

```http
POST /api_jsonrpc.php
method: sla.getsli
params: { "slaid": "<id do SLA Crítico>", "serviceids": ["<id Deps Produção>"] }
```

Campos úteis na resposta do período: `uptime`, `downtime`, `sli`.  
Para `Deps Produção`, `downtime` no exemplo acima deve ser **~1h40** (em segundos), não 2h.

Também é possível montar o Gantt pela timeline de status do serviço pai (`service.get` + status/alarms do pai): um único intervalo contínuo de problema = união visual.

---

## O que o sistema de relatórios deve fazer

### Correto (escolher uma abordagem)

**A — Preferencial (total oficial da app)**  
1. Buscar no Zabbix o serviço **pai** da aplicação (`Deps Produção`).  
2. Usar `downtime` / timeline do pai para o **total** e para a barra “Aplicação” (se existir).  
3. Barras dos filhos (API, Banco) podem continuar no Gantt só como **detalhe**; **não** somar as durações delas para o KPI.

**B — Se o Gantt só tem intervalos dos componentes**  
1. Coletar intervalos `[início, fim)` de cada componente.  
2. Calcular **união** (merge de overlapping/adjacentes).  
3. Total da app = soma das durações **depois** do merge.

Pseudocódigo:

```text
intervalos = [(api_start, api_end), (banco_start, banco_end), ...]
ordenar por início
merged = []
para cada [s, e] em intervalos:
  se merged vazio ou s > fim do último:
    appended
  senão:
    estender fim do último = max(fim, e)
total_segundos = soma (fim - início) de cada intervalo em merged
```

Exemplo numérico (epoch relativo):

- API:  `[0, 3600]`
- Banco:`[2400, 6000]`   // começa aos 40 min, dura 1h
- Soma bruta: 3600+3600 = **7200** (2h) ← errado
- União: `[0, 6000]` = **6000** (1h40) ← certo

### Errado (remover)

- `total = duração(API) + duração(Banco) + ...`
- `total = max(durações)` quando os intervalos **não** estão aninhados (no exemplo, max=1h esconde 40 min extras do banco)
- Média de SLIs dos filhos como “SLA da app”

---

## Escopo das aplicações (mesmo padrão)

Qualquer serviço **composto** no Zabbix com pai + filhos (App/API/Home + Banco), por exemplo:

- Deps Produção / Deps Homolog  
- Totvs, Portal de OS, Dimep, EAS Cozinha, GLPI, Lansweeper, Veeam Backup, etc.

Regra: **KPI de disponibilidade da aplicação = serviço pai (união)**. Componentes = detalhe do Gantt.

---

## Critérios de aceite

1. No cenário API 1h + Banco 1h com 20 min de overlap, o total do Gantt / KPI = **1h40** (± tolerância de clock).  
2. Não exibir “2h” como indisponibilidade da aplicação.  
3. Barras dos componentes podem coexistir; o total não é a soma delas.  
4. Preferir `sla.getsli` / timeline do **pai** como fonte do total quando disponível.  
5. Se um componente não tiver overlap (quedas disjuntas), a união soma os dois períodos inteiros (aí 1h + 1h = 2h é correto porque não há sobreposição).

---

## Referências neste repositório

- Validação: `reports/validacao-sla-sobreposicao-deps.md`
- Lib de união (Python): `automacao/sla_overlap_lib.py` (`union_intervals`, `union_duration`)
- Testes do cenário: `automacao/test_sla_overlap.py`
- Auditoria Zabbix: `automacao/audit_sla_overlap.py`
- Relatório SLI dos pais: `automacao/gen_sla_app_report.py`
- Fixture live: `backups/fixture_sla_critico_sli_live_20261126.json`

---

## Resumo em uma frase

**Fonte Zabbix ok; no Gantt, o total da app deve espelhar o downtime do serviço pai (união). Se hoje o relatório soma as barras dos filhos, essa é a correção a fazer no sistema de relatórios.**
