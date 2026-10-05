# Checklist de auditoria — método, filtro e achado

Todas as chamadas: MCP `zabbix` (`zabbix_api`). Se params falharem (Zabbix 7),
use `zabbix_api_docs` — não invente campos.

Paginação: lotes de `hostids` (40–50) + `countOutput` para totais. `limit` sozinho
**não** prova completude.

Rode só os blocos do escopo. P0 está detalhado em [collection-health.md](collection-health.md).

---

## P0 — Coleta (obrigatório em full/coleta)

Ver [collection-health.md](collection-health.md): unsupported enabled, LLD,
triggers Unknown, proxies, interfaces unavailable, reachability.

---

## 1. Itens não suportados (resumo se P0 já rodou)

```
item.get(countOutput=true, filter={state:1, status:0})
item.get(hostids=[...], filter={state:1, status:0}, selectHosts=[host], output=[itemid,name,key_,error,lastclock])
```

**Achado:** enabled unsupported >0 sem plano no runbook. Disabled state=1 = Informativo (contagem).

## 2. Problemas abertos e fila antiga

```
problem.get(output=[eventid,name,severity,clock,acknowledged,cause_eventid], recent=true, selectTags=extend, limit=1000)
```

Calcule:

- roots (`cause_eventid` vazio/`0`) vs symptoms
- idade ≥7 dias nos roots
- proporção `acknowledged=0`

**Achado:** roots ≥7d acumulando (processo); symptoms órfãos quando existe
`link-cause` ativa (correlação/rank).

## 3. Hosts sem template

```
host.get(output=[hostid,host,name], selectParentTemplates=[templateid,name], selectGroups=[name], filter={status:0})
```

Exceção conhecida: maioria em *Monitoramento Web* (~21–23). Só reporte host que
**deveria** ter template (servidor/rede/UPS) e não tem.

## 4. Interfaces SNMP e versão

```
hostinterface.get(output=[interfaceid,hostid,ip,port,available,error,details], filter={type:2}, selectHosts=[host,name,status])
```

`details.version` ∈ {1,2,3}. Achado: v1/v2 em equipamento com suporte v3
(Cisco/Aruba/iDRAC). UPS v2c OK.

## 5. Discovery de rede e classificação

```
drule.get(output=[druleid,name,iprange,delay,status])
hostgroup.get(search={name:Classifica*}, selectHosts=[hostid,host])
```

**Achado:** regra enabled com `iprange` errado; fila Em Classificação envelhecida;
regra disabled sem querer.

## 6. Correlação de links (firewalls)

```
correlation.get(output=[correlationid,name,status], selectFilter=extend, selectOperations=extend)
problem.get(hostids=[FW...], output=[eventid,name,severity,clock,cause_eventid], selectTags=extend)
```

Grupos FW habituais: `27,28,29,30,31,98,99,100` (confirmar no ambiente).

Cruze com `reports/link-correlation-matrix-*.csv` e worker
`scripts/link_cause_rank_worker.py`.

| Situação | Achado |
| --- | --- |
| Correlações 16/45 `status=1` | Informativo se piloto anti-storm documentado; Atenção se sem rank periódico |
| Sintoma FW com `cause_eventid=0` enquanto root `link-cause=SPO_VIVO` aberto | Crítico operacional (falta rank) |
| Interface local (`dmz`/`lan2`) como "órfã" | Não forçar sob Vivo — validar se esperado |

## 7. Duplicidade de triggers / ações

```
trigger.get(output=[triggerid,description,expression], selectHosts=[host], search={description:<termo>})
action.get(output=extend, selectOperations=extend, selectFilter=extend, selectRecoveryOperations=extend, filter={eventsource:0})
```

Duas expressões equivalentes no mesmo item = ruído. Ação sem recovery = assimetria.

## 8. Web / SSL

```
httptest.get(output=[httptestid,name,status,verify_peer,verify_host,delay], selectSteps=[name,url], selectHosts=[host])
item.get(search={name:certificate|certificado|SSL|expir}, searchWildcardsEnabled=true, filter={status:0}, selectHosts=[host])
```

**Achado:** `verify_peer=0` em produção (Atenção segurança); domínio sem janelas
30d/7d de expiração; item cert unsupported.

## 9. Tags de escopo

```
problem.get / trigger.get com selectTags
```

Dual `scope=capacity` **e** `scope=availability` no mesmo objeto = Crítico
(recorrência do bug 2026-09-25).

## 10. Macros

```
usermacro.get(globalmacro=true)
usermacro.get(hostids=[...])
```

Compare com tabela em [best-practices.md](best-practices.md).

## 11. Media types, ações Teams e internal actions

```
mediatype.get(output=extend)
action.get(output=extend, selectFilter=extend, selectOperations=extend, selectRecoveryOperations=extend)
# eventsource: 0=trigger, 4=internal (confirmar na docs da versão)
```

Ação Capri atual esperada: `Notificar MS Teams` (id histórico 22) com
`notify=teams`, `esc_period≈5m`, `pause_symptoms=1`, recovery presente.

**Achado oficial:** ausência de *internal action* para Item/LLD unsupported ou
Trigger Unknown — a doc Zabbix recomenda notificar esses estados para não
descobrir coleta quebrada só quando o negócio reclama.

## 12. Proxies e server health

Ver P0. Opcional: problemas no host `Zabbix server` (housekeeper, queue, process
busy). Triggers Unknown de coletores não usados = higiene, não outage.

---

## Evidências

Salvar sempre em `backups/` + request em `zabbix-requests/` com data `YYYYMMDD`.
No relatório, listar métodos usados (seção Dados consultados).
