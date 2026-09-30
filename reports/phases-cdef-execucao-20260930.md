# Fases C (fecho), D, E e F — execução 30/09/2026

## Fase C residual — protótipos LLD

Template `FortiGate by SNMP` (`10604`):

| Protótipo | ID | Tags adicionadas |
| --- | --- | --- |
| High packets loss | 23665 | `scope=performance`, `class=network`, `component=sd-wan` |
| Health check state is dead | 23666 | `scope=availability`, `class=network`, `component=sd-wan` |

`depends-on={#IFNAME}` preservado. Backup: `backups/phase_c_export_template_10604_before_scope_tags_20260930.json`.

Limitação: instâncias LLD já descobertas só herdam as novas tags após rediscovery/atualização do LLD. As abertas hoje ainda podem estar sem `scope`.

## Fase D — Teams só com autorização explícita

### Ação 22

- Antes: `A or B` (`notify=teams` **ou** severidade ≥ High)
- Depois: **somente** `A` (`notify=teams`)
- `esc_period=5m` e `pause_symptoms=1` mantidos

Motivo técnico: este Zabbix rejeita operador “tag does not exist” (25/13) na ação; a alternativa segura foi exigir `notify=teams`.

Backup: `backups/phase_d_backup_action_22_full_before_filter_20260930.json`.

### Causas físicas

As 11 saídas ISP continuam com `notify=teams` (confirmado).

### Agregados VPN

Removido `notify=teams` dos 12 agregados (`55133`…`55154`); permanece `telegram`.

## Fase E — piloto SPO Vivo sem `close_new`

| Correlação | Operação | Status após piloto |
| --- | --- | --- |
| 16 | close_new | **desabilitada** |
| 45 | close_new | **desabilitada** |
| 17 | close_old | ativa |
| 46 | close_old | ativa |

Efeito esperado: sintomas de `spo.vivo.isp1` deixam de ser fechados/reabertos a cada coleta; ficam abertos uma vez, ranqueados sob a causa, **sem** Teams (não têm `notify=teams`).

Backup: `backups/phase_e_backup_spo_vivo_correlations_before_pilot_20260930.json`.

Observação 7 dias: se não houver tempestade nem falso silêncio, expandir o mesmo padrão às outras ondas (SCL, BGP, …).

## Fase F — governança

### Regras operacionais

1. Circuito novo entra primeiro em `reports/mapa-links-alertas-canonico-20260930.csv` com `link-id`.
2. Causa física: `notify=teams` + `link-id` + `link-cause` (legado até migrar correlações).
3. Sintoma/agregado: **sem** `notify=teams`; `depends-on` apontando o circuito.
4. Perda de pacotes: `scope=performance` (protótipo).
5. Correlação `close_new`: não reativar em SPO Vivo sem evidência; preferir ranking (`scripts/link_cause_rank_worker.py`) no servidor.
6. Ranker: dry-run → apply; nunca na estação do usuário como processo contínuo.
7. Mudanças: backup em `backups/` antes de cada update.

### Cadência

| Quando | O quê |
| --- | --- |
| Diário (enquanto SPO Vivo aberto) | Conferir se sintomas novos ficaram ranqueados e se Teams só emitiu a causa |
| Semanal (1º mês) | Revisar ondas, flapping, problemas >24h, envios Teams |
| Mensal | Atualizar matriz canônica; incluir firewall/operadora nova |

### Rollback rápido

- Ação 22: restaurar filtro de `backups/phase_d_backup_action_22_full_before_filter_20260930.json`
- Correlações 16/45: `correlation.update` `status=0`
- Protótipos: reimportar `backups/phase_c_export_template_10604_before_scope_tags_20260930.json` se necessário

## Aceite

- [x] D: Teams exige `notify=teams`
- [x] D: agregados sem Teams
- [x] C: protótipos loss/dead com `scope`/`class`/`component`
- [x] E: `close_new` SPO Vivo desabilitado (16/45)
- [x] F: regras e cadência documentadas
- [ ] E ondas 2–5 (SCL/BGP/…) — pendente após observação de 7 dias
- [ ] Dashboard de qualidade de correlação — pendente (Fase F visual)

## Próximo

Observar 7 dias o piloto SPO Vivo. Se estável, repetir desligamento de `close_new` em SCL (`11`/`35`) na onda 2.
