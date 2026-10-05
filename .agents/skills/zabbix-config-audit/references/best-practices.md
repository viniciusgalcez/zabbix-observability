# Boas práticas — oficiais (Zabbix 7) + Capricórnio

## Da documentação oficial Zabbix

- **LLD primeiro.** Prefira discovery + filtros a dezenas de itens estáticos que
  viram unsupported em hosts diferentes (guidelines LLD / network templates).
- **Filtrar o que não existe.** Interfaces `ifAdminStatus=down`, loopback, OID
  ausente: filtre na LLD (ou singleton pattern) em vez de deixar item vermelho.
- **OID numérico em SNMP.** Templates oficiais de rede usam OID, não dependem de
  MIB carregada no server/proxy.
- **Macros de usuário** para limiares — templates oficiais e boa operação.
- **ICMP como base** em templates de rede (`Template ICMP Ping` / dependência).
- **Unsupported / Unknown / LLD unsupported são eventos internos.** A doc
  recomenda *Internal actions* para notificar quando item→unsupported,
  trigger→Unknown, LLD→unsupported. Sem isso, a dor aparece tarde.
- **Trigger Unknown** ocorre com operando unsupported ou erro de avaliação —
  trate a causa (item), não só silencie a trigger.
- **Não “consertar” unsupported com timeout global** do server/proxy/agent.

## Convenções gerais (qualquer ambiente)

- **Template > host.** Correção no host quando o problema é do template adia o retrabalho.
- **Macro > valor hardcoded.**
- **Um alerta por causa raiz.** Dependência / correlação / rank > filtro só no Teams.
- **Recuperação simétrica** (problema + recovery).
- **SNMPv3 > v2c > v1** quando o equipamento suportar.
- **Discovery com dono.** Fila “Em Classificação” sem revisão = achado de processo.
- **Unsupported enabled ≠ normal.** Sem causa anotada = achado.
- **Fila de problems sem ack** acumulando semanas = processo quebrado.
- **Certificados:** aviso ~30d e crítico ~7d.
- **Backup antes de mutação** (obrigação da skill de mudança, não desta).

## Decisões locais Capricórnio (não “desfaça” sem o usuário pedir)

- **Correlação switch→AP revertida** (2026-07-27): só servidores, não switches.
- **`scope=capacity` XOR `scope=availability`** — dual tag = bug (corrigido
  2026-09-25; recorrência = Crítico).
- **~22–23 hosts sem template** em Monitoramento Web (+ exceções) = conhecido,
  não dívida automática.
- **Teams (`action` Notificar MS Teams):** filtro `notify=teams` (tag),
  `esc_period=5m`, `pause_symptoms=1`, com recovery. Não sugerir “notificar
  tudo por severidade” sem matriz aprovada.
- **Piloto SPO Vivo:** correlações `close_new` **16** e **45** desabilitadas
  (anti-storm). Sintomas novos dependem de **rank**
  (`scripts/link_cause_rank_worker.py` + matriz
  `reports/link-correlation-matrix-*.csv`). Tratar 16/45 off como bug só se
  não houver rank periódico — aí o achado é “falta governança contínua”, não
  “reative close_new agora”.
- **Timeout em massa proibido** para limpar unsupported (runbook 2026-09-09).
- **Unsupported já diagnosticados** (`docs/production-remediation-runbook-20260909.md`):
  - `SPO-SRV-V07` — `proc.*` no Windows → `proc_info` / `perf_counter_en`
  - `SCL-ETE-TB01` — counters `Processor Information`
  - `BGP-SRV-VAPP10` — IIS `HTTP Service Request Queues` / AppPool (timeout)
  Cite o plano existente em vez de inventar outro.

## Achados recorrentes neste ambiente (checklist mental)

| Sintoma | Causa frequente |
| --- | --- |
| Muitos alertas FW “iguais” | Sintomas sem rank sob `link-cause` (ex. `SPO_VIVO`) |
| LLD `net.if.discovery` timeout | Walk SNMP pesado / OID lento no switch |
| `Unknown metric hyperv.*` | Template Hyper-V sem plugin no agente Windows |
| MySQL discovery DSN inválido | Macro `{$MYSQL.DSN}` placeholder |
| Toner `"-2"` numeric unsigned | Valor sentinela da impressora / tipo de item |
| Triggers Unknown no Zabbix server | Itens de coletores não usados (ipmi/java/vmware) |
| Problems info há 100+ dias (UPS lifetime) | Sem triagem / ack / desabilitar se inútil |

## Macros globais de limiar (referência)

| Macro | Padrão |
| --- | --- |
| `{$CPU.UTIL.CRIT}` | 90% |
| `{$MEMORY.UTIL.MAX}` | 90% |
| `{$IF.UTIL.MAX}` | 80% |
| `{$DISK.PFREE.MIN.WARN}` / `CRIT` | 20% / 10% |
| `{$UPS.BATTERY.CAPACITY.MIN.WARN}` | 40% |
| `{$CERT.EXPIRY.WARN}` | 30 dias |
| `{$SDWAN.HEALTH.IF.LOSS.WARN}` | 20 (template FortiGate) |

Host com override sem justificativa = Atenção.
