# Validação: sobreposição de indisponibilidade (Deps API + Banco)

**Data:** 2026-11-26  
**Pergunta:** Se a API Deps fica 1h fora e o banco cai 40 min *durante* essa hora, o SLA pode somar 1h40? O Zabbix já faz união ou preciso mudar o relatório?

## Veredito

| Pergunta | Resposta |
|----------|----------|
| A regra de união está correta? | **Sim.** Downtime da app = união dos componentes, não a soma. |
| O motor nativo do Zabbix faz isso no Deps? | **Sim**, no serviço pai `Deps Produção`. |
| Precisa alterar o motor/SLA do Zabbix? | **Não** (desde que só o pai tenha `slatier`). |
| Precisa alterar relatório customizado? | **Sim, se ele somar** durações de hosts/filhos. Corrigido em `gen_availability_report.py`; use `gen_sla_app_report.py` para SLI oficial. |

## Como o Zabbix calcula

1. SLA casa serviços pela tag (`slatier=critico` / `padrao`).
2. O SLI é **por serviço**, com base na timeline de status daquele serviço.
3. Pai com **algorithm = Most critical of child services (2)** fica em problema enquanto **qualquer** filho está em problema → a timeline do pai já é a **união**.
4. Filhos **sem** `slatier` **não** entram no `sla.getsli` → não há soma API+Banco no relatório nativo.

Documentação: [SLA](https://www.zabbix.com/documentation/current/en/manual/it_services/sla), [Service tree](https://www.zabbix.com/documentation/current/en/manual/it_services/service_tree).

## Evidência (Deps Produção)

Fonte: captura live `sla.getsli` + `service.get` (fixture  
[`backups/fixture_sla_critico_sli_live_20261126.json`](../backups/fixture_sla_critico_sli_live_20261126.json)).

- Pai `Deps Produção` (`serviceid=41`): `algorithm=2`, tag `slatier=critico`.
- Filhos: `Deps Produção Banco` (43), `Deps Home` (202), `Deps API` (203).
- Em `sla.getsli` do **SLA Crítico**, aparece `41`; **não** aparecem `43` / `202` / `203`.

Exemplo numérico (teste unitário):

- API `[0, 3600]`, Banco `[1200, 3600]`
- Soma = **6000 s** (errado para a app)
- União = **3600 s** (correto; bate com o pai)

## Onde a soma indevida aparece

[`automacao/gen_availability_report.py`](../automacao/gen_availability_report.py) gerava o card **“Downtime somado”** = `sum(duração de cada queda de host)`. Isso:

- é relatório de **host**, não de serviço BSM;
- conta sobreposição duas vezes;
- **não** é o que o Zabbix usa no SLA de aplicação.

### Correção feita neste branch

1. Card principal passou a **união** (exclui colaterais).
2. Soma bruta ficou só como referência, com aviso explícito.
3. Novo [`automacao/gen_sla_app_report.py`](../automacao/gen_sla_app_report.py) lê `sla.getsli` dos pais.
4. [`automacao/audit_sla_overlap.py`](../automacao/audit_sla_overlap.py) + [`automacao/test_sla_overlap.py`](../automacao/test_sla_overlap.py) validam a regra.

## Checklist operacional (rede Capri)

```bash
cd automacao
python test_sla_overlap.py
python audit_sla_overlap.py --fixture ../backups/fixture_sla_critico_sli_live_20261126.json
# ao vivo:
ZABBIX_URL=... ZABBIX_TOKEN=... python audit_sla_overlap.py --service "Deps Produção"
ZABBIX_URL=... ZABBIX_TOKEN=... python gen_sla_app_report.py --sla "SLA Crítico"
```

Se o audit ao vivo apontar filho com `slatier=critico|padrao`, **remover a tag do filho** (manter só no pai). Não inventar média/soma de componentes no relatório.
