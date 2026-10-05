# Auditoria Zabbix — Saúde de coleta — 01/10/2026

**Gerado em:** 01/10/2026 10:51 (America/Sao_Paulo)  
**Escopo:** coleta (P0)  
**Modo:** somente leitura

## Resumo

Coleta **não está “limpa”**: poucos itens unsupported enabled (7), mas **20 LLD quebradas** e **852 triggers Unknown** — a maior cascata está em switches SCL-TEC (SNMP/OID/timeout). Proxies saudáveis. 1 host ICMP down prolongado (`BGP-ACA-AP01`).

## Achados

### Crítico

- **LLD Hyper-V Unknown metric** nos FHV (SCL/BGP/SPO) — inventário de VMs não descobre.
- **`BGP-ACA-AP01` ICMP unavailable** (~28d, high).
- **Cascata Unknown em `SCL-TEC2-SW01` (284 triggers)** — coleta SNMP/itens derivados degradada; dor futura em capacidade/link se não filtrar LLD.

### Atenção

- **7 unsupported enabled** (FREP speed ×5, VAPP10 IIS, COLOR01 toner).
- **LLD `net.if.discovery` timeout parcial** em SCL-CPD-SW01, SCL-TEC2-SW01, SPO-CPD-SW01.
- **MySQL/pgsql/WMI/PhysicalDisk LLD** com macro/plugin/locale errados.
- **~5801 itens state=1** (maioria disabled) — higiene OK se intencional; não reativar sem revisão.

### Informativo

- Proxies SPO-SRV-V04, SCL-SRV-V08, BGP-SRV-V08: OK.
- Interfaces `available=2`: 0 no snapshot.
- Itens core (agent.ping/icmp/uptime) sem stale &gt;2h na amostra anterior.

## Saúde de coleta (P0)

| Indicador | Valor |
| --- | --- |
| Unsupported enabled | 7 |
| LLD unsupported enabled | 20 |
| Triggers Unknown enabled | 852 |
| Proxies OK | 3/3 |
| Interfaces unavailable | 0 |
| Reachability | 1 |

### Unsupported enabled

| Host | Itemid | Nome | Erro |
| --- | --- | --- | --- |
| BGP-SRV-FREP | 104688 | Interface eno8403: Speed | Value of type "string" is not suitable for value type "Numeric (unsigned)". Value "-1000000" |
| BGP-SRV-FREP | 104689 | Interface enp24s0f0: Speed | Value of type "string" is not suitable for value type "Numeric (unsigned)". Value "-1000000" |
| BGP-SRV-FREP | 104690 | Interface enp24s0f1: Speed | Value of type "string" is not suitable for value type "Numeric (unsigned)". Value "-1000000" |
| BGP-SRV-FREP | 104691 | Interface enp24s0f2: Speed | Value of type "string" is not suitable for value type "Numeric (unsigned)". Value "-1000000" |
| BGP-SRV-FREP | 104692 | Interface enp24s0f3: Speed | Value of type "string" is not suitable for value type "Numeric (unsigned)". Value "-1000000" |
| BGP-SRV-VAPP10 | 108972 | AppPool .NET v2.0 current queue size | Timeout occurred while gathering data. |
| SCL-DRH-COLOR01 | 110116 | Nível de toner: Toner magenta | Value of type "string" is not suitable for value type "Numeric (unsigned)". Value "-2" |

### LLD unsupported enabled

| Host | LLD | Key | Erro |
| --- | --- | --- | --- |
| SCL-CPD-SW01 | Network interfaces discovery | net.if.discovery | only partial data received, cannot retrieve OID: '.1.3.6.1.2.1.31.1.1.1.1.80' fr |
| SCL-TEC2-SW01 | Network interfaces discovery | net.if.discovery | only partial data received, cannot retrieve OID: '.1.3.6.1.2.1.31.1.1.1.6.80' fr |
| SPO-CPD-SW01 | Network interfaces discovery | net.if.discovery | only partial data received, cannot retrieve OID: '.1.3.6.1.2.1.31.1.1.1.18.100'  |
| SPO-SRV-V02 | Database discovery | pgsql.discovery.db["{$PG.HOST}","{$PG.PORT}","{$PG.USER}","{$PG.PASSWORD}","{$PG.DATABASE}"] | Unknown metric pgsql.discovery.db |
| AZ-VM-APP-03-DB | MariaDB discovery | mysql.extra_metric.discovery | Invalid parameters: Invalid first parameter "URI": parse "tcp://<Put your DSN>": |
| AZ-VM-APP-03-DB | Replication discovery | mysql.replication.discovery["{$MYSQL.DSN}","{$MYSQL.USER}","{$MYSQL.PASSWORD}"] | Cannot fetch data: Cannot fetch data.: error getting slave or replica status: Er |
| SCL-SRV-FHV02 | Hyper-V VM Discovery | hyperv.discover.vms | Unknown metric hyperv.discover.vms |
| SCL-SRV-FHV02 | Hyper-V VM Disk Discovery | hyperv.discover.vms.data | Unknown metric hyperv.discovery.vms |
| SCL-SRV-FHV03 | Hyper-V VM Discovery | hyperv.discover.vms | Unknown metric hyperv.discover.vms |
| SCL-SRV-FHV03 | Hyper-V VM Disk Discovery | hyperv.discover.vms.data | Unknown metric hyperv.discovery.vms |
| SPO-SRV-FAD01 | Hyper-V VM Discovery | hyperv.discover.vms | Unknown metric hyperv.discover.vms |
| BGP-SRV-VAPP12 | Application pools discovery | wmi.getall[root\webAdministration, select Name from ApplicationPool] | Exception occurred. (Invalid namespace ) |
| BGP-SRV-FHV01 | Hyper-V VM Discovery | hyperv.discover.vms | Unknown metric hyperv.discover.vms |
| BGP-SRV-FHV01 | Hyper-V VM Disk Discovery | hyperv.discover.vms.data | Unknown metric hyperv.discovery.vms |
| BGP-SRV-FHV02 | Hyper-V VM Discovery | hyperv.discover.vms | Unknown metric hyperv.discover.vms |
| BGP-SRV-FHV02 | Hyper-V VM Disk Discovery | hyperv.discover.vms.data | Unknown metric hyperv.discovery.vms |
| BGP-SRV-FHV03 | Hyper-V VM Discovery | hyperv.discover.vms | Unknown metric hyperv.discover.vms |
| BGP-SRV-FHV03 | Hyper-V VM Disk Discovery | hyperv.discover.vms.data | Unknown metric hyperv.discovery.vms |
| SCL-ETE-TB01 | Physical disks discovery | perf_instance_en.discovery[PhysicalDisk] | Cannot obtain object's localized name. |
| SCL-TIN-TMXC01 | Physical disks discovery | perf_instance_en.discovery[PhysicalDisk] | Cannot obtain object's localized name. |

### Top erros de triggers Unknown

| Erro (prefixo) | Qtd |
| --- | --- |
| Cannot evaluate expression: unknown user macro "{$VOLUME_SIZE_ALARM}" | 7 |
| Cannot evaluate expression: right operand "" is not a numeric value for operator at ">{$II | 4 |
| Cannot evaluate function min(/BGP-SRV-VAPP10/perf_counter_en["\HTTP Service Request Queues | 2 |
| Cannot evaluate function min(/BGP-SRV-VAPP10/perf_counter_en["\HTTP Service Request Queues | 2 |
| Cannot evaluate function last(/SCL-SRV-VAPP02-DB/mssql.backup.diff["HISTORIC_Homolog"]): i | 2 |
| Cannot evaluate function last(/SCL-SRV-VAPP02-DB/mssql.backup.diff["MAESTRO_Homolog"]): it | 2 |
| Cannot evaluate function last(/SCL-SRV-VAPP02-DB/mssql.backup.full["HISTORIC_Homolog"]): i | 2 |
| Cannot evaluate function last(/SCL-SRV-VAPP02-DB/mssql.backup.full["MAESTRO_Homolog"]): it | 2 |
| Cannot evaluate function last(/SCL-DRH-COLOR01/printer.toner.level[Toner magenta]): item i | 2 |
| Cannot evaluate function min(/SCL-SRV-FHV02/perf_counter_en["\System\Processor Queue Lengt | 1 |

### Top hosts triggers Unknown

| Host | Qtd |
| --- | --- |
| SCL-TEC2-SW01 | 284 |
| SCL-TEC1-SW02 | 144 |
| SCL-TEC1-SW03 | 122 |
| BGP-NAS-Hyperv | 18 |
| SCL-CPD-SW02 | 17 |
| BGP-SRV-VAPP10 | 12 |
| SCL-SRV-FREP | 10 |
| CLICKHOUSE-172.16.2.145 | 10 |
| BGP-NAS-DB | 10 |
| BGP-NAS-03 | 10 |
| SCL-NAS-Hyperv | 10 |
| SPO-NAS-Backup | 10 |
| BGP-NAS-Backup | 10 |
| Zabbix server | 10 |
| SCL-NAS-Backup | 10 |

## Dados consultados

Ver artefatos `backups/audit_deep_*_20261001.json` e `backups/audit_deep_remaining_gaps_20261001.json`.

## Próximos passos

1. Corrigir LLD Hyper-V (plugin/template) nos FHV — `zabbix-senior-analyst`.
2. Investigar `BGP-ACA-AP01` ICMP.
3. Unsupported FREP/VAPP10/COLOR01.
4. Filtrar/ajustar LLD SNMP nos switches SCL-TEC* (reduz Unknown em cascata).
5. Avaliar internal action (doc Zabbix) para notificar novo unsupported/Unknown.
