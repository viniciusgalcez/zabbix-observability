# Saúde de coleta (P0) — Zabbix 7

Alinhado à documentação oficial: itens unsupported, LLD unsupported e triggers
Unknown são **eventos internos** que devem ser visíveis e tratados na causa
(credencial, OID, plugin do agente, filtro LLD, macro) — não mascarados com
timeout global.

Referências oficiais:

- Internal events / notification on unsupported items
- Triggers → Unknown status (unsupported operand / evaluation error)
- LLD guidelines (filtrar para não criar unsupported; singleton pattern)
- Network device templates (OID numérico, filtrar ifAdminStatus down)

## 1. Contagens primeiro

```
item.get(countOutput=true, filter={state:1, status:0})          # unsupported enabled
item.get(countOutput=true, filter={state:1})                    # todos state=1
discoveryrule.get(countOutput=true, filter={state:1, status:0}) # LLD unsupported enabled
trigger.get(countOutput=true, filter={state:1, status:0})       # Unknown enabled
```

Se `countOutput` vier como string/número, use o valor. Se a listagem com
`limit` for menor que a contagem, **pagine por hostids**.

## 2. Itens unsupported enabled (lista completa)

Por lotes de hosts habilitados:

```
host.get(output=[hostid,host], filter={status:0})
item.get(
  hostids=[...batch...],
  output=[itemid,name,key_,error,lastclock,type,delay,status,state],
  filter={state:1, status:0},
  selectHosts=[host,name],
  templated=false
)
```

Agrupe por `host` e por prefixo de `error`.

| Padrão de erro | Interpretação típica | Severidade |
| --- | --- | --- |
| Timeout / partial data SNMP OID | SNMP lento, timeout curto, ou walk pesado demais | Atenção→Crítico se core |
| No Such Instance / No Such Object | OID/template não cabe neste firmware — filtrar LLD ou desabilitar | Atenção |
| Unknown metric `X` | Plugin/UserParameter/template load ausente no agente | Crítico se feature esperada |
| Invalid namespace / WMI | Feature Windows não instalada / namespace errado | Atenção |
| Value type mismatch (`"-2"` etc.) | Tipo do item errado ou valor sentinela do fabricante | Atenção |
| Cannot fetch / Access denied (DB) | Macro DSN/credencial | Crítico se DB em produção |
| `json: NaN` preprocessing | Prefail no preprocess — corrigir JS/regex | Atenção |

**Achado Crítico:** item enabled unsupported em host de produção sem plano
documentado em `best-practices.md` / runbook.

**Não é Crítico:** item `status=1` (disabled) ainda em state=1 — limpeza
histórica; reporte só contagem top hosts.

## 3. LLD unsupported

```
discoveryrule.get(
  output=[itemid,name,key_,status,state,error,lastclock,delay],
  filter={state:1},
  selectHosts=[host,name]
)
```

Filtre `status=0`. Casos Capri já vistos:

- `net.if.discovery` timeout parcial em switches → ajustar timeout SNMP **pontual**,
  filtros LLD, ou excluir interfaces problemáticas (não timeout global)
- `hyperv.discover.vms` Unknown metric → template Hyper-V sem loadable module no agente
- `mysql.*` com DSN placeholder `<Put your DSN>` → macro não configurada
- `perf_instance_en.discovery[PhysicalDisk]` localized name → OS em PT-BR / counters

Doc oficial: preferir LLD + filtros a itens estáticos que ficam unsupported.

## 4. Triggers Unknown

```
trigger.get(
  output=[triggerid,description,error,priority,state,status],
  filter={state:1, status:0},
  selectHosts=[host,name]
)
```

Sempre agrupe por host e por `error`. **Relacione à causa:** se o erro diz
`item is not supported`, o achado primário é o item/LLD — a trigger é cascata.

Ruído comum a **não** tratar como incidente de negócio:

- Processos do `Zabbix server` para coletores não usados (ipmi, java, vmware,
  report writer, connector) — desabilitar triggers/itens do template de server
  se o feature não está ligado (Informativo/Atenção de higiene)

## 5. Proxies (Zabbix 7)

```
proxy.get(output=[proxyid,name,operating_mode,lastaccess,version,compatibility,state,address,port])
```

| Campo | Achado |
| --- | --- |
| `lastaccess` > ~5 min | Proxy offline / rede — Crítico |
| `compatibility` ≠ current | Versão desalinhada do server — Atenção |
| `state` offline | Crítico |

## 6. Disponibilidade de interface

```
hostinterface.get(
  output=[interfaceid,hostid,type,ip,port,main,available,error,details],
  filter={available:2},
  selectHosts=[host,name,status]
)
```

`type`: 1=agent, 2=SNMP, 3=IPMI, 4=JMX. `available=2` = unavailable.

Também inventarie SNMP versions:

```
hostinterface.get(filter={type:2}, output=[...,details], selectHosts=[...])
```

`details.version`: 1 / 2 / 3. Achado se v1/v2 em Cisco/Aruba/iDRAC com suporte v3.
UPS v2c = OK por padrão.

## 7. Problemas de reachability

De `problem.get` (ou `event.get`), filtre nomes:

- `Unavailable by ICMP ping`
- `Zabbix agent is not available`
- `No SNMP data collection`
- `SNMP agent is unavailable`

Cite `eventid`, host, idade em dias, severidade.

## 8. Cascata e deduplicação no relatório

1. Liste unsupported / LLD primeiro
2. Triggers Unknown só como **efeito**, com contagem e top 10 hosts
3. Não triplique o mesmo OID timeout em item + LLD + trigger como três Críticos
   independentes — um achado raiz + menção à cascata

## 9. Artefatos sugeridos

```
zabbix-requests/audit_collection_p0_YYYYMMDD.json
backups/audit_unsupported_enabled_YYYYMMDD.json
backups/audit_lld_unsupported_YYYYMMDD.json
backups/audit_triggers_unknown_YYYYMMDD.json
backups/audit_proxies_YYYYMMDD.json
backups/audit_ifaces_unavailable_YYYYMMDD.json
```
