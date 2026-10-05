# Auditoria Zabbix Capricórnio — 01/10/2026

**Gerado em:** 01/10/2026 10:51 (America/Sao_Paulo)  
**Escopo:** full (P0 coleta + P1 configuração/governança)  
**Modo:** somente leitura

## Resumo

Ambiente **operacional**, com proxies OK e correlação de firewalls sob a causa Vivo já sanitizada (**65 sintomas / 5 roots** nos FWs). O risco estrutural agora é **saúde de coleta**: **7 itens unsupported enabled**, **20 LLD unsupported**, **852 triggers Unknown** (cascata forte em switches SCL-TEC*) e falta de rank periódico enquanto `close_new` 16/45 seguem desligadas. Fora disso, fila antiga de problems (≥7d) e 1 AP ICMP down há ~28 dias.

## Achados

### Crítico

- **`SPO-CPD-FW01` / evento `18116214` / `link-cause=SPO_VIVO`** — Link HK_ISP1 (VIVO) DOWN ainda aberto (~3d, high, `notify=teams`). É a causa ativa dos sintomas FortiGate; novos sintomas sem rank reaparecem como raiz.
  - Evidência: problema aberto com tag `link-cause=SPO_VIVO`; correlações 16/45 disabled.

- **Correlações `16` e `45` desabilitadas sem worker periódico em produção** — piloto anti-storm válido, mas sem `link_cause_rank_worker.py` agendado a governança é manual. Sintomas novos voltam a poluir a tela.
  - Evidência: `correlation.get` status=1 em 16/45; 17/46 enabled.

- **`BGP-ACA-AP01` / evento `17297217`** — `Unavailable by ICMP ping` (high) há ~27.9d. Host de AP sem resposta ICMP — risco de buraco de cobertura/SLA `hostdown`.
  - Evidência: `event.get` 17297217, tags `infra=ap`, `scope=availability`.

- **LLD Hyper-V `Unknown metric` em hosts FHV** — discovery de VMs não coleta (`hyperv.discover.vms` / disks) em SCL/BGP/SPO FHV*. Feature de inventário Hyper-V efetivamente cega.
  - Evidência: LLD unsupported enabled nos hosts FHV (ver tabela P0).

### Atenção

- **7 itens unsupported enabled** (lista completa na seção P0): speed `-1000000` em `BGP-SRV-FREP` (5 itens), timeout IIS em `BGP-SRV-VAPP10`, toner `"-2"` em `SCL-DRH-COLOR01`.

- **852 triggers Unknown enabled** — cascata; top hosts: SCL-TEC2-SW01(284), SCL-TEC1-SW02(144), SCL-TEC1-SW03(122), BGP-NAS-Hyperv(18), SCL-CPD-SW02(17). Erros frequentes: macro `{$VOLUME_SIZE_ALARM}`, IIS queue, backup MSSQL unsupported.

- **20 LLD unsupported enabled** — além de Hyper-V: `net.if.discovery` timeout parcial em switches (`SCL-CPD-SW01`, `SCL-TEC2-SW01`, `SPO-CPD-SW01`); MySQL DSN placeholder em `AZ-VM-APP-03-DB`; WMI AppPool em `BGP-SRV-VAPP12`; PhysicalDisk localized name em `SCL-ETE-TB01` / `SCL-TIN-TMXC01`; pgsql unknown metric em `SPO-SRV-V02`.

- **SNMP v1/v2 ainda em uso:** versões observadas {'3': 144, '1': 26, '2': 58} (contagem de interfaces em hosts enabled). Migrar para v3 onde o equipamento permitir (Cisco/Aruba/iDRAC).

- **39/39 httptests enabled sem `verify_peer`** — verificação TLS do peer desligada nos cenários web.

- **Fila antiga:** 65 problems-raiz com ≥7 dias; 132/133 sem acknowledgement. Exemplos: MSSQL work table cache (~139d, high), UPS battery lifetime (~135d, info), serviços Windows/Linux.

- **4 alertas FW independentes (não Vivo):** `lan3`/`lan2` BRAS, `dmz` SPO, `az-to-oci-vpn2` Azure — validar se esperado ou silenciar.

### Informativo

- Hosts enabled: **320**; sem template: **22** (dos quais ~21 em Monitoramento Web) — exceção conhecida.
- Correlações: **59** total; só **2** disabled (16 e 45).
- Dual `scope=capacity`+`availability` em problems abertos: **0**.
- Itens `state=1` no total (incl. disabled): ~**5801** — maioria disabled (limpeza); não tratar como Crítico.
- Em Classificação: nenhum host na busca anterior.
- Ação Teams `22`: enabled, `notify=teams`, `esc_period=5m`, `pause_symptoms=1`, com recovery — alinhada à decisão local.
- Proxies SPO/SCL/BGP: lastaccess &lt;1 min, version 70026 — OK.

## Saúde de coleta (P0)

| Indicador | Valor |
| --- | --- |
| Unsupported enabled | 7 |
| LLD unsupported enabled | 20 |
| Triggers Unknown enabled | 852 |
| Proxies | 3 OK (lastaccess &lt;1 min) |
| Interfaces unavailable (`available=2`) | 0 (snapshot) |
| Reachability (ICMP/agent/SNMP) | 1 (`BGP-ACA-AP01`) |
| state=1 total (enabled+disabled) | ~5801 |

### Unsupported enabled (lista completa)

| Host | Itemid | Nome | Erro |
| --- | --- | --- | --- |
| BGP-SRV-FREP | 104688 | Interface eno8403: Speed | Value of type "string" is not suitable for value type "Numeric (unsigned)". Value "-100000 |
| BGP-SRV-FREP | 104689 | Interface enp24s0f0: Speed | Value of type "string" is not suitable for value type "Numeric (unsigned)". Value "-100000 |
| BGP-SRV-FREP | 104690 | Interface enp24s0f1: Speed | Value of type "string" is not suitable for value type "Numeric (unsigned)". Value "-100000 |
| BGP-SRV-FREP | 104691 | Interface enp24s0f2: Speed | Value of type "string" is not suitable for value type "Numeric (unsigned)". Value "-100000 |
| BGP-SRV-FREP | 104692 | Interface enp24s0f3: Speed | Value of type "string" is not suitable for value type "Numeric (unsigned)". Value "-100000 |
| BGP-SRV-VAPP10 | 108972 | AppPool .NET v2.0 current queue size | Timeout occurred while gathering data. |
| SCL-DRH-COLOR01 | 110116 | Nível de toner: Toner magenta | Value of type "string" is not suitable for value type "Numeric (unsigned)". Value "-2" |

### LLD unsupported enabled (amostra)

| Host | LLD | Erro |
| --- | --- | --- |
| SCL-CPD-SW01 | Network interfaces discovery | only partial data received, cannot retrieve OID: '.1.3.6.1.2.1.31.1.1.1.1.80' from [[172.1 |
| SCL-TEC2-SW01 | Network interfaces discovery | only partial data received, cannot retrieve OID: '.1.3.6.1.2.1.31.1.1.1.6.80' from [[172.1 |
| SPO-CPD-SW01 | Network interfaces discovery | only partial data received, cannot retrieve OID: '.1.3.6.1.2.1.31.1.1.1.18.100' from [[172 |
| SPO-SRV-V02 | Database discovery | Unknown metric pgsql.discovery.db |
| AZ-VM-APP-03-DB | MariaDB discovery | Invalid parameters: Invalid first parameter "URI": parse "tcp://<Put your DSN>": invalid c |
| AZ-VM-APP-03-DB | Replication discovery | Cannot fetch data: Cannot fetch data.: error getting slave or replica status: Error 1227 ( |
| SCL-SRV-FHV02 | Hyper-V VM Discovery | Unknown metric hyperv.discover.vms |
| SCL-SRV-FHV02 | Hyper-V VM Disk Discovery | Unknown metric hyperv.discovery.vms |
| SCL-SRV-FHV03 | Hyper-V VM Discovery | Unknown metric hyperv.discover.vms |
| SCL-SRV-FHV03 | Hyper-V VM Disk Discovery | Unknown metric hyperv.discovery.vms |
| SPO-SRV-FAD01 | Hyper-V VM Discovery | Unknown metric hyperv.discover.vms |
| BGP-SRV-VAPP12 | Application pools discovery | Exception occurred. (Invalid namespace ) |
| BGP-SRV-FHV01 | Hyper-V VM Discovery | Unknown metric hyperv.discover.vms |
| BGP-SRV-FHV01 | Hyper-V VM Disk Discovery | Unknown metric hyperv.discovery.vms |
| BGP-SRV-FHV02 | Hyper-V VM Discovery | Unknown metric hyperv.discover.vms |
| BGP-SRV-FHV02 | Hyper-V VM Disk Discovery | Unknown metric hyperv.discovery.vms |
| BGP-SRV-FHV03 | Hyper-V VM Discovery | Unknown metric hyperv.discover.vms |
| BGP-SRV-FHV03 | Hyper-V VM Disk Discovery | Unknown metric hyperv.discovery.vms |
| SCL-ETE-TB01 | Physical disks discovery | Cannot obtain object's localized name. |
| SCL-TIN-TMXC01 | Physical disks discovery | Cannot obtain object's localized name. |

### Triggers Unknown — top hosts

| Host | Qtd Unknown |
| --- | --- |
| SCL-TEC2-SW01 | 284 |
| SCL-TEC1-SW02 | 144 |
| SCL-TEC1-SW03 | 122 |
| BGP-NAS-Hyperv | 18 |
| SCL-CPD-SW02 | 17 |
| BGP-SRV-VAPP10 | 12 |
| SCL-SRV-FREP | 10 |
| CLICKHOUSE-172.16.2.145 | 10 |
| BGP-NAS-DB | 10 |
| BGP-NAS-03 | 10 |
| SCL-NAS-Hyperv | 10 |
| SPO-NAS-Backup | 10 |

### Proxies

| Nome | lastaccess (min) | state | version | compatibility |
| --- | --- | --- | --- | --- |
| SPO-SRV-V04 | 1.2 | 2 | 70026 | 1 |
| SCL-SRV-V08 | 1.2 | 2 | 70026 | 1 |
| BGP-SRV-V08 | 1.2 | 2 | 70026 | 1 |

## Correlação / problemas

| Indicador | Valor |
| --- | --- |
| Problems abertos (global) | 133 (68 roots / 65 symptoms) |
| FW problems | 70 (5 roots / 65 symptoms) |
| Roots ≥7d | 65 |
| Sem ack | 132/133 |
| Correlações 16 / 45 | disabled (piloto) |
| Correlações 17 / 46 | enabled (close_old) |

### Roots FW abertos

| Eventid | Host | Dias | Sev | Nome | link-cause |
| --- | --- | --- | --- | --- | --- |
| 17437418 | BRAS-CPD-FW01 | 20.2 | info | FortiGate: Interface lan3(ISP2-): Link down | — |
| 17441868 | AZ-VM-FW-01 | 19.9 | info | FortiGate: VPN az-to-oci-vpn2: Tunnel down | — |
| 17498586 | BRAS-CPD-FW01 | 16.8 | info | FortiGate: Interface lan2(): Link down | — |
| 18116214 | SPO-CPD-FW01 | 3.1 | high | SPO: Link HK_ISP1 (VIVO) DOWN | SPO_VIVO |
| 18379687 | SPO-CPD-FW01 | 1.8 | avg | FortiGate: Interface dmz(): Link down | — |

### Correlações SPO Vivo

| Id | Nome | Status |
| --- | --- | --- |
| 17 | SPO VIVO: fechar sintomas abertos ao disparar causa | enabled |
| 16 | SPO VIVO: fechar sintomas enquanto causa ativa | disabled |
| 45 | SPO VPN ISP1 (VIVO): fechar sintomas novos enquanto causa ativa | disabled |
| 46 | SPO VPN ISP1 (VIVO): fechar sintomas ja abertos ao disparar causa | enabled |

## Dados consultados

| Método | Filtro | Artefato |
| --- | --- | --- |
| problem.get | recent, tags, cause | `backups/audit_report_all_open_problems_20261001.json` |
| host.get | status=0 + templates | `backups/audit_report_hosts_enabled_20261001.json` |
| item.get | state=1,status=0 por host | `backups/audit_deep_remaining_gaps_20261001.json` |
| discoveryrule.get | state=1 | `backups/audit_deep_lld_unsupported_20261001.json` |
| trigger.get | state=1,status=0 | `backups/audit_deep_remaining_gaps_20261001.json` |
| proxy.get | Zabbix 7 fields | `backups/audit_deep_proxies_20261001.json` |
| hostinterface.get | type=2 SNMP | `backups/audit_deep_snmp_interfaces_20261001.json` |
| httptest.get | verify_peer | `backups/audit_deep_httptests_20261001.json` |
| correlation.get | status | `backups/audit_report_correlations_20261001.json` |
| action.get | eventsource=0 | `backups/audit_report_actions_20261001.json` |
| problem.get | hostids FW | `backups/audit_all_fw_open_problems_with_cause_20261001.json` |

## Próximos passos

1. **Incidente Vivo `18116214`** — acompanhar recuperação; manter sintomas ranqueados (via `zabbix-senior-analyst` + worker).
2. **Agendar `link_cause_rank_worker.py --apply`** no servidor/automação Capri (5–15 min) enquanto 16/45 off — ou planejar reativação controlada do `close_new`.
3. **ICMP `BGP-ACA-AP01`** — validar se AP está offline de verdade ou IP/monitoramento errado; corrigir ou desativar host.
4. **Unsupported enabled (7)** — FREP speed (tratar valor sentinela), VAPP10 IIS (plano runbook), toner magenta (tipo/valor −2).
5. **LLD Hyper-V + switches SNMP timeout** — plugin agente / filtros LLD / timeout pontual (não global).
6. **Triggers Unknown em SCL-TEC\*** — atacar causa (itens/macros/OID), não só a trigger.
7. **Triagem fila ≥7d** — UPS lifetime / MSSQL crônicos: ack, desabilitar ou corrigir.
8. **httptest `verify_peer`** — habilitar onde certificado for confiável.
9. Qualquer mudança: runbook `zabbix-senior-analyst` (backup → menor mudança → validação).
