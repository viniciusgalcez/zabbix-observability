# Auditoria Zabbix Capricórnio — 05/10/2026

**Gerado em:** 05/10/2026 14:49 (America/Sao_Paulo)
**Escopo:** full
**Modo:** somente leitura

## Resumo

Ambiente pós Fases 1–4: coleta limpa no essencial (**unsupported enabled=4**, **LLD bad enabled=1**, **Unknown=90**). Ainda há dívida de fila (≥7d=58), SNMP v1/v2 (84 ifaces), e residual Unknown/NAS. Correlação 16/45 e ação Teams 22 seguem o desenho Capri.

## Achados

### Crítico

- **Unsupported enabled = 4** — coleta quebrada em produção. Top: BGP-SRV-VAPP10(4). Evidência: `backups/audit_full_evidence_20261005T174901Z.json`.

### Atenção

- **LLD unsupported enabled = 1** — discovery falhando. `SPO-NAS-Backup` `net.if.discovery`
- **Triggers Unknown enabled = 90** — abaixo de 200 (meta fase), ainda acima da meta 30d (≤50). Top: BGP-NAS-Hyperv(17), SCL-CPD-SW02(15), SCL-NAS-Hyperv(9), BGP-NAS-Backup(9), BGP-NAS-03(9), SCL-NAS-Backup(9), BGP-NAS-DB(9), SPO-NAS-Backup(9)
- **Interfaces unavailable (enabled hosts) = 2** — `SCL-Tenda-AP01`, `SCL-Tenda-AP02`
- **Problems-raiz ≥7d = 58** (58 sem ack) — fila operacional (meta Fase 5 ≤40).
- **FW roots com notify=teams = 1** — `18116214` SPO: Link HK_ISP1 (VIVO) DOWN
- **Internal actions** para unsupported/Unknown ausentes ou disabled — doc Zabbix recomenda notificar eventos internos (Fase 6.1).
- **Hosts enabled sem template (exceto Web) = 1** — `Azure Microsoft SQL database master`
- **SNMP v1/v2 em hosts enabled = 84** (v3 count=145) — migração Fase 5.3.
- **Problems de reachability ≈ 2** (amostra por nome ICMP/agent/SNMP).

### Informativo

- Correlação `16` `SPO VIVO: fechar sintomas enquanto causa ativa` = **ON**.
- Correlação `45` `SPO VPN ISP1 (VIVO): fechar sintomas novos enquanto causa ativa` = **ON**.
- Ação Teams `22` status=0 esc_period=5m pause_suppressed=1 recovery_ops=0.

## Saúde de coleta (P0)

| Indicador | Valor |
| --- | --- |
| Unsupported enabled | **4** (state=1 total 5761) |
| LLD unsupported enabled | **1** (state=1 total 24) |
| Triggers Unknown enabled | **90** |
| Hosts enabled | 321 |
| Proxies OK / atrasados | 3 / 0 |
| Interfaces unavailable (hosts enabled) | 2 |
| Problems abertos (amostra≤2000) | 153 (roots 116 / symptoms 37) |
| Roots ≥7d / unack | 58 / 58 |
| Reachability (nome) | 2 |

### Top Unknown por host

| Host | Unknown |
| --- | ---: |
| BGP-NAS-Hyperv | 17 |
| SCL-CPD-SW02 | 15 |
| SCL-NAS-Hyperv | 9 |
| BGP-NAS-Backup | 9 |
| BGP-NAS-03 | 9 |
| SCL-NAS-Backup | 9 |
| BGP-NAS-DB | 9 |
| SPO-NAS-Backup | 9 |
| AZ-VM-APP-03-DB | 2 |
| CLICKHOUSE-172.16.2.145 | 1 |
| BGP-SRV-V06 | 1 |

### Unsupported enabled (lista)

| Host | itemid | key | erro |
| --- | --- | --- | --- |
| BGP-SRV-VAPP10 | 108967 | `perf_counter_en["\HTTP Service Request Queues(Defa` | Timeout occurred while gathering data. |
| BGP-SRV-VAPP10 | 108974 | `perf_counter_en["\HTTP Service Request Queues(Deps` | Timeout occurred while gathering data. |
| BGP-SRV-VAPP10 | 108973 | `perf_counter_en["\HTTP Service Request Queues(Deps` | Timeout occurred while gathering data. |
| BGP-SRV-VAPP10 | 111905 | `perf_counter_en["\HTTP Service Request Queues(Deps` | Timeout occurred while gathering data. |

### LLD unsupported enabled

| Host | itemid | key | erro |
| --- | --- | --- | --- |
| SPO-NAS-Backup | 69789 | `net.if.discovery` | Timeout while retrieving data from "172.17.2.19:161". |

### Proxies

| Proxy | lastaccess | version | compat | Status |
| --- | --- | --- | --- | --- |
| BGP-SRV-V08 | age=-2s | ver=70026 | compat=1 | OK |
| SPO-SRV-V04 | age=-1s | ver=70026 | compat=1 | OK |
| SCL-SRV-V08 | age=-1s | ver=70026 | compat=1 | OK |

## Correlação / FW

| Indicador | Valor |
| --- | --- |
| Hosts FW (grupos) | 7 |
| Problems FW | 93 (roots 56) |
| Roots FW notify=teams | 1 |
| Roots com tag link-cause | 1 |

- `18116214` SPO: Link HK_ISP1 (VIVO) DOWN — class=network, component=sd-wan, health-check=HK_ISP1, health-check=HK_ SynergyRH, health-check=HK_Systextil_Web, health-check=HK_TEAMS

## Configuração (P1)

- SNMP versão (ifaces hosts enabled): {'3': 145, '1': 26, '2': 58}
- SNMP v1/v2: 84
- Hosts sem template (não-Web): 1
- Discovery rules (drule): 4 (enabled=3)
- Grupos Classificação: []
- httptest/cenários: 40

## Dados consultados

| Método | Filtro | Artefato |
| --- | --- | --- |
| item/trigger/discoveryrule.get | state/status P0 | `backups\audit_full_evidence_20261005T174901Z.json` |
| problem.get | recent + FW groups | idem |
| proxy/action/correlation/hostinterface/drule | P1 | idem |

## Próximos passos

1. **Fase 5.1** — triar roots ≥7d (ack/fechar/desabilitar crônicos) → via `zabbix-senior-analyst` + backup.
2. **Residual Unknown (~90)** — NAS Hyperv/Backup e SCL-CPD-SW02: corrigir item ou desabilitar trigger órfã.
3. **Fase 5.3** — plano SNMP v3 para Cisco/Aruba/iDRAC ainda em v1/v2.
4. **Fase 6.1** — criar internal action para unsupported/Unknown.
5. **Fase 7** — baseline Teams (`alert.get` 7d) se ainda não medido.
6. Reativar LLD Hyper-V/SNMP walk só após pré-requisitos ops (Fase 3D).
