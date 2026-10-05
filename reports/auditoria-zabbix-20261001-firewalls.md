# Auditoria Zabbix — Firewalls / correlação de links — 01/10/2026

**Gerado em:** 01/10/2026 10:51 (America/Sao_Paulo)  
**Escopo:** firewalls / links  
**Modo:** somente leitura

## Resumo

Nos 7 firewalls, a correlação por **rank** está coerente neste momento: **65 sintomas** sob causas linkadas vs **5 roots**. A única causa de link ativa é **SPO Vivo** (`18116214`). O risco é **regeneração de sintomas órfãos** porque `close_new` 16/45 estão off e o worker não roda sozinho.

## Achados

### Crítico

- **`18116214` SPO Link HK_ISP1 (VIVO) DOWN** — causa raiz ativa; Teams notifica esta.
- **Governança:** 16/45 disabled sem agenda de rank → sintomas novos (SCLISP*/MTZISP*/P2MTZ1*) voltam soltos (já ocorreu em 30/09 e 01/10).

### Atenção

- **4 roots FW não-Vivo** (interfaces/VPN locais) — decidir destino operacional.

### Informativo

- Hosts FW: AZ-VM-FW-01, BGP-CPD-FW01, BR-DENIM-CAPRI-FW01, BR-SCL-FIA-FW01, BRAS-CPD-FW01, SCL-CPD-FW01, SPO-CPD-FW01.
- Matriz: `reports/link-correlation-matrix-20260930.csv` (inclui `SYSTEXTIL_W1`).
- Worker: `scripts/link_cause_rank_worker.py` (retry em `event.get`; não aborta lote).

## Correlação / problemas

| Indicador | Valor |
| --- | --- |
| FW problems | 70 |
| Roots | 5 |
| Symptoms | 65 |
| 16 / 45 | disabled |
| 17 / 46 | enabled |

### Roots FW

| Eventid | Host | Dias | Sev | Nome | link-cause |
| --- | --- | --- | --- | --- | --- |
| 17437418 | BRAS-CPD-FW01 | 20.2 | info | FortiGate: Interface lan3(ISP2-): Link down | — |
| 17441868 | AZ-VM-FW-01 | 19.9 | info | FortiGate: VPN az-to-oci-vpn2: Tunnel down | — |
| 17498586 | BRAS-CPD-FW01 | 16.8 | info | FortiGate: Interface lan2(): Link down | — |
| 18116214 | SPO-CPD-FW01 | 3.1 | high | SPO: Link HK_ISP1 (VIVO) DOWN | SPO_VIVO |
| 18379687 | SPO-CPD-FW01 | 1.8 | avg | FortiGate: Interface dmz(): Link down | — |

### Correlações SPO

| Id | Nome | Status |
| --- | --- | --- |
| 17 | SPO VIVO: fechar sintomas abertos ao disparar causa | enabled |
| 16 | SPO VIVO: fechar sintomas enquanto causa ativa | disabled |
| 45 | SPO VPN ISP1 (VIVO): fechar sintomas novos enquanto causa ativa | disabled |
| 46 | SPO VPN ISP1 (VIVO): fechar sintomas ja abertos ao disparar causa | enabled |

## Dados consultados

| Método | Artefato |
| --- | --- |
| host.get groupids FW | `backups/audit_fw_hosts_enabled_20261001.json` |
| problem.get hostids FW | `backups/audit_all_fw_open_problems_with_cause_20261001.json` |
| correlation.get | `backups/audit_report_correlations_20261001.json` |

## Próximos passos

1. Agendar rank worker no servidor Capri.
2. Manter piloto 16/45 off até haver observação controlada.
3. Tratar 4 roots independentes (lan2/lan3/dmz/az-to-oci) via `zabbix-senior-analyst`.
4. Após recuperação da Vivo, validar fechamento em cascata dos sintomas.
