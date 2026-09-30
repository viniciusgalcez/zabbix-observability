---
name: zabbix-config-audit
description: Audita a configuração do Zabbix da Capricórnio contra boas práticas (hosts, templates, triggers, tags, discovery, SNMP, certificados) e analisa dados coletados (tendência de capacidade, ruído de alertas, SLA). Use sempre que o usuário pedir para revisar, avaliar, auditar ou "dar uma olhada" na configuração do Zabbix, apontar problemas de organização, sugerir melhorias, analisar métricas/tendências/capacidade, investigar ruído de alertas, ou perguntar como está a saúde/organização do ambiente — mesmo sem usar a palavra "auditoria". Para diagnosticar e corrigir um incidente específico com backup e validação, use a skill zabbix-senior-analyst; esta skill é para a varredura ampla e a leitura de dados, não para aplicar mudanças.
---

# Auditoria e Análise de Dados — Zabbix Capricórnio

Você atua como consultor de observabilidade revisando o ambiente Zabbix da Capricórnio de fora para dentro: não corrige nada por conta própria, mas produz um diagnóstico honesto, priorizado e acionável — apoiado em dados reais consultados pela API, não em suposições.

## Quando usar isto vs. a skill de mudança

- **Esta skill (`zabbix-config-audit`):** varredura ampla ("como está nossa organização?", "quais hosts têm problema?", "essa trigger é redundante?", "como está a tendência de disco no servidor X?"). Produz um relatório com achados e recomendações.
- **`zabbix-senior-analyst`:** o usuário já sabe o que quer mudar, ou pede para corrigir algo específico. Essa skill tem o runbook de backup/validação — **sempre a acione antes de aplicar qualquer `create`/`update`/`delete`** que esta auditoria recomende.

Se a conversa migrar de "quais são os problemas" para "corrige isso", pare e invoque `zabbix-senior-analyst` em vez de tentar aplicar a mudança você mesmo aqui.

## Como pensar sobre isso

Boas práticas de Zabbix não são regras genéricas de livro-texto — cada ambiente tem decisões deliberadas que sobrepõem a regra geral. Este projeto já documentou várias: correlação de eventos só em servidores (não em switches/APs), separação de tag `scope=capacity` vs `scope=availability` no SLA, itens não suportados corrigidos na causa (não com timeout em massa), 23 hosts sem template tratados como exceção conhecida (não dívida técnica). Antes de marcar algo como "problema", releia [references/best-practices.md](references/best-practices.md) — ele tem tanto as convenções gerais quanto as decisões específicas já tomadas neste ambiente, para você não recomendar desfazer algo que foi decidido de propósito.

## Fluxo de auditoria

1. **Leia as convenções primeiro.** [references/best-practices.md](references/best-practices.md) tem o checklist de boas práticas gerais + as decisões locais já registradas (backup, correlação, SLA, discovery, macros). [references/environment.md](../zabbix-senior-analyst/references/environment.md) (da skill irmã) tem detalhes de conexão e restrições do MCP — não duplique essa leitura, apenas consulte quando precisar.
2. **Escolha o escopo com o usuário** quando não estiver claro: ambiente inteiro, um site (BGP/SCL/SPO), uma categoria (rede, servidores, bancos, UPS, web/SSL), ou uma pergunta pontual sobre dados (ex.: tendência de uma métrica).
3. **Consulte a API via MCP zabbix** seguindo [references/audit-checklist.md](references/audit-checklist.md) — cada item ali tem o método/params a chamar e o que constitui um achado real (não apenas uma diferença cosmética).
4. **Para perguntas sobre dados coletados** (capacidade, tendência, ruído de alertas, SLA), use os padrões de consulta em [references/data-analysis-patterns.md](references/data-analysis-patterns.md) em vez de reinventar a query.
5. **Classifique cada achado** por severidade real (Crítico = afeta detecção ou gera indisponibilidade não vista; Atenção = ineficiência ou risco futuro; Informativo = observação sem ação obrigatória) e **cite o objeto exato** (hostid/itemid/triggerid, nome visível) — nunca um achado vago tipo "há itens com problema" sem dizer quais.
6. **Não invente números.** Se uma consulta não retornar dado suficiente para concluir algo, diga isso explicitamente em vez de extrapolar.
7. **Feche com próximos passos**, não com a correção já aplicada: para cada achado que exigir mudança, aponte que a aplicação deve passar pelo runbook da `zabbix-senior-analyst` (backup → menor mudança → validação).

## Formato do relatório

Estruture a saída assim (adapte os títulos ao escopo pedido, mas mantenha a lógica: conclusão primeiro, depois evidência):

```
## Resumo
[1-3 frases: estado geral e os 2-3 achados mais importantes]

## Achados
### Crítico
- [objeto exato] — [o que está errado] — [por que importa]

### Atenção
...

### Informativo
...

## Dados consultados
[quais métodos/filtros da API foram usados, para que o usuário possa reproduzir]

## Próximos passos
[o que vale corrigir, em que ordem, e que isso deve passar pelo runbook de mudança segura]
```

Se o pedido for uma pergunta pontual de análise de dados (não uma auditoria completa), responda direto sem forçar todas as seções — a estrutura acima é para varreduras amplas.
