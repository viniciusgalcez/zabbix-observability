# Mapa de links e alertas — Fase A (30/09/2026)

Inventário canônico gerado a partir das triggers de causa/agregado, tags `depends-on` dos `Tunnel down` e da matriz de correlação.

- Planilha: `reports/mapa-links-alertas-canonico-20260930.csv`
- Circuitos mapeados: **23**
- Causas físicas: **11**
- Agregados VPN: **12**
- Tunnel downs inventariados: **82**

## Convenção `link-id`

`site.operadora.saida` para causa física; agregados usam sufixo `.vpn-agg` e apontam `parent_link_id`.

## Circuitos

### `bgp.crosscnt.isp1.vpn-agg` — BGP-CPD-FW01

- Tipo: `agregado_vpn`
- `link-cause` atual: `BGP_ISP1_VPN`
- Trigger: `55141` — BGP: tuneis VPN pela saida 1 (CROSSCONNECTION) instaveis
- Estado: `OK`
- Teams atual/desejado: `yes` / `no`
- Parent: `bgp.crosscnt.isp1`
- Correlações: 39:close_new, 40:close_old
- Itens da expressão:
  - SD-WAN [HK_SAOCARLOS]:[BGPISP1_SCLISP2]: Health check state
  - SD-WAN [SLA_AZURE]:[BGP_AZ_W1_W1]: Health check state
  - SD-WAN [HK_MATRIZ]:[BGPISP1_MTZISP2]: Health check state
  - SD-WAN [HK_MATRIZ]:[BGPISP1_MTZISP1]: Health check state
  - SD-WAN [SLA_BRAS]:[BGPISP1_BRAS-01]: Health check state
  - SD-WAN [HK_SAOCARLOS]:[BGPISP1_SCLISP1]: Health check state
  - SD-WAN [SLA_DENIM]:[VPN_DENIM-01]: Health check state
  - SD-WAN [SLA_SAOCARLOS_FIACAO]:[BGP_SCL_FIACAO1]: Health check state
- Prefixos `depends-on` (correlação): `AZ_BGP_W1_W1; BGP1; BGPISP1; BGP_AZ_W1; BGP_ISP1; BGP_SCL_FIACAO1; BGP_SCL_FIACAO_T1; CROSSCNT; VPN-BGP-01; VPN_BGP; VPN_DENIM-01`
- Túneis casados: **14**
  - `AZ-VM-FW-01` `AZ_BGP_W1_W1` (match `AZ_BGP_W1_W1`, OK)
  - `BGP-CPD-FW01` `BGPISP1_BRAS-01` (match `BGPISP1`, OK)
  - `BGP-CPD-FW01` `BGPISP1_MTZISP1` (match `BGPISP1`, PROBLEM)
  - `BGP-CPD-FW01` `BGPISP1_MTZISP2` (match `BGPISP1`, OK)
  - `BGP-CPD-FW01` `BGPISP1_SCLISP1` (match `BGPISP1`, OK)
  - `BGP-CPD-FW01` `BGPISP1_SCLISP2` (match `BGPISP1`, OK)
  - `BGP-CPD-FW01` `BGP_AZ_W1_W1` (match `BGP_AZ_W1`, OK)
  - `BGP-CPD-FW01` `BGP_SCL_FIACAO_T1` (match `BGP_SCL_FIACAO_T1`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BR-SCL-FIA-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BRAS-CPD-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `SCL-CPD-FW01` `SCLISP1_BGPISP1` (match `BGPISP1`, OK)
  - `SCL-CPD-FW01` `SCLISP2_BGPISP1` (match `BGPISP1`, OK)
  - `SPO-CPD-FW01` `BGP_SCL_FIACAO_T1` (match `BGP_SCL_FIACAO_T1`, PROBLEM)

### `bgp.vivo.isp2.vpn-agg` — BGP-CPD-FW01

- Tipo: `agregado_vpn`
- `link-cause` atual: `BGP_ISP2_VPN`
- Trigger: `55142` — BGP: tuneis VPN pela saida 2 (VIVO) instaveis
- Estado: `OK`
- Teams atual/desejado: `yes` / `no`
- Parent: `bgp.vivo.isp2`
- Correlações: 41:close_new, 42:close_old
- Itens da expressão:
  - SD-WAN [SLA_AZURE]:[BGP_AZ_W2_W1]: Health check state
  - SD-WAN [HK_SAOCARLOS]:[BGPISP2_SCLISP1]: Health check state
  - SD-WAN [SLA_BRAS]:[BGPISP2_BRAS-02]: Health check state
  - SD-WAN [HK_MATRIZ]:[BGPISP2_MTZISP1]: Health check state
  - SD-WAN [HK_SAOCARLOS]:[BGPISP2_SCLISP2]: Health check state
  - SD-WAN [HK_MATRIZ]:[BGPISP2_MTZISP2]: Health check state
  - SD-WAN [SLA_DENIM]:[VPN_DENIM-02]: Health check state
  - SD-WAN [SLA_SAOCARLOS_FIACAO]:[BGP_SCL_FIACAO2]: Health check state
- Prefixos `depends-on` (correlação): `AZ_BGP_W1_W2; BGP2; BGPISP2; BGP_AZ_W2; BGP_ISP2; BGP_SCL_FIACAO2; ISP2_VIVO; SYSTEXTIL1ISP2; SYSTEXTIL2ISP2; VPN-BGP-02; VPN_DENIM-02`
- Túneis casados: **17**
  - `AZ-VM-FW-01` `AZ_BGP_W1_W2` (match `AZ_BGP_W1_W2`, OK)
  - `BGP-CPD-FW01` `BGPISP2_BRAS-02` (match `BGPISP2`, OK)
  - `BGP-CPD-FW01` `BGPISP2_MTZISP1` (match `BGPISP2`, PROBLEM)
  - `BGP-CPD-FW01` `BGPISP2_MTZISP2` (match `BGPISP2`, OK)
  - `BGP-CPD-FW01` `BGPISP2_SCLISP1` (match `BGPISP2`, OK)
  - `BGP-CPD-FW01` `BGPISP2_SCLISP2` (match `BGPISP2`, OK)
  - `BGP-CPD-FW01` `BGP_SCL_FIACAO2` (match `BGP_SCL_FIACAO2`, OK)
  - `BGP-CPD-FW01` `SYSTEXTIL1ISP2` (match `SYSTEXTIL1ISP2`, OK)
  - `BGP-CPD-FW01` `SYSTEXTIL2ISP2` (match `SYSTEXTIL2ISP2`, OK)
  - `BGP-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BRAS-CPD-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `SCL-CPD-FW01` `SCLISP1_BGPISP2` (match `BGPISP2`, OK)
  - `SCL-CPD-FW01` `SCLISP2_BGPISP2` (match `BGPISP2`, OK)
  - `SCL-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `SPO-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)

### `bras.claro.isp1.vpn-agg` — BRAS-CPD-FW01

- Tipo: `agregado_vpn`
- `link-cause` atual: `BRAS_WAN1_VPN`
- Trigger: `55149` — BRAS: tuneis VPN pela saida 1 (CLARO) instaveis
- Estado: `OK`
- Teams atual/desejado: `yes` / `no`
- Parent: `bras.claro.isp1`
- Correlações: 57:close_new, 58:close_old
- Itens da expressão:
  - SD-WAN [SLA_BRAGANCA]:[VPN-BGP-01]: Health check state
  - SD-WAN [SLA_MATRIZ]:[VPN-MTZ-01]: Health check state
  - SD-WAN [SLA_SAOCARLOS]:[VPN-SCL-01]: Health check state
- Prefixos `depends-on` (correlação): `BRAS-01; ISP1-CLARO; VPN-BGP-01; VPN-MTZ-01; VPN-SCL-01; VPN_BGP; VPN_SCL; VPN_SPO; wan`
- Túneis casados: **14**
  - `BGP-CPD-FW01` `BGPISP1_BRAS-01` (match `BRAS-01`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BR-SCL-FIA-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BR-SCL-FIA-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BR-SCL-FIA-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BRAS-CPD-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BRAS-CPD-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BRAS-CPD-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `SCL-CPD-FW01` `SCLISP1_BRAS-01` (match `BRAS-01`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2` (match `VPN_SCL`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2_T1` (match `VPN_SCL`, OK)
  - `SPO-CPD-FW01` `MTZISP1_BRAS-01` (match `BRAS-01`, PROBLEM)

### `bras.isp2.vpn-agg` — BRAS-CPD-FW01

- Tipo: `agregado_vpn`
- `link-cause` atual: `BRAS_WAN2_VPN`
- Trigger: `55150` — BRAS: tuneis VPN pela saida 2 instaveis
- Estado: `OK`
- Teams atual/desejado: `yes` / `no`
- Correlações: 59:close_new, 60:close_old
- Itens da expressão:
  - SD-WAN [SLA_BRAGANCA]:[VPN-BGP-02]: Health check state
  - SD-WAN [SLA_MATRIZ]:[VPN-MTZ-02]: Health check state
  - SD-WAN [SLA_SAOCARLOS]:[VPN-SCL-02]: Health check state
- Prefixos `depends-on` (correlação): `BRAS-02; VPN-BGP-02; VPN-MTZ-02; VPN-SCL-02`
- Túneis casados: **12**
  - `BGP-CPD-FW01` `BGPISP2_BRAS-02` (match `BRAS-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `BRAS-CPD-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BRAS-CPD-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BRAS-CPD-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `SCL-CPD-FW01` `SCL2_BRAS-02` (match `BRAS-02`, OK)
  - `SPO-CPD-FW01` `MTZISP2_BRAS-02` (match `BRAS-02`, OK)

### `denim.algar.isp2.vpn-agg` — BR-DENIM-CAPRI-FW01

- Tipo: `agregado_vpn`
- `link-cause` atual: `DENIM_WAN2_VPN`
- Trigger: `55154` — DENIM: tuneis VPN pela saida 2 (ALGAR) instaveis
- Estado: `OK`
- Teams atual/desejado: `yes` / `no`
- Parent: `denim.algar.isp2`
- Correlações: 55:close_new, 56:close_old
- Itens da expressão:
  - SD-WAN [SLA_MATRIZ]:[VPN-MTZ-02]: Health check state
  - SD-WAN [SLA_SAOCARLOS]:[VPN-SCL-02]: Health check state
  - SD-WAN [SLA_BRAGANCA]:[VPN-BGP-02]: Health check state
- Prefixos `depends-on` (correlação): `ISP2-ALGAR; VPN-BGP-02; VPN-MTZ-02; VPN-SCL-02; VPN_DENIM-02; lan3`
- Túneis casados: **12**
  - `BGP-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `BRAS-CPD-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BRAS-CPD-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BRAS-CPD-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `SCL-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `SPO-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)

### `denim.flexus.isp1.vpn-agg` — BR-DENIM-CAPRI-FW01

- Tipo: `agregado_vpn`
- `link-cause` atual: `DENIM_WAN1_VPN`
- Trigger: `55153` — DENIM: tuneis VPN pela saida 1 (FLEXUS) instaveis
- Estado: `OK`
- Teams atual/desejado: `yes` / `no`
- Parent: `denim.flexus.isp1`
- Correlações: 53:close_new, 54:close_old
- Itens da expressão:
  - SD-WAN [SLA_SAOCARLOS]:[VPN-SCL-01]: Health check state
  - SD-WAN [SLA_BRAGANCA]:[VPN-BGP-01]: Health check state
  - SD-WAN [SLA_MATRIZ]:[VPN-MTZ-01]: Health check state
- Prefixos `depends-on` (correlação): `ISP1-FLEXUS; VPN-BGP-01; VPN-MTZ-01; VPN-SCL-01; VPN_BGP; VPN_DENIM-01; VPN_SCL; VPN_SPO; wan`
- Túneis casados: **11**
  - `BR-DENIM-CAPRI-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BR-SCL-FIA-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BR-SCL-FIA-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BR-SCL-FIA-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BRAS-CPD-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BRAS-CPD-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BRAS-CPD-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2` (match `VPN_SCL`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2_T1` (match `VPN_SCL`, OK)

### `fia.claro.isp1.vpn-agg` — BR-SCL-FIA-FW01

- Tipo: `agregado_vpn`
- `link-cause` atual: `FIA_WAN1_VPN`
- Trigger: `55151` — FIA: tuneis VPN pela saida 1 (CLARO DEDICADO) instaveis
- Estado: `OK`
- Teams atual/desejado: `yes` / `no`
- Parent: `fia.claro.isp1`
- Correlações: 49:close_new, 50:close_old
- Itens da expressão:
  - SD-WAN [SLA_SAOCARLOS]:[VPN-SCL-01]: Health check state
  - SD-WAN [SLA_BRAGANCA]:[VPN-BGP-01]: Health check state
  - SD-WAN [SLA_MATRIZ]:[VPN-MTZ-01]: Health check state
- Prefixos `depends-on` (correlação): `FIACAO1; ISP1-CLARO-DEDICADO; VPN-BGP-01; VPN-MTZ-01; VPN-SCL-01; VPN_BGP; VPN_SCL; VPN_SPO; wan`
- Túneis casados: **11**
  - `BR-DENIM-CAPRI-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BR-SCL-FIA-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BR-SCL-FIA-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BR-SCL-FIA-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BRAS-CPD-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BRAS-CPD-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BRAS-CPD-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2` (match `VPN_SCL`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2_T1` (match `VPN_SCL`, OK)

### `fia.claro.isp2.vpn-agg` — BR-SCL-FIA-FW01

- Tipo: `agregado_vpn`
- `link-cause` atual: `FIA_WAN2_VPN`
- Trigger: `55152` — FIA: tuneis VPN pela saida 2 (CLARO BANDA LARGA) instaveis
- Estado: `OK`
- Teams atual/desejado: `yes` / `no`
- Parent: `fia.claro.isp2`
- Correlações: 51:close_new, 52:close_old
- Itens da expressão:
  - SD-WAN [SLA_MATRIZ]:[VPN-MTZ-02]: Health check state
  - SD-WAN [SLA_SAOCARLOS]:[VPN-SCL-02]: Health check state
  - SD-WAN [SLA_BRAGANCA]:[VPN-BGP-02]: Health check state
- Prefixos `depends-on` (correlação): `BGP_SCL_FIACAO2; FIACAO2; ISP2-CLARO; SPO_SCL_FIACAO2; VPN-BGP-02; VPN-MTZ-02; VPN-SCL-02; VPN_SCL_FIACAO2; lan3`
- Túneis casados: **13**
  - `BGP-CPD-FW01` `BGP_SCL_FIACAO2` (match `BGP_SCL_FIACAO2`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `BRAS-CPD-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BRAS-CPD-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BRAS-CPD-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2` (match `VPN_SCL_FIACAO2`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2_T1` (match `VPN_SCL_FIACAO2`, OK)
  - `SPO-CPD-FW01` `SPO_SCL_FIACAO2` (match `SPO_SCL_FIACAO2`, OK)

### `scl.algar.isp2.vpn-agg` — SCL-CPD-FW01

- Tipo: `agregado_vpn`
- `link-cause` atual: `SCL_ISP2_VPN`
- Trigger: `55143` — SCL: tuneis VPN pela saida 2 (ALGAR) instaveis
- Estado: `OK`
- Teams atual/desejado: `yes` / `no`
- Parent: `scl.algar.isp2`
- Correlações: 43:close_new, 44:close_old
- Itens da expressão:
  - SD-WAN [SLA_AZURE]:[SCL_AZ_W2_W1]: Health check state
  - SD-WAN [HK_MATRIZ]:[SCLISP2_MTZISP1]: Health check state
  - SD-WAN [HK_MATRIZ]:[SCLISP2_MTZISP2]: Health check state
  - SD-WAN [HK_BRAGANCA]:[SCLISP2_BGPISP2]: Health check state
  - SD-WAN [HK_BRAGANCA]:[SCLISP2_BGPISP1]: Health check state
  - SD-WAN [SLA_BRAS]:[SCLISP2_BRAS-02]: Health check state
  - SD-WAN [SLA_DENIM]:[VPN_DENIM-02]: Health check state
  - SD-WAN [SLA_SAOCARLOS_FIACAO]:[VPN_SCL_FIACAO2]: Health check state
- Prefixos `depends-on` (correlação): `AZ_SCL_W1_W2; ISP2-ALGAR; ISP2_ALGAR; SCL2; SCLISP2; SCL_AZ_W2; VPN-SCL-02; VPN_DENIM-02; VPN_SCL_FIACAO2`
- Túneis casados: **16**
  - `AZ-VM-FW-01` `AZ_SCL_W1_W2` (match `AZ_SCL_W1_W2`, OK)
  - `BGP-CPD-FW01` `BGPISP1_SCLISP2` (match `SCLISP2`, OK)
  - `BGP-CPD-FW01` `BGPISP2_SCLISP2` (match `SCLISP2`, OK)
  - `BGP-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `BRAS-CPD-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `SCL-CPD-FW01` `SCL2_BRAS-02` (match `SCL2`, OK)
  - `SCL-CPD-FW01` `SCLISP2_BGPISP1` (match `SCLISP2`, OK)
  - `SCL-CPD-FW01` `SCLISP2_BGPISP2` (match `SCLISP2`, OK)
  - `SCL-CPD-FW01` `SCLISP2_MTZISP1` (match `SCLISP2`, OK)
  - `SCL-CPD-FW01` `SCLISP2_MTZISP2` (match `SCLISP2`, OK)
  - `SCL-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2` (match `VPN_SCL_FIACAO2`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2_T1` (match `VPN_SCL_FIACAO2`, OK)
  - `SPO-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)

### `scl.vivo.isp1.vpn-agg` — SCL-CPD-FW01

- Tipo: `agregado_vpn`
- `link-cause` atual: `SCL_ISP1_VPN`
- Trigger: `55133` — SCL: tuneis VPN pela saida 1 (VIVO) instaveis
- Estado: `OK`
- Teams atual/desejado: `yes` / `no`
- Parent: `scl.vivo.isp1`
- Correlações: 35:close_new, 36:close_old
- Itens da expressão:
  - SD-WAN [SLA_AZURE]:[SCL_AZ_W1_W1]: Health check state
  - SD-WAN [HK_MATRIZ]:[SCLISP1_MTZISP2]: Health check state
  - SD-WAN [HK_BRAGANCA]:[SCLISP1_BGPISP2]: Health check state
  - SD-WAN [HK_BRAGANCA]:[SCLISP1_BGPISP1]: Health check state
  - SD-WAN [HK_MATRIZ]:[SCLISP1_MTZISP1]: Health check state
  - SD-WAN [SLA_BRAS]:[SCLISP1_BRAS-01]: Health check state
  - SD-WAN [SLA_DENIM]:[VPN_DENIM-01]: Health check state
  - SD-WAN [SLA_SAOCARLOS_FIACAO]:[VPN_SCL_FIACAO1]: Health check state
- Prefixos `depends-on` (correlação): `AZ_SCL_W1_W1; FIACAO2_T1; HK_VIVO; ISP1_VIVO; P2MTZ; SCL1; SCLISP1; SCL_AZ_W1; VPN-SCL-01; VPN_DENIM-01; VPN_SCL; VPN_SCL_FIACAO1`
- Túneis casados: **22**
  - `AZ-VM-FW-01` `AZ_SCL_W1_W1` (match `AZ_SCL_W1_W1`, OK)
  - `BGP-CPD-FW01` `BGPISP1_SCLISP1` (match `SCLISP1`, OK)
  - `BGP-CPD-FW01` `BGPISP2_SCLISP1` (match `SCLISP1`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BR-SCL-FIA-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BRAS-CPD-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `SCL-CPD-FW01` `SCLISP1_BGPISP1` (match `SCLISP1`, OK)
  - `SCL-CPD-FW01` `SCLISP1_BGPISP2` (match `SCLISP1`, OK)
  - `SCL-CPD-FW01` `SCLISP1_BRAS-01` (match `SCLISP1`, OK)
  - `SCL-CPD-FW01` `SCLISP1_MTZISP1` (match `SCLISP1`, OK)
  - `SCL-CPD-FW01` `SCLISP1_MTZISP2` (match `SCLISP1`, OK)
  - `SCL-CPD-FW01` `SCL_AZ_W1_W1` (match `SCL_AZ_W1`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2` (match `VPN_SCL`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2_T1` (match `FIACAO2_T1`, OK)
  - `SPO-CPD-FW01` `P2MTZ1BGP1` (match `P2MTZ`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ1BGP2` (match `P2MTZ`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ1SCL1` (match `P2MTZ`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ1SCL2` (match `P2MTZ`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ2BGP1` (match `P2MTZ`, OK)
  - `SPO-CPD-FW01` `P2MTZ2BGP2` (match `P2MTZ`, OK)
  - … +2 túneis

### `spo.algar.isp2.vpn-agg` — SPO-CPD-FW01

- Tipo: `agregado_vpn`
- `link-cause` atual: `SPO_ISP2_VPN`
- Trigger: `55145` — SPO: tuneis VPN pela saida 2 (ALGAR) instaveis
- Estado: `OK`
- Teams atual/desejado: `yes` / `no`
- Parent: `spo.algar.isp2`
- Correlações: 47:close_new, 48:close_old
- Itens da expressão:
  - SD-WAN [SLA_MATRIZ_TO_AZURE]:[MTZ_AZ_W2_W1]: Health check state
  - SD-WAN [HK_SAOCARLOS]:[MTZISP2_SCLISP2]: Health check state
  - SD-WAN [HK_BRAGANCA]:[MTZISP2_BGPISP1]: Health check state
  - SD-WAN [HK_SAOCARLOS]:[MTZISP2_SCLISP1]: Health check state
  - SD-WAN [HK_BRAGANCA]:[MTZISP2_BGPISP2]: Health check state
  - SD-WAN [SLA_DENIM]:[VPN_DENIM-02]: Health check state
  - SD-WAN [SLA_BRAS]:[MTZISP2_BRAS-02]: Health check state
  - SD-WAN [SLA_SAOCARLOS_FIACAO]:[SPO_SCL_FIACAO2]: Health check state
- Prefixos `depends-on` (correlação): `AZ_MTZ_W1_W2; ISP2_ALGAR; MTZISP2; MTZ_AZ_W2; P2MTZ2; SPO_ALGAR; SPO_SCL_FIACAO2; SYSTEXTIL; VPN-MTZ-02; VPN_DENIM-02`
- Túneis casados: **25**
  - `AZ-VM-FW-01` `AZ_MTZ_W1_W2` (match `AZ_MTZ_W1_W2`, OK)
  - `BGP-CPD-FW01` `BGPISP1_MTZISP2` (match `MTZISP2`, OK)
  - `BGP-CPD-FW01` `BGPISP2_MTZISP2` (match `MTZISP2`, OK)
  - `BGP-CPD-FW01` `SYSTEXTIL1ISP1` (match `SYSTEXTIL`, OK)
  - `BGP-CPD-FW01` `SYSTEXTIL1ISP2` (match `SYSTEXTIL`, OK)
  - `BGP-CPD-FW01` `SYSTEXTIL2ISP1` (match `SYSTEXTIL`, OK)
  - `BGP-CPD-FW01` `SYSTEXTIL2ISP2` (match `SYSTEXTIL`, OK)
  - `BGP-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BRAS-CPD-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `SCL-CPD-FW01` `SCLISP1_MTZISP2` (match `MTZISP2`, OK)
  - `SCL-CPD-FW01` `SCLISP2_MTZISP2` (match `MTZISP2`, OK)
  - `SCL-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `SPO-CPD-FW01` `MTZISP2_BRAS-02` (match `MTZISP2`, OK)
  - `SPO-CPD-FW01` `P2MTZ2BGP1` (match `P2MTZ2`, OK)
  - `SPO-CPD-FW01` `P2MTZ2BGP2` (match `P2MTZ2`, OK)
  - `SPO-CPD-FW01` `P2MTZ2SCL1` (match `P2MTZ2`, OK)
  - `SPO-CPD-FW01` `P2MTZ2SCL2` (match `P2MTZ2`, OK)
  - `SPO-CPD-FW01` `SPO_SCL_FIACAO2` (match `SPO_SCL_FIACAO2`, OK)
  - … +5 túneis

### `spo.vivo.isp1.vpn-agg` — SPO-CPD-FW01

- Tipo: `agregado_vpn`
- `link-cause` atual: `SPO_ISP1_VPN`
- Trigger: `55144` — SPO: tuneis VPN pela saida 1 (VIVO) instaveis
- Estado: `PROBLEM`
- Teams atual/desejado: `yes` / `no`
- Parent: `spo.vivo.isp1`
- Correlações: 45:close_new, 46:close_old
- Itens da expressão:
  - SD-WAN [HK_BRAGANCA]:[MTZISP1_BGPISP2]: Health check state
  - SD-WAN [HK_SAOCARLOS]:[MTZISP1_SCLISP1]: Health check state
  - SD-WAN [SLA_MATRIZ_TO_AZURE]:[MTZ_AZ_W1_W1]: Health check state
  - SD-WAN [HK_SAOCARLOS]:[MTZISP1_SCLISP2]: Health check state
  - SD-WAN [HK_BRAGANCA]:[MTZISP1_BGPISP1]: Health check state
  - SD-WAN [SLA_DENIM]:[VPN_DENIM-01]: Health check state
  - SD-WAN [SLA_BRAS]:[MTZISP1_BRAS-01]: Health check state
  - SD-WAN [SLA_SAOCARLOS_FIACAO]:[SPO_SCL_FIACAO1]: Health check state
- Prefixos `depends-on` (correlação): `AZ_MTZ_W1; AZ_MTZ_W1_W1; BGP_SCL_FIACAO_T1; ISP1-VIVO; ISP1_VIVO; MTZISP1; MTZ_AZ_W1; P2MTZ1; SPO_SCL_FIACAO1; VPN-MTZ-01; VPN_DENIM-01; VPN_SPO`
- Túneis casados: **16**
  - `AZ-VM-FW-01` `AZ_MTZ_W1` (match `AZ_MTZ_W1`, PROBLEM)
  - `BGP-CPD-FW01` `BGPISP1_MTZISP1` (match `MTZISP1`, PROBLEM)
  - `BGP-CPD-FW01` `BGPISP2_MTZISP1` (match `MTZISP1`, PROBLEM)
  - `BGP-CPD-FW01` `BGP_SCL_FIACAO_T1` (match `BGP_SCL_FIACAO_T1`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BR-SCL-FIA-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BRAS-CPD-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `SCL-CPD-FW01` `SCLISP1_MTZISP1` (match `MTZISP1`, OK)
  - `SCL-CPD-FW01` `SCLISP2_MTZISP1` (match `MTZISP1`, OK)
  - `SPO-CPD-FW01` `BGP_SCL_FIACAO_T1` (match `BGP_SCL_FIACAO_T1`, PROBLEM)
  - `SPO-CPD-FW01` `MTZISP1_BRAS-01` (match `MTZISP1`, PROBLEM)
  - `SPO-CPD-FW01` `MTZ_AZ_W1_W1` (match `MTZ_AZ_W1`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ1BGP1` (match `P2MTZ1`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ1BGP2` (match `P2MTZ1`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ1SCL1` (match `P2MTZ1`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ1SCL2` (match `P2MTZ1`, PROBLEM)

### `bgp.crosscnt.isp1` — BGP-CPD-FW01

- Tipo: `causa_link`
- `link-cause` atual: `BGP_ISP1`
- Trigger: `47636` — BGP: Link HK_ISP1 (CROSSCNT) DOWN
- Estado: `OK`
- Teams atual/desejado: `yes` / `teams`
- Correlações: 7:close_new, 20:close_old, 39:close_new, 40:close_old
- Itens da expressão:
  - SD-WAN [HK_Systextil_Web]:[ISP1_CROSSCNT]: Health check state
  - SD-WAN [HK_ISP1]:[ISP1_CROSSCNT]: Health check state
  - SD-WAN [SLA_INTERNET]:[ISP1_CROSSCNT]: Health check state
  - SD-WAN [HK_ SynergyRH]:[ISP1_CROSSCNT]: Health check state
- Prefixos `depends-on` (correlação): `AZ_BGP_W1_W1; BGP1; BGPISP1; BGP_AZ_W1; BGP_ISP1; BGP_SCL_FIACAO1; BGP_SCL_FIACAO_T1; CROSSCNT; VPN-BGP-01; VPN_BGP; VPN_DENIM-01`
- Túneis casados: **14**
  - `AZ-VM-FW-01` `AZ_BGP_W1_W1` (match `AZ_BGP_W1_W1`, OK)
  - `BGP-CPD-FW01` `BGPISP1_BRAS-01` (match `BGPISP1`, OK)
  - `BGP-CPD-FW01` `BGPISP1_MTZISP1` (match `BGPISP1`, PROBLEM)
  - `BGP-CPD-FW01` `BGPISP1_MTZISP2` (match `BGPISP1`, OK)
  - `BGP-CPD-FW01` `BGPISP1_SCLISP1` (match `BGPISP1`, OK)
  - `BGP-CPD-FW01` `BGPISP1_SCLISP2` (match `BGPISP1`, OK)
  - `BGP-CPD-FW01` `BGP_AZ_W1_W1` (match `BGP_AZ_W1`, OK)
  - `BGP-CPD-FW01` `BGP_SCL_FIACAO_T1` (match `BGP_SCL_FIACAO_T1`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BR-SCL-FIA-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BRAS-CPD-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `SCL-CPD-FW01` `SCLISP1_BGPISP1` (match `BGPISP1`, OK)
  - `SCL-CPD-FW01` `SCLISP2_BGPISP1` (match `BGPISP1`, OK)
  - `SPO-CPD-FW01` `BGP_SCL_FIACAO_T1` (match `BGP_SCL_FIACAO_T1`, PROBLEM)

### `bgp.vivo.isp2` — BGP-CPD-FW01

- Tipo: `causa_link`
- `link-cause` atual: `BGP_ISP2`
- Trigger: `47620` — BGP: Link HK_ISP2 (VIVO) DOWN
- Estado: `OK`
- Teams atual/desejado: `yes` / `teams`
- Correlações: 3:close_new, 21:close_old, 41:close_new, 42:close_old
- Itens da expressão:
  - SD-WAN [HK_ SynergyRH]:[ISP2_VIVO]: Health check state
  - SD-WAN [SLA_INTERNET]:[ISP2_VIVO]: Health check state
  - SD-WAN [HK_Systextil_Web]:[ISP2_VIVO]: Health check state
  - SD-WAN [HK_ISP2]:[ISP2_VIVO]: Health check state
- Prefixos `depends-on` (correlação): `AZ_BGP_W1_W2; BGP2; BGPISP2; BGP_AZ_W2; BGP_ISP2; BGP_SCL_FIACAO2; ISP2_VIVO; SYSTEXTIL1ISP2; SYSTEXTIL2ISP2; VPN-BGP-02; VPN_DENIM-02`
- Túneis casados: **17**
  - `AZ-VM-FW-01` `AZ_BGP_W1_W2` (match `AZ_BGP_W1_W2`, OK)
  - `BGP-CPD-FW01` `BGPISP2_BRAS-02` (match `BGPISP2`, OK)
  - `BGP-CPD-FW01` `BGPISP2_MTZISP1` (match `BGPISP2`, PROBLEM)
  - `BGP-CPD-FW01` `BGPISP2_MTZISP2` (match `BGPISP2`, OK)
  - `BGP-CPD-FW01` `BGPISP2_SCLISP1` (match `BGPISP2`, OK)
  - `BGP-CPD-FW01` `BGPISP2_SCLISP2` (match `BGPISP2`, OK)
  - `BGP-CPD-FW01` `BGP_SCL_FIACAO2` (match `BGP_SCL_FIACAO2`, OK)
  - `BGP-CPD-FW01` `SYSTEXTIL1ISP2` (match `SYSTEXTIL1ISP2`, OK)
  - `BGP-CPD-FW01` `SYSTEXTIL2ISP2` (match `SYSTEXTIL2ISP2`, OK)
  - `BGP-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BRAS-CPD-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `SCL-CPD-FW01` `SCLISP1_BGPISP2` (match `BGPISP2`, OK)
  - `SCL-CPD-FW01` `SCLISP2_BGPISP2` (match `BGPISP2`, OK)
  - `SCL-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `SPO-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)

### `bras.claro.isp1` — BRAS-CPD-FW01

- Tipo: `causa_link`
- `link-cause` atual: `BRAS_ISP1`
- Trigger: `54333` — BRAS: Saida de internet 1 (CLARO) sem conectividade
- Estado: `OK`
- Teams atual/desejado: `yes` / `teams`
- Correlações: 24:close_new, 33:close_new, 34:close_old, 57:close_new, 58:close_old
- Itens da expressão:
  - SD-WAN [HK_SYSTEXTIL]:[wan]: Health check state
  - SD-WAN [HK_ISP1]:[wan]: Health check state
  - SD-WAN [HK_8.8.8.8]:[wan]: Health check state
- Prefixos `depends-on` (correlação): `BRAS-01; ISP1-CLARO; VPN-BGP-01; VPN-MTZ-01; VPN-SCL-01; VPN_BGP; VPN_SCL; VPN_SPO; wan`
- Túneis casados: **14**
  - `BGP-CPD-FW01` `BGPISP1_BRAS-01` (match `BRAS-01`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BR-SCL-FIA-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BR-SCL-FIA-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BR-SCL-FIA-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BRAS-CPD-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BRAS-CPD-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BRAS-CPD-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `SCL-CPD-FW01` `SCLISP1_BRAS-01` (match `BRAS-01`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2` (match `VPN_SCL`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2_T1` (match `VPN_SCL`, OK)
  - `SPO-CPD-FW01` `MTZISP1_BRAS-01` (match `BRAS-01`, PROBLEM)

### `denim.algar.isp2` — BR-DENIM-CAPRI-FW01

- Tipo: `causa_link`
- `link-cause` atual: `DENIM_ISP2`
- Trigger: `54451` — DENIM: Saida de internet 2 (ALGAR) sem conectividade
- Estado: `OK`
- Teams atual/desejado: `yes` / `teams`
- Correlações: 19:close_new, 25:close_new, 26:close_old, 55:close_new, 56:close_old
- Itens da expressão:
  - SD-WAN [HK_ISP2]:[lan3]: Health check state
  - SD-WAN [HK_8.8.8.8]:[lan3]: Health check state
- Prefixos `depends-on` (correlação): `ISP2-ALGAR; VPN-BGP-02; VPN-MTZ-02; VPN-SCL-02; VPN_DENIM-02; lan3`
- Túneis casados: **12**
  - `BGP-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `BRAS-CPD-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BRAS-CPD-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BRAS-CPD-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `SCL-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `SPO-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)

### `denim.flexus.isp1` — BR-DENIM-CAPRI-FW01

- Tipo: `causa_link`
- `link-cause` atual: `DENIM_ISP1`
- Trigger: `54452` — DENIM: Saida de internet 1 (FLEXUS) sem conectividade
- Estado: `OK`
- Teams atual/desejado: `yes` / `teams`
- Correlações: 18:close_new, 27:close_new, 28:close_old, 53:close_new, 54:close_old
- Itens da expressão:
  - SD-WAN [HK_8.8.8.8]:[wan]: Health check state
  - SD-WAN [HK_ISP1]:[wan]: Health check state
- Prefixos `depends-on` (correlação): `ISP1-FLEXUS; VPN-BGP-01; VPN-MTZ-01; VPN-SCL-01; VPN_BGP; VPN_DENIM-01; VPN_SCL; VPN_SPO; wan`
- Túneis casados: **11**
  - `BR-DENIM-CAPRI-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BR-SCL-FIA-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BR-SCL-FIA-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BR-SCL-FIA-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BRAS-CPD-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BRAS-CPD-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BRAS-CPD-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2` (match `VPN_SCL`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2_T1` (match `VPN_SCL`, OK)

### `fia.claro.isp1` — BR-SCL-FIA-FW01

- Tipo: `causa_link`
- `link-cause` atual: `FIA_ISP1`
- Trigger: `54332` — FIA: Saida de internet 1 (CLARO DEDICADO) sem conectividade
- Estado: `OK`
- Teams atual/desejado: `yes` / `teams`
- Correlações: 22:close_new, 29:close_new, 30:close_old, 49:close_new, 50:close_old
- Itens da expressão:
  - SD-WAN [HK_8.8.8.8]:[wan]: Health check state
  - SD-WAN [HK_ISP1]:[wan]: Health check state
- Prefixos `depends-on` (correlação): `FIACAO1; ISP1-CLARO-DEDICADO; VPN-BGP-01; VPN-MTZ-01; VPN-SCL-01; VPN_BGP; VPN_SCL; VPN_SPO; wan`
- Túneis casados: **11**
  - `BR-DENIM-CAPRI-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BR-SCL-FIA-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BR-SCL-FIA-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BR-SCL-FIA-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BRAS-CPD-FW01` `VPN_BGP` (match `VPN_BGP`, OK)
  - `BRAS-CPD-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BRAS-CPD-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2` (match `VPN_SCL`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2_T1` (match `VPN_SCL`, OK)

### `fia.claro.isp2` — BR-SCL-FIA-FW01

- Tipo: `causa_link`
- `link-cause` atual: `FIA_ISP2`
- Trigger: `54334` — FIA: Saida de internet 2 (CLARO BANDA LARGA) sem conectividade
- Estado: `OK`
- Teams atual/desejado: `yes` / `teams`
- Correlações: 23:close_new, 31:close_new, 32:close_old, 51:close_new, 52:close_old
- Itens da expressão:
  - SD-WAN [HK_ISP2]:[lan3]: Health check state
  - SD-WAN [HK_8.8.8.8]:[lan3]: Health check state
- Prefixos `depends-on` (correlação): `BGP_SCL_FIACAO2; FIACAO2; ISP2-CLARO; SPO_SCL_FIACAO2; VPN-BGP-02; VPN-MTZ-02; VPN-SCL-02; VPN_SCL_FIACAO2; lan3`
- Túneis casados: **13**
  - `BGP-CPD-FW01` `BGP_SCL_FIACAO2` (match `BGP_SCL_FIACAO2`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `BRAS-CPD-FW01` `VPN-BGP-02` (match `VPN-BGP-02`, OK)
  - `BRAS-CPD-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BRAS-CPD-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2` (match `VPN_SCL_FIACAO2`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2_T1` (match `VPN_SCL_FIACAO2`, OK)
  - `SPO-CPD-FW01` `SPO_SCL_FIACAO2` (match `SPO_SCL_FIACAO2`, OK)

### `scl.algar.isp2` — SCL-CPD-FW01

- Tipo: `causa_link`
- `link-cause` atual: `SCL_ALGAR`
- Trigger: `50307` — SCL: Link HK_ALGAR (ISP2_ALGAR) DOWN
- Estado: `OK`
- Teams atual/desejado: `yes` / `teams`
- Correlações: 14:close_new, 15:close_old, 43:close_new, 44:close_old
- Itens da expressão:
  - SD-WAN [SLA_INTERNET]:[ISP2_ALGAR]: Health check state
  - SD-WAN [HK_Systextil_Web]:[ISP2_ALGAR]: Health check state
  - SD-WAN [HK_ALGAR]:[ISP2_ALGAR]: Health check state
  - SD-WAN [GLPI]:[ISP2_ALGAR]: Health check state
  - SD-WAN [HK_Teams]:[ISP2_ALGAR]: Health check state
- Prefixos `depends-on` (correlação): `AZ_SCL_W1_W2; ISP2-ALGAR; ISP2_ALGAR; SCL2; SCLISP2; SCL_AZ_W2; VPN-SCL-02; VPN_DENIM-02; VPN_SCL_FIACAO2`
- Túneis casados: **16**
  - `AZ-VM-FW-01` `AZ_SCL_W1_W2` (match `AZ_SCL_W1_W2`, OK)
  - `BGP-CPD-FW01` `BGPISP1_SCLISP2` (match `SCLISP2`, OK)
  - `BGP-CPD-FW01` `BGPISP2_SCLISP2` (match `SCLISP2`, OK)
  - `BGP-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `BRAS-CPD-FW01` `VPN-SCL-02` (match `VPN-SCL-02`, OK)
  - `SCL-CPD-FW01` `SCL2_BRAS-02` (match `SCL2`, OK)
  - `SCL-CPD-FW01` `SCLISP2_BGPISP1` (match `SCLISP2`, OK)
  - `SCL-CPD-FW01` `SCLISP2_BGPISP2` (match `SCLISP2`, OK)
  - `SCL-CPD-FW01` `SCLISP2_MTZISP1` (match `SCLISP2`, OK)
  - `SCL-CPD-FW01` `SCLISP2_MTZISP2` (match `SCLISP2`, OK)
  - `SCL-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2` (match `VPN_SCL_FIACAO2`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2_T1` (match `VPN_SCL_FIACAO2`, OK)
  - `SPO-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)

### `scl.vivo.isp1` — SCL-CPD-FW01

- Tipo: `causa_link`
- `link-cause` atual: `HK_VIVO`
- Trigger: `50306` — SCL: Link HK_VIVO (ISP1_VIVO) DOWN
- Estado: `OK`
- Teams atual/desejado: `yes` / `teams`
- Correlações: 11:close_new, 12:close_old, 35:close_new, 36:close_old
- Itens da expressão:
  - SD-WAN [GLPI]:[ISP1_VIVO]: Health check state
  - SD-WAN [HK_VIVO]:[ISP1_VIVO]: Health check state
  - SD-WAN [HK_Teams]:[ISP1_VIVO]: Health check state
  - SD-WAN [HK_Systextil_Web]:[ISP1_VIVO]: Health check state
  - SD-WAN [SLA_INTERNET]:[ISP1_VIVO]: Health check state
- Prefixos `depends-on` (correlação): `AZ_SCL_W1_W1; FIACAO2_T1; HK_VIVO; ISP1_VIVO; P2MTZ; SCL1; SCLISP1; SCL_AZ_W1; VPN-SCL-01; VPN_DENIM-01; VPN_SCL; VPN_SCL_FIACAO1`
- Túneis casados: **22**
  - `AZ-VM-FW-01` `AZ_SCL_W1_W1` (match `AZ_SCL_W1_W1`, OK)
  - `BGP-CPD-FW01` `BGPISP1_SCLISP1` (match `SCLISP1`, OK)
  - `BGP-CPD-FW01` `BGPISP2_SCLISP1` (match `SCLISP1`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BR-SCL-FIA-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `BRAS-CPD-FW01` `VPN_SCL` (match `VPN_SCL`, OK)
  - `SCL-CPD-FW01` `SCLISP1_BGPISP1` (match `SCLISP1`, OK)
  - `SCL-CPD-FW01` `SCLISP1_BGPISP2` (match `SCLISP1`, OK)
  - `SCL-CPD-FW01` `SCLISP1_BRAS-01` (match `SCLISP1`, OK)
  - `SCL-CPD-FW01` `SCLISP1_MTZISP1` (match `SCLISP1`, OK)
  - `SCL-CPD-FW01` `SCLISP1_MTZISP2` (match `SCLISP1`, OK)
  - `SCL-CPD-FW01` `SCL_AZ_W1_W1` (match `SCL_AZ_W1`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2` (match `VPN_SCL`, OK)
  - `SCL-CPD-FW01` `VPN_SCL_FIACAO2_T1` (match `FIACAO2_T1`, OK)
  - `SPO-CPD-FW01` `P2MTZ1BGP1` (match `P2MTZ`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ1BGP2` (match `P2MTZ`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ1SCL1` (match `P2MTZ`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ1SCL2` (match `P2MTZ`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ2BGP1` (match `P2MTZ`, OK)
  - `SPO-CPD-FW01` `P2MTZ2BGP2` (match `P2MTZ`, OK)
  - … +2 túneis

### `spo.algar.isp2` — SPO-CPD-FW01

- Tipo: `causa_link`
- `link-cause` atual: `SPO_ALGAR`
- Trigger: `50305` — SPO: Link HK_ISP2 (ALGAR) DOWN
- Estado: `OK`
- Teams atual/desejado: `yes` / `teams`
- Correlações: 8:close_new, 13:close_old, 47:close_new, 48:close_old
- Itens da expressão:
  - SD-WAN [HK_TEAMS]:[ISP2_ALGAR]: Health check state
  - SD-WAN [HK_ SynergyRH]:[ISP2_ALGAR]: Health check state
  - SD-WAN [HK_Systextil_Web]:[ISP2_ALGAR]: Health check state
  - SD-WAN [sla_internet]:[ISP2_ALGAR]: Health check state
  - SD-WAN [HK_ISP2]:[ISP2_ALGAR]: Health check state
- Prefixos `depends-on` (correlação): `AZ_MTZ_W1_W2; ISP2_ALGAR; MTZISP2; MTZ_AZ_W2; P2MTZ2; SPO_ALGAR; SPO_SCL_FIACAO2; SYSTEXTIL; VPN-MTZ-02; VPN_DENIM-02`
- Túneis casados: **25**
  - `AZ-VM-FW-01` `AZ_MTZ_W1_W2` (match `AZ_MTZ_W1_W2`, OK)
  - `BGP-CPD-FW01` `BGPISP1_MTZISP2` (match `MTZISP2`, OK)
  - `BGP-CPD-FW01` `BGPISP2_MTZISP2` (match `MTZISP2`, OK)
  - `BGP-CPD-FW01` `SYSTEXTIL1ISP1` (match `SYSTEXTIL`, OK)
  - `BGP-CPD-FW01` `SYSTEXTIL1ISP2` (match `SYSTEXTIL`, OK)
  - `BGP-CPD-FW01` `SYSTEXTIL2ISP1` (match `SYSTEXTIL`, OK)
  - `BGP-CPD-FW01` `SYSTEXTIL2ISP2` (match `SYSTEXTIL`, OK)
  - `BGP-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BR-SCL-FIA-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `BRAS-CPD-FW01` `VPN-MTZ-02` (match `VPN-MTZ-02`, OK)
  - `SCL-CPD-FW01` `SCLISP1_MTZISP2` (match `MTZISP2`, OK)
  - `SCL-CPD-FW01` `SCLISP2_MTZISP2` (match `MTZISP2`, OK)
  - `SCL-CPD-FW01` `VPN_DENIM-02` (match `VPN_DENIM-02`, OK)
  - `SPO-CPD-FW01` `MTZISP2_BRAS-02` (match `MTZISP2`, OK)
  - `SPO-CPD-FW01` `P2MTZ2BGP1` (match `P2MTZ2`, OK)
  - `SPO-CPD-FW01` `P2MTZ2BGP2` (match `P2MTZ2`, OK)
  - `SPO-CPD-FW01` `P2MTZ2SCL1` (match `P2MTZ2`, OK)
  - `SPO-CPD-FW01` `P2MTZ2SCL2` (match `P2MTZ2`, OK)
  - `SPO-CPD-FW01` `SPO_SCL_FIACAO2` (match `SPO_SCL_FIACAO2`, OK)
  - … +5 túneis

### `spo.vivo.isp1` — SPO-CPD-FW01

- Tipo: `causa_link`
- `link-cause` atual: `SPO_VIVO`
- Trigger: `50308` — SPO: Link HK_ISP1 (VIVO) DOWN
- Estado: `PROBLEM`
- Teams atual/desejado: `yes` / `teams`
- Correlações: 16:close_new, 17:close_old, 45:close_new, 46:close_old
- Itens da expressão:
  - SD-WAN [sla_internet]:[ISP1_VIVO]: Health check state
  - SD-WAN [HK_ISP1]:[ISP1_VIVO]: Health check state
  - SD-WAN [HK_TEAMS]:[ISP1_VIVO]: Health check state
  - SD-WAN [HK_ SynergyRH]:[ISP1_VIVO]: Health check state
  - SD-WAN [HK_Systextil_Web]:[ISP1_VIVO]: Health check state
- Prefixos `depends-on` (correlação): `AZ_MTZ_W1; AZ_MTZ_W1_W1; BGP_SCL_FIACAO_T1; ISP1-VIVO; ISP1_VIVO; MTZISP1; MTZ_AZ_W1; P2MTZ1; SPO_SCL_FIACAO1; VPN-MTZ-01; VPN_DENIM-01; VPN_SPO`
- Túneis casados: **16**
  - `AZ-VM-FW-01` `AZ_MTZ_W1` (match `AZ_MTZ_W1`, PROBLEM)
  - `BGP-CPD-FW01` `BGPISP1_MTZISP1` (match `MTZISP1`, PROBLEM)
  - `BGP-CPD-FW01` `BGPISP2_MTZISP1` (match `MTZISP1`, PROBLEM)
  - `BGP-CPD-FW01` `BGP_SCL_FIACAO_T1` (match `BGP_SCL_FIACAO_T1`, OK)
  - `BR-DENIM-CAPRI-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BR-SCL-FIA-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `BRAS-CPD-FW01` `VPN_SPO` (match `VPN_SPO`, PROBLEM)
  - `SCL-CPD-FW01` `SCLISP1_MTZISP1` (match `MTZISP1`, OK)
  - `SCL-CPD-FW01` `SCLISP2_MTZISP1` (match `MTZISP1`, OK)
  - `SPO-CPD-FW01` `BGP_SCL_FIACAO_T1` (match `BGP_SCL_FIACAO_T1`, PROBLEM)
  - `SPO-CPD-FW01` `MTZISP1_BRAS-01` (match `MTZISP1`, PROBLEM)
  - `SPO-CPD-FW01` `MTZ_AZ_W1_W1` (match `MTZ_AZ_W1`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ1BGP1` (match `P2MTZ1`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ1BGP2` (match `P2MTZ1`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ1SCL1` (match `P2MTZ1`, PROBLEM)
  - `SPO-CPD-FW01` `P2MTZ1SCL2` (match `P2MTZ1`, PROBLEM)

## Lacunas remanescentes

1. `AZ-VM-FW-01` não tem causa `Saida de internet`; entra só como ponta VPN dos hubs.
2. `BRAS_WAN2_VPN` sem parent físico claro no inventário (carrier `unknown`).
3. Health-checks SD-WAN e `High packets loss` ainda não foram listados linha a linha neste CSV (só túneis `Tunnel down` + itens das causas).
4. Casos com `depends-on` vazio (`dmz`, `lan2`) ficam fora do casamento automático.

## Próximo passo (Fase B)

1. Revisar a tabela de `spo.vivo.isp1` (circuito ativo).
2. Confirmar se todos os túneis listados devem depender desse link.
3. Rodar `scripts/link_cause_rank_worker.py` contra a matriz preenchida.
4. Em seguida padronizar `notify=teams` só nas causas físicas (Fase D).
