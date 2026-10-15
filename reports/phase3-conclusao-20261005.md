# Fase 3 — Conclusão (2026-10-05)

## Resultado

- LLD bad **enabled** no escopo 3A/3B/3C: **0**
- MySQL AZ extra_metric: disabled — plugin ainda resolve DSN placeholder; host macro={$MYSQL.DSN}=tcp://127.0.0.1:3306
- FAD01 service.discovery: disabled — colisão com Template App NDD Print (service.info estáticos); macro NOT_MATCHES ajustada
- SPO-SRV-V02 templates: Linux by Zabbix agent active

## 3D status

| # | Tema | Resultado |
| --- | --- | --- |
| 3D.1 | Hyper-V | Template `Template Windows Hyper-V Host 2` discovery **disabled** (agentes 7.0.26 sem métrica). Reativar após loadable module |
| 3D.2 | SNMP CBS350 | Proxy SNMP timeout **60s**; iface **bulk=0**, max_rep=3. Walk ainda timeout → walk+LLD **disabled**. Settings mantidos |
| 3D.3 | MySQL AZ | Host `{$MYSQL.DSN}=tcp://127.0.0.1:3306`; extra_metric/replication **disabled** (plugin ainda usa placeholder / privs) |
| 3D.4 | PostgreSQL SPO-V02 | Template **desvinculado** (plugin pgsql ausente no agente) |
| 3D.5 | IIS WMI VAPP12 | AppPool discovery **disabled** (Invalid namespace). VAPP10 OK |
| 3D.6 | PhysicalDisk ETE/TIN | **Disabled** — PDH falha em `perf_instance` e `perf_instance_en`. Template Windows revertido para `_en` |
| 3D.7 | FAD01 services | Macro `{$SERVICE.NAME.NOT_MATCHES}` com nddPrint/DCSServer; discovery disabled por colisão NDD |

## LLD bad enabled restantes

_Nenhum._

## Backups

- `backups/phase3d_before_apply_*`
- `backups/phase3d_followup_before_*`
- `backups/phase3_lld_before_disable_*`
