# Modelo de relatório de auditoria

Salvar em: `reports/auditoria-zabbix-YYYYMMDD.md`  
(ou `reports/auditoria-zabbix-YYYYMMDD-<escopo>.md`)

Fuso das datas no texto: `dd/MM/yyyy HH:mm` · `America/Sao_Paulo`.

```markdown
# Auditoria Zabbix Capricórnio — dd/MM/yyyy

**Gerado em:** dd/MM/yyyy HH:mm (America/Sao_Paulo)
**Escopo:** full | coleta | firewalls | rede | servidores | web | ...
**Modo:** somente leitura

## Resumo
[1–3 frases: veredito + 2–3 achados que importam agora]

## Achados

### Crítico
- **`host` / `id` / objeto** — o que está errado — por que importa
  - Evidência: erro da API / contagem / idade

### Atenção
- ...

### Informativo
- ...

## Saúde de coleta (P0)
| Indicador | Valor |
| --- | --- |
| Unsupported enabled | N |
| LLD unsupported enabled | N |
| Triggers Unknown enabled | N |
| Proxies OK / atrasados | ... |
| Interfaces unavailable | N |
| Reachability problems | N |

[Tabela curta dos top hosts/erros — detalhe longo só se <30 linhas]

## Correlação / problemas (se no escopo)
| Indicador | Valor |
| --- | --- |
| Problems abertos | N (roots / symptoms) |
| FW roots / symptoms | ... |
| Correlações 16/45 | enabled/disabled |

## Dados consultados
| Método | Filtro | Artefato backups/ |
| --- | --- | --- |
| item.get | state=1,status=0 | audit_...json |

## Próximos passos
1. [risco alto →] … (via `zabbix-senior-analyst` + backup)
2. ...
3. ...
```

### Regras de escrita

- Conclusão primeiro; sem “vou auditar…” no relatório final.
- IDs reais da API; se a consulta falhou, diga **falhou** e o erro.
- Cascata: um achado raiz + “N triggers Unknown decorrentes”, não N Críticos clones.
- Exceções conhecidas (Web sem template, piloto 16/45) vão em Informativo com contexto.
- Chat do usuário: resumo curto + caminho do `.md`.
