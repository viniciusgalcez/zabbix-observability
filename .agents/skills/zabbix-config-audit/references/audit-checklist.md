# Checklist de auditoria — método, filtro e o que conta como achado

Todas as chamadas usam o MCP `zabbix` (`zabbix_api`). Use `zabbix_api_list` e `zabbix_api_docs` se precisar confirmar parâmetros de um método antes de chamar — não adivinhe nomes de campo.

Rode apenas os blocos relevantes ao escopo pedido pelo usuário (site, categoria, ou tudo). Para ambientes grandes, sempre pagine (`output`, `limit` quando disponível) em vez de puxar tudo de uma vez sem necessidade.

## 1. Itens não suportados

```
item.get(output=["itemid","name","key_","status","state","error","lastclock"], filter={"state": 1})
```
`state=1` é "not supported". Agrupe por host e por padrão de erro (`error`). **Achado real:** item unsupported há mais de ~1 dia sem explicação conhecida (cruzar com `best-practices.md` para ver se já é um caso documentado). Não repita como novidade um item que o runbook já rastreia — cite o plano existente.

## 2. Problemas sem reconhecimento

```
problem.get(output="extend", acknowledged=false, recent=false, sortfield="eventid", sortorder="DESC")
```
Cruze contagem total vs. reconhecidos. **Achado real:** proporção alta de não reconhecidos acumulando ao longo de dias/semanas (não apenas "há problemas abertos agora", que é estado normal de qualquer ambiente).

## 3. Hosts sem template

```
host.get(output=["hostid","host","name"], selectParentTemplates=["templateid","name"], selectGroups=["name"])
```
Filtre onde `parentTemplates` está vazio. Cruze o grupo do host contra a exceção documentada (Monitoramento Web, um host de banco) antes de reportar como achado.

## 4. Interfaces SNMP desatualizadas

```
hostinterface.get(output="extend", filter={"type": 2})
```
Campo `details.version` indica 1/2/3. **Achado:** `version` 1 ou 2 num host cujo tipo de equipamento (grupo) tipicamente suporta v3 (switches Cisco, APs Aruba, iDRAC, QNAP — ver templates documentados). UPS costuma ficar em v2c por padrão do fabricante — isso não é achado a menos que o UPS específico já tenha suporte a v3 confirmado.

## 5. Discovery e fila de classificação

```
drule.get(output="extend", selectDChecks="extend")
host.get(output=["hostid","host"], groupids=[<id do grupo "Em Classificação">])
```
**Achado:** fila de "Em Classificação" com hosts há muito tempo (`host.get` com `selectInventory` ou cruzando `dhosts`/`dservices` para ver `lastup`). Também verifique `drule.get` para `status` (regra pausada sem querer) e `delay` (regras devem rodar; se o intervalo ficou muito longo por engano em algum ajuste manual, sinalize).

## 6. Duplicidade de triggers/ações equivalentes

```
trigger.get(output=["triggerid","description","expression"], selectHosts=["host"], search={"description": "<termo>"})
action.get(output="extend", selectOperations="extend", selectFilter="extend")
```
Ao investigar uma trigger específica, sempre busque por descrição/chave similar no mesmo host e no template antes de concluir que ela é única. Duas triggers com expressões equivalentes para o mesmo item é o padrão de "ruído duplicado" do best-practices.md.

## 7. Certificados SSL e monitoramento web

```
httptest.get(output="extend", selectSteps="extend")
```
Verifique se cada cenário com verificação de certificado tem os dois limiares (aviso ~30 dias, crítico ~7 dias) — comparar com a tabela já documentada em `docs/dashboard-ricoh-impressao.md`-style e no relatório da 4Linux (8 domínios com essa política). **Achado:** domínio monitorado sem verificação de certificado, ou com só um dos dois limiares.

## 8. Tags de escopo (`scope=capacity` vs `scope=availability`)

```
trigger.get(output=["triggerid","description"], selectTags="extend", tags=[{"tag":"scope","operator":0,"value":"capacity"}])
```
Cruze o resultado buscando triggers que tenham **ambas** as tags de scope simultaneamente — isso é precisamente o bug já corrigido em 2026-09-25. Ver `best-practices.md` para o precedente exato antes de reportar.

## 9. Macros de host divergentes do padrão global

```
usermacro.get(output="extend", hostids=[...])
usermacro.get(output="extend", globalmacro=true)
```
Compare os valores por host contra a tabela global em `best-practices.md`. Divergência sem contexto óbvio (nome do host, tipo de aplicação) é Atenção, não Crítico — pode ser intencional.

## 10. Media types e ações de notificação

```
mediatype.get(output="extend")
action.get(output="extend", selectOperations="extend", selectFilter="extend", selectRecoveryOperations="extend")
```
Verifique se a ação tem **operação de recuperação** configurada (não só de problema) — uma ação sem `recoveryOperations` correspondente é a "recuperação assimétrica" do best-practices.md. Confirme também que a mídia de recuperação é a mesma da abertura (evita o caso documentado do Teams Incident Hub onde a recuperação usava mídia padrão em vez do webhook correto).
