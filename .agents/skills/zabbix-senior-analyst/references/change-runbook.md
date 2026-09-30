# Runbook de mudança

## 1. Diagnóstico

Identifique host, template, interface, proxy, item, trigger, evento, ação e tipo de mídia envolvidos. Consulte objetos relacionados na mesma leitura quando possível. Para falha de coleta, compare `status`, `state`, `error`, `lastclock` e `lastvalue`.

Separe três estados:

- **Configuração:** objeto habilitado, expressão válida e herança correta.
- **Coleta:** item suportado e recebendo valores atuais.
- **Notificação:** evento elegível, ação correspondente, operação executada e alerta enviado.

## 2. Projeto da correção

Escolha uma métrica que represente o sintoma operacional. Modele recuperação determinística e trate erros de coleta. Para flapping, use uma janela de estabilidade adequada e dependências com a causa raiz.

Antes de criar um objeto, pesquise por nome, chave, expressão, host/template e tags. Se houver duas regras para o mesmo sintoma, mantenha a mais direta e confiável; desative a redundante após backup.

## 3. Backup

Faça o backup imediatamente antes da mutação. Um backup antigo de outra etapa não substitui o backup do estado atual.

- Hosts/templates: `configuration.export` com os IDs exatos.
- Dashboards: `dashboard.get` com páginas e widgets completos.
- Actions/media types/correlations/services: método `get` com saída completa e relacionamentos relevantes.

Não prossiga quando o backup falhar.

## 4. Aplicação

Use chamadas pequenas e idempotentes. Evite misturar mudanças independentes no mesmo lote. Preserve campos existentes que a API substitui integralmente, especialmente tags, operações, filtros, páginas e widgets.

Para rollout em massa:

1. registre a quantidade e os IDs afetados;
2. aplique em um representante;
3. valide coleta, problema e recuperação;
4. aplique ao conjunto restante;
5. compare a contagem final com o inventário inicial.

## 5. Verificação

Após a aplicação, confirme por API:

- o objeto existe uma única vez e está habilitado;
- o item está suportado e com valor atual;
- a trigger não possui erro de avaliação;
- o evento abre somente após a estabilidade definida;
- a recuperação fecha o mesmo incidente;
- `alert.get` registra o envio ao Teams sem erro e sem duplicidade.

Quando a verificação depender do tempo, aguarde somente o intervalo necessário e mantenha o usuário informado durante a espera.

## 6. Entrega

Informe o que mudou, por que resolveu, evidências do teste e qualquer comportamento ainda dependente de uma ação externa, como reconectar um recurso. Inclua links para os backups e arquivos de requisição relevantes.
