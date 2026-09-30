# Padrões de análise de dados coletados

Estas são consultas para responder perguntas sobre o que o Zabbix já coletou — não sobre a configuração em si. Use quando o usuário perguntar algo como "como está a tendência de disco no servidor X", "qual host gera mais alerta", "qual a disponibilidade do serviço Y este mês".

## Tendência de capacidade (disco, memória, CPU)

```
item.get(output=["itemid","name","key_","lastvalue","units"], hostids=[...], search={"key_": "vfs.fs.size"})
trend.get(itemids=[...], time_from=<epoch>, time_till=<epoch>, output="extend")
```
`history.get` para granularidade fina em janelas curtas (últimas horas/dias); `trend.get` (agregados horários min/avg/max) para janelas longas (semanas/meses) — não puxe `history.get` de 90 dias de um item de alta frequência, isso é caro e desnecessário quando `trend.get` já responde a pergunta de tendência.

Ao relatar tendência, dê a taxa de variação (ex.: "caiu de 35% livre para 22% livre em 30 dias") em vez de só o valor atual — é isso que torna a análise útil para prever quando vai estourar o limiar (`{$DISK.PFREE.MIN.WARN}`/`CRIT`).

## Ruído de alertas / eventos por host ou trigger

```
event.get(output="extend", time_from=<epoch>, time_till=<epoch>, source=0, object=0, sortfield="clock", sortorder="DESC")
```
Agrupe por `hostid`/`objectid` para achar os hosts/triggers que mais geraram eventos na janela. Cruze com `acknowledged` para separar "muito evento, mas resolvido rápido" de "muito evento, ninguém olha". Isso é o dado por trás de reportar redução de ruído (o painorama do projeto já documentou uma queda de ~25 alertas simultâneos para 1 após correlação — use o mesmo tipo de contagem para medir casos novos).

## Disponibilidade / SLA de serviço

```
service.get(output="extend", selectParents="extend", selectChildren="extend", selectProblemTags="extend")
sla.get(output="extend")
sla.getsli(slaid=<id>, period_from=<epoch>, period_to=<epoch>)
```
`sla.getsli` devolve o SLI (percentual de disponibilidade) por período — é a fonte correta para "qual foi o SLA do serviço X este mês", não uma contagem manual de eventos. Lembre-se do limite documentado: correções de tag (como a de `scope`) **não reescrevem histórico já fechado do SLA** — se o usuário perguntar por um mês que já teve o bug de classificação, o SLI daquele mês pode estar inflado por indisponibilidade que era na verdade capacidade; explique essa limitação em vez de tratar o número como absoluto.

## Contagem/distribuição por severidade

```
problem.get(output="extend", time_from=<epoch>, severities=[0,1,2,3,4,5])
```
Agrupe localmente por `severity` para responder "quantos eventos High/Disaster tivemos essa semana". Combine com `acknowledged` para o mesmo cruzamento de "visto vs. ignorado" do bloco de ruído acima.

## Boas práticas ao apresentar números

- Sempre diga o período exato consultado (from/to em `dd/MM/yyyy HH:mm`, fuso `America/Sao_Paulo` — convenção já usada no projeto).
- Não interpole ou estime valor para um item com `state=1` (unsupported) na janela — reporte a lacuna de dado em vez de preencher com zero ou com o último valor válido.
- Quando a pergunta envolver comparação com um baseline (ex.: "isso é normal?"), diga qual baseline você está usando (macro global, mesma métrica em outro host do mesmo tipo, ou período anterior) — nunca afirme "isso é anormal" sem um ponto de comparação explícito.
