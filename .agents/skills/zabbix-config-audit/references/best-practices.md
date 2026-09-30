# Boas práticas — gerais e específicas deste ambiente

## Convenções gerais de Zabbix (aplicam-se a qualquer ambiente)

- **Template > host.** Regra, macro ou trigger que se repete em vários hosts pertence ao template (ou ao protótipo de descoberta), não a cada host individualmente. Corrigir um host isolado quando o problema é do template só adia o retrabalho.
- **Macro > valor hardcoded.** Limiares (`{$CPU.UTIL.CRIT}`, `{$DISK.PFREE.MIN.WARN}`, etc.) devem vir de macro — global por padrão, sobrescrita no host só quando aquele host tiver uma razão de negócio documentada para um limiar diferente. Um limiar diferente sem explicação é um achado, não uma curiosidade.
- **Um alerta por causa raiz.** Se duas triggers (ou uma trigger + uma dependência mal configurada) disparam para o mesmo sintoma, isso é ruído duplicado, não redundância de segurança. Prefira dependências e correlação a filtros só na camada de notificação (Teams/Telegram) — filtrar na saída esconde o sintoma, não corrige a causa.
- **Recuperação simétrica.** Toda trigger crítica deve fechar sozinha quando a condição normalizar. Uma trigger que só abre e nunca fecha automaticamente (ou que depende de reconhecimento manual para "resolver") é uma bandeira amarela.
- **SNMPv3 > SNMPv2c > SNMPv1**, quando o dispositivo suportar. v1/v2c em um dispositivo que aceita v3 é um achado de segurança, não só de padronização.
- **Discovery não é "fire and forget".** Hosts que caem em um grupo tipo "Em Classificação" (ou equivalente) e ficam ali por muito tempo indicam ou um dispositivo não identificado corretamente (ajustar a regra de classificação) ou um dispositivo que não deveria estar sendo monitorado (removê-lo da rede varrida). Uma fila de classificação crescendo sem revisão periódica é o achado — não o fato de existir uma fila.
- **Itens não suportados (`unsupported`) não são normais.** Um item unsupported por mais de alguns dias é sinal de credencial errada, OID inexistente, chave não suportada na plataforma, ou item que deveria ter sido desabilitado. Nunca é "esperado" sem uma causa raiz anotada.
- **Problemas sem reconhecimento acumulando** é sinal de que a fila perdeu dono, não que o ambiente está calmo. Uma alta proporção de problemas antigos não reconhecidos é sempre um achado de processo, mesmo que a severidade individual seja baixa.
- **Certificados SSL e itens de expiração** devem ter janela de aviso (tipicamente 30 dias) e crítica (tipicamente 7 dias) — um domínio monitorado sem as duas janelas é uma lacuna.
- **Backup antes de qualquer mutação.** Isso não é responsabilidade desta skill (que só lê), mas é a primeira pergunta a fazer antes de recomendar qualquer correção: "isso vai passar pelo runbook de backup?"

## Decisões já tomadas neste ambiente (não são achados — respeite-as)

Registradas na documentação do projeto e no vault Obsidian (`Projetos/Zabbix Observability/Operacao-e-Governanca.md`):

- **Correlação de eventos só em servidores.** Dependências switch→AP foram deliberadamente revertidas (decisão do responsável, 2026-07-27: "em switch não precisa alterar, somente em servidores"). Não recomende recriar essa correlação sem que o usuário peça — é uma escolha de produto, não uma lacuna.
- **`scope=capacity` e `scope=availability` são mutuamente exclusivos por design.** Um evento com as duas tags simultaneamente é o bug que já foi corrigido em 2026-09-25 (protótipos de filesystem Linux/Windows e trigger do Nextcloud). Se você encontrar essa combinação em algum outro trigger/protótipo, é uma recorrência do mesmo problema, não uma novidade — trate como Crítico e cite o precedente.
- **23 hosts sem template é uma exceção conhecida** (a maioria em "Monitoramento Web" e um em bancos de dados) — não é dívida técnica por padrão. Só é achado se um host específico *deveria* ter template e não tem (verifique o tipo do host antes de reportar).
- **A ação "Notificar MS Teams" usa lista fechada de triggers**, não filtro amplo por severidade/tag — decisão deliberada para evitar volume indevido, feita após o incidente do BGP-REV-AP01 (trigger `37785` incluído manualmente em 2026-09-09). Recomendar "trocar para filtro amplo" sem matriz aprovada é desalinhado com a decisão registrada — mencione a decisão antes de sugerir mudança nesse ponto.
- **`Timeout` de servidor/proxy/agente não deve ser alterado em massa** para eliminar itens *unsupported* — isso amplia o impacto sem corrigir a causa (regra explícita do runbook de remediação, 2026-09-09).
- **Itens não suportados específicos e suas causas raiz já diagnosticadas** (ver `docs/production-remediation-runbook-20260909.md`): `SPO-SRV-V07` (métricas `proc.mem`/`proc.cpu.util` não suportadas no Windows — substituir por `proc_info`/`perf_counter_en` após validação local), `SCL-ETE-TB01` (contadores `Processor Information` expirados), `BGP-SRV-VAPP10` (contadores IIS `HTTP Service Request Queues`/`APP_POOL_WAS` expirando). Se a auditoria encontrar esses mesmos itens ainda não suportados, cite que já há um plano documentado em vez de propor um novo do zero.

## Macros globais de limiar (referência rápida)

| Macro | Valor padrão | Observação |
| --- | --- | --- |
| `{$CPU.UTIL.CRIT}` | 90% | |
| `{$MEMORY.UTIL.MAX}` | 90% | |
| `{$IF.UTIL.MAX}` | 80% | |
| `{$DISK.PFREE.MIN.WARN}` / `{$DISK.PFREE.MIN.CRIT}` | 20% / 10% | |
| `{$UPS.BATTERY.CAPACITY.MIN.WARN}` | 40% | |
| `{$CERT.EXPIRY.WARN}` | 30 dias | |

Um host com macro própria sobrescrevendo uma dessas sem justificativa aparente (ex.: `{$CPU.UTIL.CRIT}=99` num host qualquer) é um achado de Atenção — pergunte ou sinalize, não assuma que é intencional.
