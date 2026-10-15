# Ambiente Zabbix da Capricórnio

## Conexão e artefatos

- O MCP `zabbix` já está configurado no projeto com permissão de escrita.
- Não leia, copie ou mostre credenciais presentes nos arquivos de configuração.
- Execute lotes de chamadas por meio de `scripts/dashboard_mcp_session.py` usando arquivos em `zabbix-requests/`.
- Salve exports, snapshots anteriores e resultados de verificação em `backups/`, usando nomes com alvo, finalidade e data.
- Considere `.agents/AGENTS.md` parte obrigatória das regras locais.

## Convenções conhecidas

- O fluxo do Microsoft Teams usa uma ação e um tipo de mídia já existentes. Descubra os IDs atuais por API antes de modificar; não confie apenas em IDs históricos.
- A tag convencional para inclusão explícita no fluxo é `notify=teams`.
- O fluxo também pode incluir eventos por severidade. Sempre leia a fórmula atual de condições e as operações antes de concluir por que um evento foi ou não enviado.
- O envio de problema pode ser atrasado em cinco minutos para evitar flapping. Consulte `esc_period`, `operations`, passos e horário dos alerts.
- Datas exibidas ao usuário devem seguir `dd/MM/yyyy HH:mm:ss` e o fuso `America/Sao_Paulo`.
- Cartões do Teams devem ser objetivos, sem títulos repetidos como “INCIDENTE ATIVO” ou “RESOLVIDO” quando o estado já estiver claro pela cor e pelos campos.

## Restrições locais

- Métodos `delete` e `massdelete` podem estar bloqueados no MCP. Não tente burlar esse bloqueio.
- O computador do usuário não é o Zabbix Server. Não deixe processos, tarefas ou contêineres locais como parte da solução de produção.
- O ambiente contém proxies. Ao interpretar `nodata()`, considere atraso ou transferência histórica do proxy e confirme `state`, `error`, `lastclock` e `lastvalue` do item.
