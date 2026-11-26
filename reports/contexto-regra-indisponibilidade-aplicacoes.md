# Contexto — regra de indisponibilidade de aplicações compostas

**Para:** sistema de relatórios / KPI de disponibilidade que consome dados do Zabbix  
**De:** validação observabilidade Zabbix (ex.: Deps API + Banco)  
**Data:** 2026-11-26  
**Objetivo:** documentar a regra de negócio. O total de indisponibilidade da **aplicação** é a **união** dos intervalos dos componentes, nunca a soma das durações.

*(Gantt, lista de incidentes, dashboard etc. são só formas de exibir; a regra é a mesma.)*

---

## Regra de negócio

Enquanto a aplicação já está indisponível por um componente, o tempo **sobreposto** de outro componente **não** se soma de novo. O tempo em que um componente fica fora **depois** que o outro voltou **entra** no total.

### Exemplo (Deps)

- **Deps API** fora por **1 hora** (ex.: 10:00–11:00)
- **Deps Banco** cai aos **40 min** e fica **1 hora** fora (ex.: 10:40–11:40)
- Sobreposição: **20 min** (10:40–11:00)

| Cálculo | Resultado | Correto? |
|---------|-----------|----------|
| Soma (1h + 1h) | **2h** | Não — conta a sobreposição duas vezes |
| União dos intervalos | **1h40** | Sim — impacto real na aplicação |
| Só a API | **1h** | Não — ignora os 40 min em que só o banco ficou fora depois |

---

## O que o Zabbix já faz

No Zabbix Services/BSM (apps compostas):

- Serviço **pai** (ex.: `Deps Produção`) com algorithm **Most critical of child services**
- Filhos = componentes (API, Home, Banco, …)
- Tag SLA **`slatier=critico` / `padrao` só no pai**

O SLI/`downtime` do **pai** via API já é a união:

```text
method: sla.getsli
params: { "slaid": "<SLA>", "serviceids": ["<id do serviço pai>"] }
```

Campos: `uptime`, `downtime`, `sli`. No exemplo, `downtime` do pai ≈ **1h40**, não 2h.

**Não** é preciso reimplementar essa lógica no motor de SLA do Zabbix.

---

## O que o sistema de relatórios deve fazer

### Preferencial

1. Usar o serviço **pai** da aplicação no Zabbix.
2. KPI / total de indisponibilidade = `downtime` (ou timeline) desse pai (`sla.getsli`).
3. Detalhe por componente (API, banco…) pode aparecer, mas **não** entra na soma do KPI da app.

### Se o relatório só tem intervalos dos componentes

1. Coletar `[início, fim)` de cada componente.
2. Fazer **união** (merge de overlapping/adjacentes).
3. Total da app = duração dessa união.

```text
ordenar intervalos por início
merged = []
para cada [s, e]:
  se vazio ou s > fim_do_último → append
  senão → fim_do_último = max(fim_do_último, e)
total = soma das durações de merged
```

Exemplo numérico:

- API `[0, 3600]`, Banco `[2400, 6000]`
- Soma bruta = **7200** (2h) ← errado  
- União = **6000** (1h40) ← certo  

### Errado

- `total = duração(API) + duração(Banco) + …`
- `total = max(durações)` quando as janelas não estão aninhadas
- Média dos SLIs dos filhos como “SLA da app”

---

## Escopo

Mesma regra para qualquer app composta no Zabbix (pai + filhos), por exemplo: Deps Produção/Homolog, Totvs, Portal de OS, Dimep, EAS Cozinha, GLPI, Lansweeper, Veeam Backup, etc.

**KPI de disponibilidade da aplicação = serviço pai (união).** Componentes = detalhe.

---

## Critérios de aceite

1. No cenário do exemplo, indisponibilidade da app = **1h40** (± clock).  
2. Não reportar **2h** como downtime da aplicação.  
3. Fonte preferida do total: `sla.getsli` / timeline do **pai**.  
4. Quedas **sem** overlap: a união soma os períodos inteiros (aí 1h + 1h = 2h é correto).

---

## Referências neste repositório

- `reports/validacao-sla-sobreposicao-deps.md`
- `automacao/sla_overlap_lib.py` (`union_intervals`, `union_duration`)
- `automacao/test_sla_overlap.py`
- `automacao/audit_sla_overlap.py`
- `automacao/gen_sla_app_report.py`
- `backups/fixture_sla_critico_sli_live_20261126.json`

---

## Resumo

**Indisponibilidade da aplicação = união dos componentes.** O Zabbix já entrega isso no serviço pai; o relatório deve usar esse valor (ou calcular a união), nunca somar as durações sobrepostas.
