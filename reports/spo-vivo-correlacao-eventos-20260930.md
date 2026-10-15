# SPO/Vivo — associação dos eventos em 30/09/2026

## Estado observado

- Host: `SPO-CPD-FW01` (`10758`).
- Causa física: evento `18116214`, trigger `50308`, `link-cause=SPO_VIVO`. A trigger estava em `PROBLEM`; os cinco health checks de `ISP1_VIVO` estavam em estado de falha. A interface `ISP1_VIVO` reportava estado operacional `2` (down).
- Causa agregada de VPN: evento `17779567`, trigger `55144`, `link-cause=SPO_ISP1_VPN`, também em `PROBLEM`.
- 36 problemas abertos no host. Os eventos `18379687` (dmz) e `18379641` (SYSTEXTIL_W1) não tinham vínculo comprovado com a saída Vivo.
- Correlações `16`, `17`, `45` e `46` já existiam e estavam ativas. As regras `16` e `45` fecham o evento novo; em condição persistente, isso pode gerar fechamento e reabertura repetidos.

## Alteração aplicada

Os 33 problemas comprovadamente ligados à saída Vivo, incluindo o evento agregado de VPN, foram classificados como sintomas da causa `18116214` usando `event.acknowledge` com `action=256` e `cause_eventid=18116214`. O backup imediatamente anterior está em `backups/backup_spo_vivo_33_symptoms_before_rank_20260930.json`.

## Validação

- `problem.get`: 33 problemas com `cause_eventid=18116214`; três causas independentes (`18116214`, `18379687`, `18379641`).
- As triggers `50308` e `55144` permanecem habilitadas, sem erro de avaliação e em `PROBLEM`.
- As correlações `16`, `17`, `45` e `46` permanecem habilitadas.
- A ação Teams `22` está habilitada com `esc_period=5m` e `pause_symptoms=1`. `alert.get` registrou envio bem-sucedido do evento raiz `18116214` pelo tipo de mídia Teams `53`.

## Limite e correção permanente

A classificação por `event.acknowledge` atua nos 33 eventos atuais. A correlação global nativa do Zabbix 7.0 oferece operações de fechar eventos, mas não uma operação de atribuir causa a novos sintomas. Ampliar a regra `45` enquanto ela usa `close_new` pode reproduzir a tempestade de eventos já observada. Os sintomas descobertos são herdados de protótipos do template FortiGate, e a API não permite adicionar dependências diretamente às instâncias descobertas. A solução permanente exige um desenho de dependências no nível de protótipos/host ou uma automação do lado do Zabbix que atribua a causa sem fechar os sintomas. Não foi criada uma correlação duplicada.

Referências: [event.acknowledge](https://www.zabbix.com/documentation/7.0/en/manual/api/reference/event/acknowledge), [correlação global](https://www.zabbix.com/documentation/7.0/en/manual/config/event_correlation/global), [dependências de trigger](https://www.zabbix.com/documentation/7.0/en/manual/config/triggers/dependencies).

## Reconciliação automática preparada em 30/09/2026

O arquivo `scripts/spo_vivo_rank_worker.py` consulta somente o host `10758` e exige uma única causa aberta da trigger `50308` com `link-cause=SPO_VIVO`. Ele atribui a essa causa apenas novos problemas da interface `ISP1_VIVO` identificada nas tags `interface` ou `sdwan-if`, além da trigger agregada `55144`. Não associa indiscriminadamente túneis de outros sites; a topologia de cada um ainda precisa ser comprovada. O programa falha sem alterar nada se a causa não estiver aberta ou estiver ambígua, ignora eventos anteriores à causa e salva o `problem.get` completo dos dois eventos imediatamente antes de cada `event.acknowledge`.

Foram executados dois testes de seleção e falha segura e uma consulta real em modo simulação. Uma passagem real subsequente encontrou zero eventos novos elegíveis. Na consulta de 30/09/2026 às 10:16 (Brasília), continuavam 36 problemas abertos: 33 sintomas vinculados à causa `18116214`, dois problemas independentes e a própria causa. As triggers `50308` e `55144` permaneciam em `PROBLEM`, sem erro de avaliação. O arquivo `backups/verify_spo_vivo_new_symptoms_live_20260930.json` guarda essa leitura. A leitura individual com `eventids`, tags e reconhecimentos também foi aceita pela API e está em `backups/verify_spo_vivo_rank_worker_event_reads_20260930.json`. Nenhuma configuração do Zabbix nem evento foi modificado nesta passagem.

### Implantação necessária para execução contínua

O programa foi preparado, mas **não está agendado nem implantado**. Para torná-lo permanente, execute-o em um servidor aprovado próximo ao Zabbix, com uma conta de API dedicada e de privilégio mínimo para consultar problemas e alterar a classificação de eventos do host SPO. Forneça `ZABBIX_URL` por HTTPS (HTTP só é aceito no loopback) e `ZABBIX_API_TOKEN` por mecanismo de segredo do servidor. Execute primeiro sem `--apply`, confira os IDs listados e só então use `--apply`. Agende a execução no servidor em intervalo de aproximadamente um minuto e preserve o diretório de backups. Não implantar na estação do usuário.

Critérios de aceite: abrir um evento de teste comprovadamente da interface `ISP1_VIVO` enquanto a causa estiver aberta; confirmar seu `cause_eventid` igual ao evento da causa; confirmar que o Teams envia apenas o alerta da causa após os cinco minutos; confirmar a recuperação da causa e que um problema independente (por exemplo, a VPN `SYSTEXTIL_W1`) não foi associado. Sem acesso ao servidor de execução e sem um token dedicado, estes testes ponta a ponta ainda não foram feitos.
