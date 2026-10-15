# Roadmap de correção — Auditoria Zabbix 01/10/2026

**Base:** `reports/auditoria-zabbix-20261001.md` (+ coleta / firewalls)  
**Regra:** cada fase aplica via skill `zabbix-senior-analyst` (backup → menor mudança → validação). Esta roadmap **não** autoriza mutação por si só — execute fase a fase com o responsável.

**Meta mensurável (re-auditoria P0):**

| Indicador | Hoje (pós-Fase 1) | Meta fase A–C | Meta 30 dias |
| --- | --- | --- | --- |
| Unsupported enabled | **0** (era 7) | 0–2 | 0 |
| LLD unsupported enabled | 20 | ≤8 | ≤3 |
| Triggers Unknown enabled | **90** (era 852) | ≤200 | ≤50 |
| FW roots órfãos com causa link ativa | recorrente | 0 após rank | 0 contínuo |
| ICMP down &gt;7d sem dono | **0** (era 1) | 0 | 0 |
| Problems-raiz ≥7d | 65 | ≤40 | ≤20 |
| Envios Teams indevidos (sintoma sob causa) | a medir (7.1) | 0 em piloto 48h | 0 contínuo |
| Classes críticas sem PROBLEM+OK no Teams | a medir (7.3/7.5) | 0 no piloto | 0 |

---

## Visão das fases

```
Fase 0  Contenção operacional (hoje–2 dias)
Fase 1  Coleta rápida — unsupported 7 + ICMP AP ✅ 2026-10-01
Fase 2  Correlação contínua (rank worker) ✅ parcial 2026-10-02
Fase 3  LLD crítica — CONCLUÍDA 2026-10-05 (bad enabled=0; 3D remediação API ok)
Fase 4  Cascata Unknown ✅ 2026-10-05 (834→90; TEC*=0)
Fase 5  Higiene (fila antiga, FW órfãos, web TLS, SNMP v3)
Fase 6  Governança (internal actions + re-auditoria)
Fase 7  Alertas Zabbix → Microsoft Teams (qualidade + cobertura)
```

---

## Fase 0 — Contenção (D0–D2)

**Objetivo:** parar o sangramento visual e de Teams enquanto a Vivo estiver down.

| # | Ação | Alvo | Critério de pronto |
| --- | --- | --- | --- |
| 0.1 | Rodar `scripts/link_cause_rank_worker.py --allow-http --apply` após novos sintomas | FWs / `18116214` | Dry-run com `candidates=[]` ou só ambíguos |
| 0.2 | Confirmar que só a causa Vivo tem `notify=teams` entre roots de link | action 22 / tags | `problem.get` roots com notify=teams = 1 (a causa) |
| 0.3 | Registrar no canal NOC: “piloto 16/45 off; sintomas sob 18116214” | operação | Time alinhado |

**Atualização 2026-10-02:** `close_new` 16/45 **reativadas** (sintomas não ficavam correlacionados só com rank pontual). Trade-off: tempestade PROBLEM+OK enquanto causa Vivo aberta.

---

## Fase 1 — Coleta rápida (D1–D5) — CONCLUÍDA 2026-10-01

**Objetivo:** zerar unsupported enabled fáceis e o buraco ICMP.

| # | Ação | Objeto | Abordagem | Pronto quando | Status |
| --- | --- | --- | --- | --- | --- |
| 1.1 | `BGP-ACA-AP01` ICMP | event `17297217` | Host já disabled (`status=1`); `manual_close` no trigger ICMP tpl `23176`; evento fechado (`r_eventid` `18525365`) | Problem fechado ou host disabled com nota | OK |
| 1.2 | Speed `-1000000` | items `104688`–`104692` em `BGP-SRV-FREP` | JS sanitize sentinela `-1`/negativos → `0` no protótipo tpl `42682` (host proto `104339`) | state=0 ou status=1 documentado | OK (itens `state=0`; JS no proto — sync LLD net.if ≤1h) |
| 1.3 | Toner magenta `"-2"` | item `110116` `SCL-DRH-COLOR01` | JS sanitize no proto tpl RICOH `96476` (host proto `96489`); check-now task `4372` | Unsupported resolvido | OK (`state=0`, prep `21`) |
| 1.4 | IIS AppPool queue timeout | item `108972` `BGP-SRV-VAPP10` | Item + trigger `51071` disabled (pool `.NET v2.0` morto / timeout) | Unsupported resolvido ou item disabled | OK (`status=1`) |

**Validação P0 (2026-10-01):** `unsupported enabled = 0`; ICMP `17297217` ausente de `problem.get`; host `10713` disabled.

**Backups/apply:** `backups/phase1_*_20261001.json`, requests em `zabbix-requests/phase1_*`.

**Dependência:** nenhuma. Pode paralelizar 1.2–1.4 com 1.1.

---

## Fase 2 — Correlação contínua (D2–D7) — CONCLUÍDA 2026-10-05

**Objetivo:** sintomas de link não voltarem como causa raiz.

| # | Ação | Detalhe | Pronto quando | Status |
| --- | --- | --- | --- | --- |
| 2.1 | Agendar rank no **servidor/automação Capri** (não na estação) | Cron root `*/10` `--apply` em `spo-srv-v01`; `/opt/zabbix-observality`; env `/etc/zabbix/link_cause_rank.env`; log `/var/log/zabbix/link_cause_rank.log` | Task ativa com `--apply`; 48h sem órfãos | **OK** — cron `--apply` ativo 05/10; apply manual `18556245`→`18116214`; observar 48h |
| 2.2 | Decidir destino dos 4 roots FW não-Vivo | Macros `CONTROL=0`: BRAS `lan2`/`lan3`, SPO `dmz`, AZ `az-to-oci-vpn2`; eventos fechados | Cada um: corrigido **ou** suppressed com justificativa | **OK** (macros 8605–8608; triggers `value=0`) |
| 2.3 | Plano 16/45 | Reativadas em 02/10 para correlação persistir | ADR/nota on/off | **OK — ON** |

**Validação P0 FW (2026-10-05):** apply rankou `18556245` (VPN SYSTEXTIL_W1) sob `18116214` SPO_VIVO; dry-run pós-apply `candidates=[]`.

**Artefatos:** matriz `reports/link-correlation-matrix-20260930.csv`; `scripts/link_cause_rank_worker.py`; `scripts/run_link_cause_rank.sh`; backups `phase2_1_*_20261005.json`, `link_cause_before_rank_18556245_*`.

---

## Fase 3 — LLD crítica (D5–D15) — CONCLUÍDA 2026-10-05

**Objetivo:** zerar LLD bad enabled no escopo; remediar o que a API permite; deixar explícito o que depende de agente/rede para reativação futura.

**Evidência:** `reports/phase3-lld-baseline-20261005.md`, `reports/phase3-conclusao-20261005.md` — **LLD bad enabled = 0** no escopo.

| Atividade | O quê | Status |
| --- | --- | --- |
| **3A–3C contenção** | Desabilitar LLD quebrada | **OK** |
| **3D remediação** | Ajustes proxy/iface/macros/templates + desvínculos | **OK** (reativação plena de Hyper-V/SNMP/MySQL/disk/FAD fica para ops instalar módulo/feature — ver 3D) |

### 3A — Hyper-V — OK

| Hosts | LLD | Correção |
| --- | --- | --- |
| FHV* + FAD01 | `hyperv.discover.vms` / disks | Discovery **disabled no template** `Template Windows Hyper-V Host 2` (agentes 7.0.26 sem métrica) |
| SPO-SRV-FAD01 | `service.discovery` | **Disabled** — colisão com `Template App NDD Print`; macro `{$SERVICE.NAME.NOT_MATCHES}` ampliada |

### 3B — Switches SNMP — OK (walk contido; proxy/iface endurecidos)

| Hosts | Correção |
| --- | --- |
| SCL-CPD-SW01, SCL-TEC2-SW01, SPO-CPD-SW01 | Proxy `timeout_snmp_agent=60s`; iface **bulk=0**, max_rep **3**; `net.if.walk` + LLD **disabled** (CBS350 ainda timeout no walk) |

Unknown TEC* (~554) → **Fase 4**.

### 3C — LLD config — OK

| Host | Correção |
| --- | --- |
| AZ-VM-APP-03-DB | `{$MYSQL.DSN}=tcp://127.0.0.1:3306`; LLD extra/replication **disabled** (agent2 ainda resolve placeholder) |
| SPO-SRV-V02 | Template **PostgreSQL desvinculado** |
| BGP-SRV-VAPP12 | WMI AppPool **disabled** (Invalid namespace) |
| SCL-ETE-TB01, SCL-TIN-TMXC01 | PhysicalDisk LLD **disabled** (PDH falha `_en` e locale) |

### 3D — Remediação executada + pré-requisitos ops para reativar

| # | Tema | Feito na Fase 3 | Para reativar discovery (ops) | Status |
| --- | --- | --- | --- | --- |
| 3D.1 | Hyper-V | Tpl discovery off | Loadable module / UserParameter nos agentes → reabilitar 87847/87848 | Fechado Zabbix; ops se quiser inventário VM |
| 3D.2 | SNMP CBS350 | Proxy 60s + bulk=0 + max_rep=3; walk off | Walk completar sem timeout → reabilitar walk+LLD | Fechado Zabbix; rede/CBS350 se quiser LLD if |
| 3D.3 | MySQL AZ | Macro DSN host; LLD off | Corrigir expansão DSN no agent2 / grants → reabilitar | Fechado Zabbix |
| 3D.4 | pgsql SPO-V02 | Template unlinked | Instalar plugin + religar template | **OK completo** |
| 3D.5 | IIS VAPP12 | LLD AppPool off | Feature IIS WMI ou manter off | Fechado Zabbix |
| 3D.6 | PhysicalDisk | LLD off; tpl `_en` preservado | Corrigir PDH/locale no OS ou aceitar só `vfs.fs` | Fechado Zabbix |
| 3D.7 | FAD01 services | Macro NOT_MATCHES; discovery off | Remover service.info estáticos NDD **ou** manter discovery off | Fechado Zabbix |

**Backups:** `backups/phase3_lld_before_disable_*`, `phase3b_*`, `phase3d_before_apply_*`, `phase3d_followup_before_*`.

---

## Fase 4 — Cascata Unknown (D10–D20) — CONCLUÍDA 2026-10-05

**Objetivo:** 852 → &lt;200 Unknown enabled, atacando **causa**, não silenciando trigger.

**Resultado:** Unknown global **834 → 90**; TEC2/TEC1-SW02/TEC1-SW03/CPD/VAPP10 → **0**. Evidência: `reports/phase4-conclusao-20261005.md`.

| Prioridade | Host / padrão | Ação | Status |
| --- | --- | --- | --- |
| P1 | SCL-TEC2-SW01, TEC1-SW02, TEC1-SW03 | Triggers Unknown com item disabled/unsupported → disabled | **OK** (0) |
| P1+ | SCL/SPO-CPD-SW01, BGP-SRV-VAPP10 | Mesmo critério | **OK** |
| P2 | Macro `{$VOLUME_SIZE_ALARM}` | Sem Unknown ativo por essa macro na varredura | **OK** (n/a) |
| P2 | VAPP10 IIS / MSSQL Homolog | VAPP10 limpo; Homolog unsupported enabled não encontrado | **OK** |
| P3 | NAS / SW02 / Zabbix server | Sweep residual (+179); ~90 Unknown restantes | Residual → Fase 5 |

**Pronto:** Unknown &lt;200 ✅; top TEC* &lt;50 ✅.

**Backups:** `backups/phase4_unknown_triggers_before_*`, `phase4_residual_before_*`.

---

## Fase 5 — Higiene e endurecimento (D15–D30)

| # | Tema | Ação | Pronto |
| --- | --- | --- | --- |
| 5.1 | Fila ≥7d (65 roots) | Triagem semanal: ack / fechar / desabilitar UPS lifetime e MSSQL crônicos sem dono; priorizar high `11804031` | ≤40 roots ≥7d |
| 5.2 | httptest `verify_peer` | Habilitar onde o CA for confiável (piloto 5 cenários → resto) | Maioria verify_peer=1 |
| 5.3 | SNMP v1/v2 → v3 | Inventário 84 ifaces; migrar Cisco/Aruba/iDRAC com suporte | Plano + % migrado |
| 5.4 | state=1 disabled (~5801) | Não reativar; opcional purge/documentar top hosts | Nota de governança |

---

## Fase 6 — Governança contínua (D20–D30+)

| # | Ação | Pronto |
| --- | --- | --- |
| 6.1 | Internal action (doc Zabbix): notificar item/LLD unsupported e trigger Unknown | Ação interna criada + teste |
| 6.2 | Re-auditoria full com skill `zabbix-config-audit` | Novo `reports/auditoria-zabbix-YYYYMMDD.md` batendo metas |
| 6.3 | Rank worker em monitoramento (falha do job = alerta) | Job falho gera notificação |

---

## Fase 7 — Alertas Zabbix → Microsoft Teams (D7–D21)

**Objetivo:** cada incidente que o NOC precisa ver chega no Teams **uma vez** (PROBLEM + OK), sem chuva de sintoma e sem buraco silencioso.

**Contexto já feito (não refazer):** ação `22` (`Notificar MS Teams`) filtra só `notify=teams`; `esc_period≈5m`; `pause_symptoms=1`; recovery presente; agregados VPN sem Teams (Fase D 30/09).

| # | Ação | Detalhe | Pronto quando | Status |
| --- | --- | --- | --- | --- |
| 7.1 | Baseline de entrega | `action.get` 22 + media type Teams; `alert.get` 7d (enviados / falhos / sem media); listar erros de webhook | Relatório `reports/teams-alerts-baseline-YYYYMMDD.md` com contagens | Pendente |
| 7.2 | Inventário `notify=teams` | Quem tem a tag (host/template/protótipo): causas de link, servidores críticos, impressoras, etc. vs sintomas que ainda herdam a tag | Planilha/CSV: deve notificar / não deve / indefinido | Pendente |
| 7.3 | Cobertura (buracos) | Problemas High/Disaster **sem** `notify=teams` que o NOC espera (ex.: Hyper-V pressão real, host unreachable, disco crítico) | Lista aprovada + tags aplicadas **só** no aprovado | Pendente |
| 7.4 | Ruído (sobra) | Sintomas FW/VPN/SD-WAN, LLD flap, Warning crônico com `notify=teams` indevido → remover tag (sintoma fica só no Zabbix) | `alert.get` sem envio de sintoma sob causa aberta | Pendente |
| 7.5 | PROBLEM + recuperação | Para cada classe aprovada: abrir/fechar (ou usar evento real) e confirmar **2** alerts Teams (problem + recovery) via `alert.get` | 100% das classes piloto com par PROBLEM/OK | Pendente |
| 7.6 | Flapping / atraso | Validar `esc_period=5m` e `pause_symptoms` sob causa link; documentar exceções (ex.: segurança sem delay) | Nota operacional + zero tempestade no canal NOC em 48h de piloto | Pendente |
| 7.7 | Canal e formatação | Media type / mensagem: host, severidade, opdata, link da UI; **sem** bloco “Ação sugerida”/recomendações; canal correto | Mensagem legível aprovada pelo NOC | **OK parcial** — recomendações removidas do media type `53` em 2026-10-05 |
| 7.8 | Automação auxiliar | Revisar `automacao/sync_teams_notifications.py` (se ainda usada): não duplicar ação 22; ou desativar se obsoleta | Uma única fonte de verdade = ação 22 | Pendente |

**Regras da fase (não negociar sem ADR):**

1. Teams **só** com tag `notify=teams` (não voltar filtro “severity ≥ High”).
2. Um alerta por causa raiz; sintoma sob correlação/rank **sem** a tag.
3. Sempre validar recuperação — PROBLEM sem OK deixa o canal mentindo.
4. Backup da ação 22 e das triggers/tags antes de cada mutação (`backups/phase7_*`).

**Aceite da fase:**

- Baseline 7.1 publicado.
- Zero sintoma de link/VPN no Teams sob causa aberta (amostra 48h).
- Classes críticas aprovadas em 7.3 com par PROBLEM/OK comprovado.
- Media type sem falha recorrente de webhook (ou falha com dono + alerta interno).

**Dependência:** Fase 2 estável (rank no Capri) reduz tempestade; 7.3/7.4 podem começar em paralelo com Fase 3.

**Artefatos esperados:** `reports/teams-alerts-baseline-*.md`, `reports/teams-notify-inventory-*.csv`, `backups/phase7_*`, requests em `zabbix-requests/phase7_*`.

---

## Ordem sugerida de execução (checklist)

```
Progresso:
- [x] Fase 0 — rank manual + alinhamento NOC
- [x] Fase 1 — ICMP AP + 7 unsupported
- [x] Fase 2 — agenda rank + 4 roots FW (cron `--apply` Capri 05/10)
- [x] Fase 3A — Hyper-V LLD (tpl discovery off)
- [x] Fase 3B — SNMP LLD switches (proxy 60s/bulk=0; walk contido)
- [x] Fase 3C — MySQL/pgsql/WMI/disk LLD
- [x] Fase 3D — Remediação API (pgsql unlinked; macros/proxy/iface; reativações ops opcionais)
- [x] Fase 4 — Unknown TEC* + macros (834→90)
- [ ] Fase 5 — fila antiga / TLS / SNMPv3
- [ ] Fase 6 — internal actions + re-auditoria
- [ ] Fase 7 — Teams: baseline → inventário → cobertura/ruído → PROBLEM/OK
```

---

## Fora de escopo / decisões explícitas

- **Não** correlacionar switch→AP (decisão 2026-07-27).
- **Não** aumentar timeout global de server/proxy/agent para “limpar” unsupported.
- **Não** reativar close_new 16/45 sem fase 2.1 estável e janela observada (já reativadas em 02/10 — só mudar com evidência).
- Hosts Monitoramento Web sem template: exceção conhecida — não é fase desta roadmap.
- **Não** ampliar ação 22 para “toda severidade High” sem matriz 7.2/7.3 aprovada (volta chuva no Teams).

---

## Referências

- Auditorias: `reports/auditoria-zabbix-20261001.md`, `-coleta.md`, `-firewalls.md`
- Skill correção: `.agents/skills/zabbix-senior-analyst/`
- Skill re-auditoria: `.agents/skills/zabbix-config-audit/`
- Worker: `scripts/link_cause_rank_worker.py`
- Matriz: `reports/link-correlation-matrix-20260930.csv`
- Teams (histórico): `reports/phases-cdef-execucao-20260930.md`, `automacao/sync_teams_notifications.py`
- Runbook unsupported histórico: `docs/production-remediation-runbook-20260909.md`
