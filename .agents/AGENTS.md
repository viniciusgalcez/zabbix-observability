# Regras do Projeto Zabbix Observality

## Backup antes de alterações no Zabbix
* **SEMPRE** faça backup das configurações (via API `configuration.export` ou similar) antes de realizar qualquer alteração (create, update, delete) no Zabbix.
* Salve os backups no diretório `backups/` com um nome descritivo (ex: `backup_host_<id>_<timestamp>.json`).
