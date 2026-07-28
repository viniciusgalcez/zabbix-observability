# Reversão da correlação #4 (switch → AP) — 2026-07-27

Por decisão do Vinicius, a correlação de eventos deve ficar **só nos servidores**,
não em switches/APs. ("Em switch não precisa alterar, somente em servidores.")

## O que foi revertido
Todas as dependências switch → AP aplicadas foram removidas (triggers de AP
voltaram a `dependencies: []`):

- **BGP-EXP-SW03 → AP11-24** (28 triggers) — do commit `ef73c90`, revertido.
- **Lote parcial do resto** (46 triggers, switches BGP-ACA/ADM/CPD/EXP-SW01/POR/REV
  e primeiros do lote) — nunca chegou a ser commitado; revertido.

Total revertido: **74 triggers**. Validado por amostragem (todos `dependencies: []`).

Os outros ~76 triggers do plano do resto (arquivo
`correlacao-dep-switch-ap-resto-2026-07-27.json`) **nunca foram aplicados**.

## O que permanece (correlação de servidores — mantida)
- **#1** serviço depende de host-down: Docker, IIS ×3, MySQL, Apache (via protótipo).
- **Consolidação** dos 29 triggers de agent-down duplicados.

Os arquivos `correlacao-dep-switch-ap-2026-07-27.json` e
`correlacao-dep-switch-ap-resto-2026-07-27.json` ficam como registro histórico,
mas as mudanças que descrevem **não estão mais ativas** no Zabbix.
