# Zabbix Observability

Este repositório contém scripts, playbooks, dashboards e ferramentas de automação para monitoramento e observabilidade utilizando o **Zabbix**. O projeto visa consolidar alertas, gerar relatórios de indisponibilidade e fornecer visualizações geográficas e de desempenho.

## 📂 Estrutura do Projeto

O repositório é organizado em diretórios específicos para cada funcionalidade:

- **`automacao/`**: Scripts de automação para gestão de agentes e triggers.
- **`dashboards-grafana/`**: Configurações e importação de dashboards para visualização de dados no Grafana.
- **`backups/`**: Scripts e procedimentos para backup de configurações e dados críticos.
- **`.agents/`**: Configurações e scripts relacionados aos agentes do Zabbix.
- **`noc_app/templates/`**: Modelos de templates para aplicação e monitoramento específico.
- **`.claude/`**: Configurações de assistência para IA (Claude) dentro do repositório.

## 📊 Arquivos Principais

### Dashboards e Relatórios
- **`noc_geomap_dashboard.json`**: JSON de exportação para dashboard de mapa geográfico (Geomap) do Zabbix/NOC.
- **`noc-geomap.html`**: Visualização HTML do mapa de rede.
- **`relatorio-monitoramento.html`**: Relatório geral de status de monitoramento.
- **`relatorio-indisponibilidade.html`** e **`relatorio-indisponibilidade.xlsx`**: Relatórios detalhados sobre tempo de inatividade e indisponibilidade de serviços.

### Scripts e Executáveis
- **`Painel-Zabbix.bat`**: Script em lote (Windows) para abrir ou iniciar o painel de controle do Zabbix.
- **`abrir-noc.cmd`**: Comando para abrir a interface do NOC (Network Operations Center).
- **`.gitignore`**: Configuração para ignorar arquivos desnecessários no controle de versão.

## 🛠️ Tecnologias Utilizadas

O projeto é composto por uma mistura de linguagens para cobrir diferentes necessidades de automação e visualização:

| Linguagem | Percentual | Uso Principal |
|-----------|------------|---------------|
| HTML      | 62.9%      | Dashboards, relatórios e interfaces web |
| Python    | 24.7%      | Scripts de automação e lógica de backend |
| PowerShell| 9.6%       | Automação do sistema e gestão de agentes |
| Shell     | 1.7%       | Scripts de inicialização e utilitários |

## 🚀 Instalação e Uso

1. **Clone o repositório**:
   ```bash
   git clone <url-do-repositorio>
   cd zabbix-observability
