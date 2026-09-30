# Fase B — classificação dos problemas abertos nos firewalls

Data: 30/09/2026

## Decisão de topologia

`BGPISP2_MTZISP1` e `SCLISP2_MTZISP1` permanecem sob `spo.vivo.isp1`.
Motivo: a matriz de correlação usa o prefixo `MTZISP1` (ponta na saída 1 da matriz),
e no incidente atual esses sintomas já acompanharam a queda da Vivo.

## Resumo

- Problemas abertos nos 7 firewalls: **57**
- Causa `spo.vivo.isp1`: **1**
- Sintomas já ranqueados sob Vivo: **50**
- Sintomas soltos candidatos: **0**
- Independentes de rede: **5**
- Outra causa: **1**
- Stale >24h (independentes/outra causa): **4**

## Ranker

Dry-run de `scripts/link_cause_rank_worker.py`: **0 candidatos**, **0 ambíguos**.
 Evidência: `backups/phase_b_link_cause_rank_dryrun_20260930.json`.
 Nenhum `event.acknowledge` adicional foi necessário.

## Independentes (não ranquear sob Vivo)

- `18379687` `SPO-CPD-FW01` — FortiGate: Interface dmz(): Link down (desde 29/09/2026 16:48:18, 18.9h, depends-on=``)
- `18379641` `SPO-CPD-FW01` — FortiGate: VPN SYSTEXTIL_W1: Tunnel down (desde 29/09/2026 16:47:44, 18.9h, depends-on=`SYSTEXTIL_W1`)
- `17498586` `BRAS-CPD-FW01` — FortiGate: Interface lan2(): Link down (desde 14/09/2026 16:16:17, 379.4h, depends-on=``)
- `17441868` `AZ-VM-FW-01` — FortiGate: VPN az-to-oci-vpn2: Tunnel down (desde 11/09/2026 12:43:20, 455.0h, depends-on=`az-to-oci-vpn2`)
- `17437418` `BRAS-CPD-FW01` — FortiGate: Interface lan3(ISP2-): Link down (desde 11/09/2026 06:59:18, 460.7h, depends-on=`ISP2-`)

## Stale >24h a documentar

- `17498586` `BRAS-CPD-FW01` — FortiGate: Interface lan2(): Link down (379.4h, classe `independente_rede`)
- `17441868` `AZ-VM-FW-01` — FortiGate: VPN az-to-oci-vpn2: Tunnel down (455.0h, classe `independente_rede`)
- `17437418` `BRAS-CPD-FW01` — FortiGate: Interface lan3(ISP2-): Link down (460.7h, classe `independente_rede`)
- `13501111` `BGP-CPD-FW01` — FortiGate: SD-WAN [HK_8.8.8.8]:[port3]: High packets loss (3215.5h, classe `sintoma_outra_causa`)

## Aceite da Fase B

- [x] Problemas classificados
- [x] Ranker dry-run sem pendência comprovada
- [x] Independentes documentados (não forçar sob Vivo)
- [x] Stale >24h listados para tratamento posterior (sem fechar às cegas)

Planilha: `reports/phase-b-classificacao-problemas-fw-20260930.csv`

## Próximo (Fase C)

Padronizar tags canônicas no piloto `spo.vivo.isp1` 
(`link-id=spo.vivo.isp1`, `depends-on` nos sintomas, `scope=performance` em loss).
