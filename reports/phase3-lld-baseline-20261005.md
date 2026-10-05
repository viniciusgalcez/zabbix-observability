# Fase 3 — Baseline LLD (2026-10-05)

Inventário via API antes de mutações.

## 3A — Hyper-V

- Hosts: 6 (faltando: nenhum)
- LLD rules: 35 | LLD bad/enabled: **1**
- Unsupported enabled: **0** | Unknown triggers: **11**

| Host | LLD bad | Unsupported | Unknown | Templates (trecho) |
| --- | ---: | ---: | ---: | --- |
| SCL-SRV-FHV02 | 0 | 0 | 2 | Windows by Zabbix agent, Template Windows Hyper-V Host 2, Role - Servidor Hyper-V |
| SCL-SRV-FHV03 | 0 | 0 | 2 | Windows by Zabbix agent, Template Windows Hyper-V Host 2, Role - Servidor Hyper-V |
| BGP-SRV-FHV01 | 0 | 0 | 2 | Windows by Zabbix agent, Template Windows Hyper-V Host 2, Role - Servidor Hyper-V |
| BGP-SRV-FHV02 | 0 | 0 | 2 | Windows by Zabbix agent, Template Windows Hyper-V Host 2, Role - Servidor Hyper-V |
| BGP-SRV-FHV03 | 0 | 0 | 2 | Windows by Zabbix agent, Template Windows Hyper-V Host 2, Role - Servidor Hyper-V |
| SPO-SRV-FAD01 | 1 | 0 | 1 | Windows by Zabbix agent, Role - Controlador de Dominio Primario On-Prem, Role - Servidor Hyper-V, Role - Entra Connect e Gateways, … |

### LLD com erro (enabled)

- `SPO-SRV-FAD01` `service.discovery` (itemid 85275): Cannot create item: item with the same key "service.info["DCSServer",state]" already exists. Cannot create item: item with the same key "service.info["nddPrint.Agent.Guardian",state]" already exists. Cannot create item: item with the same key "service.info["nddPrint.Agent.HttpServer",state]" already

## 3B — Switches SNMP

- Hosts: 5 (faltando: nenhum)
- LLD rules: 60 | LLD bad/enabled: **0**
- Unsupported enabled: **0** | Unknown triggers: **554**

| Host | LLD bad | Unsupported | Unknown | Templates (trecho) |
| --- | ---: | ---: | ---: | --- |
| SCL-CPD-SW01 | 0 | 0 | 2 | Cisco IOS by SNMP, Cisco CBS350 Environment by SNMP |
| SCL-TEC2-SW01 | 0 | 0 | 284 | Cisco IOS by SNMP, Cisco CBS350 Environment by SNMP |
| SPO-CPD-SW01 | 0 | 0 | 2 | Cisco IOS by SNMP, Cisco CBS350 Environment by SNMP |
| SCL-TEC1-SW02 | 0 | 0 | 144 | Cisco IOS by SNMP, Cisco CBS350 Environment by SNMP |
| SCL-TEC1-SW03 | 0 | 0 | 122 | Cisco IOS by SNMP, Cisco CBS350 Environment by SNMP |

## 3C — LLD config

- Hosts: 5 (faltando: nenhum)
- LLD rules: 23 | LLD bad/enabled: **0**
- Unsupported enabled: **0** | Unknown triggers: **23**

| Host | LLD bad | Unsupported | Unknown | Templates (trecho) |
| --- | ---: | ---: | ---: | --- |
| AZ-VM-APP-03-DB | 0 | 0 | 3 | MySQL by Zabbix agent 2 |
| SPO-SRV-V02 | 0 | 0 | 8 | Linux by Zabbix agent active, PostgreSQL by Zabbix agent |
| BGP-SRV-VAPP12 | 0 | 0 | 2 | Windows by Zabbix agent, IIS by Zabbix agent, Role - Servidor IIS |
| SCL-ETE-TB01 | 0 | 0 | 5 | Windows by Zabbix agent |
| SCL-TIN-TMXC01 | 0 | 0 | 5 | Windows by Zabbix agent |

