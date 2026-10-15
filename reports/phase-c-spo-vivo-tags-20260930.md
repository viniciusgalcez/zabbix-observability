# Fase C — tags canônicas no piloto `spo.vivo.isp1`

Data: 30/09/2026

## O que foi aplicado

### Causa física `50308` (`SPO_VIVO`)

Tags finais:

- `link-id=spo.vivo.isp1` *(novo)*
- `carrier=vivo` *(novo)*
- `class=network` *(novo)*
- `component=wan-link` *(novo)*
- `link-cause=SPO_VIVO` *(mantido — correlações 16/17/45/46)*
- `notify=teams`, `notify=telegram`
- `scope=availability`, `service=internet`, `site=spo`, `link=ISP1`

Estado após update: `PROBLEM`, sem erro de avaliação.

### Agregado VPN `55144` (`SPO_ISP1_VPN`)

- `link-id=spo.vivo.isp1.vpn-agg` *(novo)*
- `carrier=vivo`, `class=network`, `component=vpn` *(novos)*
- `depends-on=SPO_VIVO` *(novo)*
- `notify=teams` **removido** (agregado deixa de autorizar Teams; resta `telegram`)
- `link-cause=SPO_ISP1_VPN` mantido
- Dependência de trigger para `50308` preservada

## Backups

- `backups/phase_c_spo_vivo_cause_before_tags_20260930.json`
- `backups/phase_c_export_spo_cpd_fw01_before_tags_20260930.json`
- Aplicação: `backups/phase_c_apply_tags_cause_50308_20260930.json`, `backups/phase_c_apply_tags_aggregate_55144_20260930.json`
- Verificação: `backups/phase_c_verify_spo_vivo_tags_after_20260930.json`

## Limitações conscientes

1. O evento aberto `18116214` **não muda as tags** até reabrir; tags de evento são fixadas na criação. Triggers novas já nascem com o contrato.
2. Sintomas descobertos (`flags=4`, ex. `High packets loss` `43231`/`43234`) ainda usam `depends-on=ISP1_VIVO` e **não têm** `scope=performance`. A API não deve editar instância LLD; isso vai no protótipo do template `FortiGate by SNMP` (próxima onda da Fase C).
3. `link-cause` permanece `SPO_VIVO` / `SPO_ISP1_VPN` até a migração das 59 correlações para `link-id` canônico.

## Aceite do piloto

- [x] Causa com `link-id`, `carrier`, `class`, `component`
- [x] `link-cause` legado preservado
- [x] Agregado sem `notify=teams`
- [x] Correlações 16/17/45/46 ativas
- [ ] Protótipos LLD com `scope=performance` e `depends-on` canônico — pendente

## Próximo

Fase D no mesmo piloto: confirmar que o Teams só notifica a causa `50308` (ação 22 + `notify=teams`), e depois onda de protótipos SD-WAN/VPN no template.
