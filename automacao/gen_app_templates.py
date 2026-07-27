#!/usr/bin/env python3
"""
Gera um arquivo de export do Zabbix 7.0 (YAML) com templates de DISPONIBILIDADE
por servico/aplicacao, baseados em service.info[<servico>,state] do Zabbix Agent.

Cada template:
  - 1 macro {$...SERVICE} com o nome do servico Windows (ajustavel por host)
  - 1 item service.info[{$MACRO},state] (coletado a cada 1m)
  - 1 trigger: dispara quando state <> 0 (servico nao esta "Running")
  - valuemap "Windows service state" so para exibicao amigavel

Importar em: Data collection > Templates > Import
"""
import uuid

GROUP = "Templates/Applications"

# Template base de disponibilidade do agente. Todas as triggers de servico
# dependem da trigger dele -> quando o host/agente cai, dispara so UM alerta
# ("agente indisponivel") e os "servico parado" ficam suprimidos (anti-tempestade).
AGENT_TEMPLATE = "App Zabbix Agent Availability"
# Chave UNICA (nao colide com o item agent.ping do template Windows oficial):
# simple check executado pelo proxy testando a porta 10050 do agente.
AGENT_ITEM_KEY = "net.tcp.service[tcp,{HOST.CONN},{$ZBX.AGENT.PORT}]"
DEP_NAME = "Agente ou host inacessivel em {HOST.NAME}"
DEP_EXPR = f"max(/{AGENT_TEMPLATE}/{AGENT_ITEM_KEY},#3)=0"   # sustentado (#3) anti-flapping

# UUIDs DETERMINISTICOS no formato v4 (exigido pelo Zabbix): hash md5 do seed
# com os bits de versao/variante forcados para v4. Assim:
#  - regenerar produz sempre o MESMO uuid -> "Update existing" funciona, sem colisao
#  - passa na validacao "UUIDv4 is expected" do import
# NUNCA usar uuid4() aqui (aleatorio quebra o reimport).
import hashlib
def u(seed):
    b = bytearray(hashlib.md5(seed.encode("utf-8")).digest())
    b[6] = (b[6] & 0x0F) | 0x40  # versao 4
    b[8] = (b[8] & 0x3F) | 0x80  # variante RFC 4122
    return uuid.UUID(bytes=bytes(b)).hex

# (chave, nome_template, macro, servico_padrao, nome_trigger, severidade, tag_componente)
SERVICES = [
    ("dhcp",     "App DHCP Server por Zabbix agent",        "{$DHCP.SERVICE}",    "DHCPServer",     "DHCP Server parado",                     "HIGH",     "dhcp"),
    ("dns",      "App DNS Server por Zabbix agent",         "{$DNS.SERVICE}",     "DNS",            "DNS Server parado",                      "HIGH",     "dns"),
    ("spooler",  "App Print Spooler por Zabbix agent",      "{$SPOOLER.SERVICE}", "Spooler",        "Spooler de impressao parado",            "WARNING",  "spooler"),
    ("adds",     "App Active Directory DS por Zabbix agent","{$ADDS.SERVICE}",    "NTDS",           "Active Directory (NTDS) parado",         "DISASTER", "active-directory"),
    ("adcs",     "App AD Certificate Services por Zabbix agent","{$ADCS.SERVICE}","CertSvc",        "Autoridade Certificadora (CA) parada",   "HIGH",     "ad-cs"),
    ("nps",      "App NPS RADIUS por Zabbix agent",         "{$NPS.SERVICE}",     "IAS",            "Network Policy Server (RADIUS) parado",  "HIGH",     "radius"),
    ("mssql",    "App SQL Server por Zabbix agent",         "{$MSSQL.SERVICE}",   "MSSQLSERVER",    "SQL Server parado",                      "HIGH",     "mssql"),
    ("mssqlag",  "App SQL Server Agent por Zabbix agent",   "{$MSSQLAGENT.SERVICE}","SQLSERVERAGENT","SQL Server Agent parado",               "AVERAGE",  "mssql"),
    ("iis",      "App IIS por Zabbix agent",                "{$IIS.SERVICE}",     "W3SVC",          "IIS (W3SVC) parado",                     "HIGH",     "iis"),
    ("hyperv",   "App Hyper-V por Zabbix agent",            "{$HYPERV.SERVICE}",  "vmms",           "Hyper-V VM Management parado",           "HIGH",     "hyper-v"),
    ("cluster",  "App Failover Cluster por Zabbix agent",   "{$CLUSTER.SERVICE}", "ClusSvc",        "Servico de Cluster parado",              "HIGH",     "cluster"),
    ("pbigw",    "App Power BI Gateway por Zabbix agent",   "{$PBIGW.SERVICE}",   "PBIEgwService",  "Power BI Gateway parado",                "AVERAGE",  "powerbi"),
    ("zbxproxy", "App Zabbix Proxy por Zabbix agent",       "{$ZBXPROXY.SERVICE}","Zabbix Proxy",   "Servico Zabbix Proxy parado",            "HIGH",     "zabbix-proxy"),
    ("dimep",    "App Dimep por Zabbix agent",              "{$DIMEP.SERVICE}",   "NewAccess.Communication.Service", "Dimep (NewAccess) parado",      "HIGH",     "dimep"),
    ("clipnet",  "App Clipnet por Zabbix agent",            "{$CLIPNET.FIREBIRD}","FirebirdServerDefaultInstance", "Clipnet (Firebird) parado",      "HIGH",     "clipnet"),
    ("depshml",  "App Deps Homolog por Zabbix agent",       "{$DEPS.HOMOLOG.SVC}","DepsIntegrador", "Deps Integrador (homolog) parado",        "AVERAGE",  "deps-homolog-app"),
]

ROLE_GROUP = "Templates/Roles"

# Templates de PAPEL: agrupam (linkam) os templates de servico por tipo de host.
# Linke UM role template no host e ele herda todos os servicos daquele papel.
# (nome_role, descricao, [chaves de SERVICES que ele agrupa])
ROLES = [
    ("Role - Controlador de Dominio Primario On-Prem",
     "DC primario on-premises: DHCP, Spooler, DNS, AD DS e RADIUS.",
     ["dhcp", "spooler", "dns", "adds", "nps"]),
    ("Role - Controlador de Dominio Secundario",
     "DC secundario: DNS e AD DS (sem DHCP/RADIUS).",
     ["dns", "adds"]),
    ("Role - Controlador de Dominio Secundario com CA",
     "DC secundario com Autoridade Certificadora: DNS, AD DS e AD CS (sem DHCP/RADIUS).",
     ["dns", "adds", "adcs"]),
    ("Role - Controlador de Dominio Azure",
     "DC em VM Azure (sem DHCP/Spooler): AD DS, DNS e RADIUS.",
     ["adds", "dns", "nps"]),
    ("Role - Servidor Hyper-V",
     "No de virtualizacao Hyper-V em cluster: Hyper-V e Failover Cluster.",
     ["hyperv", "cluster"]),
    ("Role - Zabbix Proxy",
     "Servidor que roda o servico Zabbix Proxy.",
     ["zbxproxy"]),
    ("Role - SQL Server",
     "Servidor de banco SQL Server: instancia e agent.",
     ["mssql", "mssqlag"]),
    ("Role - Servidor IIS",
     "Servidor de aplicacao web IIS.",
     ["iis"]),
    ("Role - Veeam Backup",
     "Servidor de backup Veeam (B&R): Backup, Data Mover, Broker, Catalog, Enterprise Manager, Mount e vPower NFS.",
     ["veeambackup"]),
    ("Role - Entra Connect e Gateways",
     "Servidor de sincronia Entra Connect, Lansweeper e Power BI Gateway.",
     ["adsync", "pbigw", "lansweeper"]),
    ("Role - Veeam ONE",
     "Servidor Veeam ONE (monitoracao): Monitoring, Reporting e Analytics.",
     ["veeamone"]),
    ("Role - Dimep",
     "Servidor Dimep (NewAccess Communication Service).",
     ["dimep"]),
    ("Role - NodeRed",
     "Servidor da stack IoT: Node-RED, Mosquitto e Grafana (servicos Windows).",
     ["nodered"]),
    ("Role - EAS Cozinha",
     "Servidor EAS-Cozinha (processos TexHost, TexCom, TexDosif, InfoTint).",
     ["eascozinha"]),
    ("Role - Totvs",
     "Servidor Totvs (componentes por porta TCP: license, DBAccess, broker, monitor, TSS).",
     ["totvs"]),
    ("Role - Fact Teares",
     "Servidor Fact / Portal Teares (Dashboard).",
     ["factteares"]),
    ("Role - Veeam Repository Linux",
     "Repositorio Veeam em Linux (systemd): data mover, imutabilidade, deployer e environment.",
     ["veeamrepo"]),
    ("Role - Cisco Dashboard e Oxidized Linux",
     "Servidor Linux com Cisco Business Dashboard e Oxidized (backup de rede).",
     ["ciscooxi"]),
    ("Role - GLPI Linux",
     "Servidor GLPI em Linux (AZ-VM-APP-03): Apache, PHP-FPM e MySQL.",
     ["glpi"]),
    ("Role - Grafana Linux",
     "Servidor Grafana em Linux.",
     ["grafana"]),
    ("Role - Clickhouse Linux",
     "Servidor ClickHouse em Linux.",
     ["clickhouse"]),
    ("Role - Docker Linux",
     "Host Docker em Linux (daemon up via systemd). Containers: linkar tambem o template oficial Docker by Zabbix agent 2.",
     ["dockerlinux"]),
    ("Role - Fastweb Linux",
     "Servidor Linux da integracao Fastweb (via cron).",
     ["fastweb"]),
    ("Role - PostgreSQL Linux",
     "Servidor PostgreSQL em Linux.",
     ["postgreslinux"]),
    ("Role - Clipnet",
     "Servidor Clipnet (banco Firebird - FirebirdServerDefaultInstance).",
     ["clipnet"]),
    ("Role - Deps Homolog",
     "Servidor de homologacao Deps (servico DepsIntegrador).",
     ["depshml"]),
]

# Templates com MULTIPLOS servicos no mesmo template (varios itens + triggers).
# (chave, nome_template, descricao, [ (item_label, macro, servico, nome_trigger, severidade, componente) ])
MULTI = [
    ("veeamone", "App Veeam ONE por Zabbix agent",
     "Disponibilidade do Veeam ONE: Monitoring, Reporting e Analytics.",
     [
        ("Veeam ONE Monitoring", "{$VEEAMONE.DCS}", "VeeamDCS", "Veeam ONE Monitoring (VeeamDCS) parado", "HIGH",    "veeam-one"),
        ("Veeam ONE Reporting",  "{$VEEAMONE.RSS}", "VeeamRSS", "Veeam ONE Reporting (VeeamRSS) parado",  "HIGH",    "veeam-one"),
        ("Veeam ONE Analytics",  "{$VEEAMONE.OAS}", "VeeamOAS", "Veeam ONE Analytics (VeeamOAS) parado",  "AVERAGE", "veeam-one"),
     ]),
    ("factteares", "App Fact Teares por Zabbix agent",
     "Disponibilidade dos servicos Fact / Portal Teares (Dashboard).",
     [
        ("Portal Teares (Producao)", "{$FACT.PORTAL}", "Portal_Teares",     "Portal Teares parado", "HIGH", "fact"),
        ("Agente FACT Toyota",       "{$FACT.AGENT}",  "FACT_Agent_Toyota", "Agente FACT parado",   "HIGH", "fact"),
     ]),
    ("adsync", "App Entra Connect Sync por Zabbix agent",
     "Disponibilidade do Microsoft Entra Connect: sync, health agent e updater.",
     [
        ("Entra Connect Sync",         "{$ADSYNC.SERVICE}", "ADSync",                     "Microsoft Entra Connect Sync parado",   "HIGH",    "entra-connect"),
        ("Entra Connect Health Agent", "{$ADSYNC.HEALTH}",  "AzureADConnectHealthAgent",  "Entra Connect Health Agent parado",     "AVERAGE", "entra-connect"),
        ("Entra Connect Agent Updater","{$ADSYNC.UPDATER}", "AzureADConnectAgentUpdater", "Entra Connect Agent Updater parado",    "WARNING", "entra-connect"),
     ]),
    ("lansweeper", "App Lansweeper por Zabbix agent",
     "Disponibilidade do Lansweeper: server, agent e auto-update.",
     [
        ("Lansweeper Server",      "{$LANSWEEPER.SERVER}", "lansweeperservice",      "Lansweeper Server parado",      "HIGH",    "lansweeper"),
        ("Lansweeper Agent",       "{$LANSWEEPER.AGENT}",  "LansweeperAgentService", "Lansweeper Agent parado",       "AVERAGE", "lansweeper"),
        ("Lansweeper Auto-update", "{$LANSWEEPER.UPDATE}", "lansweeperautoupdate",   "Lansweeper Auto-update parado", "WARNING", "lansweeper"),
     ]),
    ("nodered", "App NodeRed por Zabbix agent",
     "Disponibilidade da stack IoT em servicos Windows: Node-RED (Inst 1/2/3/QA), Mosquitto (MQTT) e Grafana. Host: SCL-SRV-VAPP03.",
     [
        ("Node-RED Inst 1",  "{$NODERED.SVC1}",   "noderedsvc1",  "Node-RED Inst 1 parado", "HIGH",    "node-red"),
        ("Node-RED Inst 2",  "{$NODERED.SVC2}",   "noderedsvc2",  "Node-RED Inst 2 parado", "HIGH",    "node-red"),
        ("Node-RED Inst 3",  "{$NODERED.SVC3}",   "noderedsvc3",  "Node-RED Inst 3 parado", "HIGH",    "node-red"),
        ("Node-RED QA",      "{$NODERED.SVCQA}",  "noderedsvcqa", "Node-RED QA parado",     "AVERAGE", "node-red"),
        ("Mosquitto (MQTT)", "{$MOSQUITTO.SVC}",  "mosquitto",    "Mosquitto parado",       "HIGH",    "mosquitto"),
        ("Grafana (Windows)","{$GRAFANA.WIN.SVC}","Grafana",      "Grafana parado",         "HIGH",    "grafana"),
     ]),
    ("veeambackup", "App Veeam Backup por Zabbix agent",
     "Disponibilidade dos servicos do Veeam Backup & Replication. Host: BGP-SRV-VAPP02.",
     [
        ("Veeam Backup Service",      "{$VEEAM.BACKUP}",   "VeeamBackupSvc",            "Veeam Backup Service parado",      "HIGH",    "veeam-backup"),
        ("Veeam Data Mover",          "{$VEEAM.TRANSPORT}","VeeamTransportSvc",         "Veeam Data Mover parado",          "HIGH",    "veeam-backup"),
        ("Veeam Broker",             "{$VEEAM.BROKER}",   "VeeamBrokerSvc",            "Veeam Broker parado",              "AVERAGE", "veeam-backup"),
        ("Veeam Guest Catalog",       "{$VEEAM.CATALOG}",  "VeeamCatalogSvc",           "Veeam Guest Catalog parado",       "AVERAGE", "veeam-backup"),
        ("Veeam Enterprise Manager",  "{$VEEAM.ENTMGR}",   "VeeamEnterpriseManagerSvc", "Veeam Enterprise Manager parado",  "AVERAGE", "veeam-backup"),
        ("Veeam Mount Service",       "{$VEEAM.MOUNT}",    "VeeamMountSvc",             "Veeam Mount Service parado",       "AVERAGE", "veeam-backup"),
        ("Veeam vPower NFS",          "{$VEEAM.NFS}",      "VeeamNFSSvc",               "Veeam vPower NFS parado",          "AVERAGE", "veeam-backup"),
     ]),
]

# Templates LINUX (systemd via agent2). Usam systemd.unit.info[<unit>,ActiveState]
# - item direto por unit (nao depende da descoberta systemd, que estava com timeout).
# (chave, nome_template, descricao, [ (item_label, macro, unit, nome_trigger, severidade, componente) ])
LINUX_SYSTEMD = [
    ("veeamrepo", "App Veeam Repository Linux",
     "Disponibilidade dos servicos Veeam em repositorio Linux (systemd / agent2).",
     [
        ("Veeam Data Mover",     "{$VEEAM.UNIT.TRANSPORT}", "veeamtransport.service",  "Veeam Data Mover parado",          "HIGH",    "veeam"),
        ("Veeam Immutability",   "{$VEEAM.UNIT.IMMU}",      "veeamimmurepo.service",   "Veeam Immutability Service parado","HIGH",    "veeam"),
        ("Veeam Deployer",       "{$VEEAM.UNIT.DEPLOY}",    "veeamdeployment.service", "Veeam Deployer parado",            "AVERAGE", "veeam"),
        ("Veeam Environment",    "{$VEEAM.UNIT.ENV}",       "veeamenvironment.service","Veeam Environment parado",         "AVERAGE", "veeam"),
     ]),
    ("ciscooxi", "App Cisco Dashboard e Oxidized Linux",
     "Disponibilidade do Cisco Business Dashboard e do Oxidized (backup de config de rede) - Linux/systemd.",
     [
        ("Cisco Business Dashboard", "{$CBD.UNIT}",      "cisco-business-dashboard.service", "Cisco Business Dashboard parado", "HIGH",    "cisco-dashboard"),
        ("Oxidized (backup de rede)","{$OXIDIZED.UNIT}", "oxidized.service",                 "Oxidized parado",                 "AVERAGE", "oxidized"),
     ]),
    ("glpi", "App GLPI Linux",
     "Disponibilidade da stack web do GLPI (Apache, PHP-FPM e MySQL) - Linux/systemd. Host: AZ-VM-APP-03.",
     [
        ("GLPI Apache (web)",  "{$GLPI.APACHE.UNIT}", "apache2.service",    "GLPI Apache parado",  "HIGH", "apache"),
        ("GLPI PHP-FPM",       "{$GLPI.PHP.UNIT}",    "php8.4-fpm.service", "GLPI PHP-FPM parado", "HIGH", "php-fpm"),
        ("GLPI MySQL",         "{$GLPI.DB.UNIT}",     "mysql.service",      "GLPI MySQL parado",   "HIGH", "mysql"),
     ]),
    ("grafana", "App Grafana Linux",
     "Disponibilidade do Grafana - Linux/systemd.",
     [
        ("Grafana", "{$GRAFANA.UNIT}", "grafana-server.service", "Grafana parado", "HIGH", "grafana"),
     ]),
    ("clickhouse", "App Clickhouse Linux",
     "Disponibilidade do ClickHouse - Linux/systemd.",
     [
        ("ClickHouse Server", "{$CLICKHOUSE.UNIT}", "clickhouse-server.service", "ClickHouse Server parado", "HIGH", "clickhouse"),
     ]),
    ("dockerlinux", "App Docker Linux",
     "Disponibilidade do daemon Docker (systemd). Para monitorar containers, use tambem o template oficial Docker by Zabbix agent 2.",
     [
        ("Docker daemon", "{$DOCKER.UNIT}", "docker.service", "Docker daemon parado", "HIGH", "docker"),
     ]),
    ("fastweb", "App Fastweb Linux",
     "Disponibilidade do agendador cron que executa a integracao Fastweb - Linux/systemd. Host: SPO-SRV-V05.",
     [
        ("Cron (agendador Fastweb)", "{$FASTWEB.CRON.UNIT}", "cron.service", "Cron (Fastweb) parado", "HIGH", "fastweb"),
     ]),
    ("postgreslinux", "App PostgreSQL Linux",
     "Disponibilidade do PostgreSQL - Linux/systemd. Host: spo-srv-v02 (DB do Zabbix).",
     [
        ("PostgreSQL", "{$POSTGRES.UNIT}", "postgresql.service", "PostgreSQL parado", "HIGH", "postgresql"),
     ]),
]

# Templates por PROCESSO (Windows/Linux) - usam proc.num[<processo>].
# Dispara quando o numero de processos = 0 (processo nao esta rodando).
# (chave, nome_template, descricao, [ (item_label, macro, processo, nome_trigger, severidade, componente) ])
PROCESS = [
    ("eascozinha", "App EAS Cozinha por Zabbix agent",
     "Disponibilidade dos processos EAS-Cozinha (proc.num). Host: SCL-SRV-VAPP14. Confirme os nomes dos processos nas macros.",
     [
        ("EAS TexHost",  "{$EAS.TEXHOST}",  "TexHost.exe",  "EAS TexHost fora do ar",  "HIGH", "eas-cozinha"),
        ("EAS TexCom",   "{$EAS.TEXCOM}",   "TexCom.exe",   "EAS TexCom fora do ar",   "HIGH", "eas-cozinha"),
        ("EAS TexDosif", "{$EAS.TEXDOSIF}", "Texdosif.exe", "EAS TexDosif fora do ar", "HIGH", "eas-cozinha"),
     ]),
]

# Templates por PORTA TCP em escuta - usam net.tcp.listen[<porta>].
# Dispara quando a porta nao esta escutando (=0). Ideal p/ apps multi-componente
# cujos nomes de servico sao instaveis, mas as portas sao conhecidas (ex.: Totvs).
# (chave, nome_template, descricao, [ (item_label, macro, porta, nome_trigger, severidade, componente) ])
PORT_LISTEN = [
    ("totvs", "App Totvs por Zabbix agent",
     "Disponibilidade dos componentes Totvs por porta TCP em escuta (net.tcp.listen). Host: BGP-SRV-VAPP11.",
     [
        ("Totvs License Server",     "{$TOTVS.PORT.LICENSE}",  "17501", "Totvs License Server fora do ar",      "HIGH",    "totvs"),
        ("Totvs DBAccess Master",    "{$TOTVS.PORT.DBMASTER}", "17100", "Totvs DBAccess Master fora do ar",     "HIGH",    "totvs"),
        ("Totvs DBAccess Slave",     "{$TOTVS.PORT.DBSLAVE}",  "17101", "Totvs DBAccess Slave fora do ar",      "AVERAGE", "totvs"),
        ("Totvs Broker Smartclient", "{$TOTVS.PORT.BROKER}",   "17200", "Totvs Broker Smartclient fora do ar",  "HIGH",    "totvs"),
        ("Totvs App Server Monitor", "{$TOTVS.PORT.MONITOR}",  "17210", "Totvs Monitor fora do ar",             "AVERAGE", "totvs"),
        ("Totvs TSS NF-e",           "{$TOTVS.PORT.TSS}",      "1307",  "Totvs TSS NF-e fora do ar",            "AVERAGE", "totvs"),
     ]),
]

VM_STATES = [
    ("0", "Running"), ("1", "Paused"), ("2", "Start pending"), ("3", "Pause pending"),
    ("4", "Continue pending"), ("5", "Stop pending"), ("6", "Stopped"),
    ("7", "Unknown"), ("255", "No such service"),
]

def valuemap_block(indent, tname):
    sp = " " * indent
    lines = [f"{sp}valuemaps:", f"{sp}  - uuid: {u('vmap:'+tname)}", f"{sp}    name: 'Windows service state'", f"{sp}    mappings:"]
    for val, name in VM_STATES:
        lines.append(f"{sp}      - value: '{val}'")
        lines.append(f"{sp}        newvalue: '{name}'")
    return "\n".join(lines)

def app_short(tname):
    """Nome curto da aplicacao para a trigger agregada."""
    return tname.replace("App ", "").replace(" por Zabbix agent", "").replace(" Linux", "").strip()

def avail_template(tname, desc, comps, kind):
    """Builder unificado de template de disponibilidade.
    kind: 'service'|'systemd'|'proc'|'port'.
    comps: lista de (label, macro, default, trig, sev, comp[, status]).
      1 componente  -> 1 trigger nomeada (alerta daquele item).
      >1 componentes -> 1 trigger AGREGADA (dispara se QUALQUER componente cair);
                        itens mantidos sem trigger propria (visiveis em Latest data)."""
    def keycond(macro):
        # Condicao SUSTENTADA (#3 = 3 ultimas coletas) -> anti-flapping.
        # So dispara se o componente esteve fora nas 3 ultimas leituras (nao num blip).
        if kind == "service":   # UNSIGNED: down quando state<>0; min(#3)<>0 = as 3 fora
            k = f"service.info[{macro},state]"; return k, f"min(/{tname}/{k},#3)<>0"
        if kind == "systemd":   # CHAR: down quando ActiveState<>active; count das 3 != active
            k = f'systemd.unit.info["{macro}",ActiveState]'; return k, f'count(/{tname}/{k},#3,"ne","active")=3'
        if kind == "proc":      # UNSIGNED: down quando =0; max(#3)=0 = as 3 zeradas
            k = f"proc.num[{macro}]"; return k, f"max(/{tname}/{k},#3)=0"
        if kind == "port":      # UNSIGNED: down quando nao escuta (=0); max(#3)=0 = as 3 fora
            k = f"net.tcp.listen[{macro}]"; return k, f"max(/{tname}/{k},#3)=0"
        raise ValueError(kind)
    vt = "CHAR" if kind == "systemd" else "UNSIGNED"
    itype = "ZABBIX_ACTIVE" if kind == "systemd" else "ZABBIX_PASSIVE"
    iname = {"service": "estado do servico", "systemd": "estado da unit",
             "proc": "numero de processos", "port": "porta em escuta"}[kind]
    mdesc = {"service": "Nome do servico Windows (Get-Service -Name ...).",
             "systemd": "Nome da unit systemd (systemctl list-units --type=service).",
             "proc": "Nome do processo (tasklist / Get-Process).",
             "port": "Porta TCP do componente."}[kind]
    multi = len(comps) > 1

    meta = []
    for c in comps:
        label, macro, default, trig, sev, comp = c[:6]
        status = c[6] if len(c) > 6 else "ENABLED"
        k, cond = keycond(macro)
        meta.append((label, macro, default, trig, sev, comp, status, k, cond))

    def trig_entry(name, expr, sev, desc_t, dep=None, extra_tags=None):
        """Uma entrada de trigger (sem o cabecalho 'triggers:'). dep=(nome, expr) cria dependencia.
        extra_tags: lista de (tag, valor) adicionais (ex.: ('aggregate','1') na agregada)."""
        e = [
            f"            - uuid: {u('trig:'+tname+':'+name)}",
            f"              expression: '{expr}'",
            f"              name: '{name}'",
            f"              priority: {sev}",
            f"              description: '{desc_t}'",
        ]
        if dep:
            dname, dexpr = dep
            e += [
                "              dependencies:",
                f"                - name: '{dname}'",
                f"                  expression: '{dexpr}'",
            ]
        e += [
            "              tags:",
            "                - tag: scope",
            "                  value: availability",
        ]
        for tg, tv in (extra_tags or []):
            e += [f"                - tag: {tg}", f"                  value: '{tv}'"]
        return e

    out = [
        f"    - uuid: {u('tmpl:'+tname)}",
        f"      template: '{tname}'",
        f"      name: '{tname}'",
        f"      description: '{desc}'",
        "      groups:",
        f"        - name: '{GROUP}'",
        "      items:",
    ]
    # AGREGADA com AND: dispara so quando TODOS os componentes estao parados
    # (aplicacao totalmente fora do ar) -> 1 alerta unico.
    agg_expr = " and ".join(m[8] for m in meta)
    short = app_short(tname)
    for idx, (label, macro, default, trig, sev, comp, status, k, cond) in enumerate(meta):
        out += [
            f"        - uuid: {u('item:'+tname+':'+k)}",
            f"          name: '{label}: {iname}'",
            f"          type: {itype}",
            f"          key: '{k}'",
            "          delay: 1m",
            f"          value_type: {vt}",
        ]
        if kind == "service":
            out += ["          valuemap:", "            name: 'Windows service state'"]
        if status == "DISABLED":
            out.append("          status: DISABLED")
        out += [
            "          tags:",
            "            - tag: component",
            f"              value: '{comp}'",
        ]
        agg_name = f"{short} fora do ar em {{HOST.NAME}}"
        out.append("          triggers:")
        if multi:
            if idx == 0:
                # agregada PRIMEIRO (no item 0) para as dependentes resolverem no import.
                # Dispara so quando TODOS os componentes caem. Tag aggregate=1 para event correlation.
                out += trig_entry(agg_name, agg_expr, "HIGH",
                                  "Todos os componentes parados (aplicacao indisponivel). Veja em Latest data.",
                                  extra_tags=[("aggregate", "1")])
            # trigger individual do componente, DEPENDENTE da agregada: quando TODOS caem,
            # a agregada entra em problema e o Zabbix SUPRIME as individuais (nem cria evento).
            # Sem flapping (ao contrario do event correlation, que so fecha e a trigger reabre).
            out += trig_entry(f"{trig} em {{HOST.NAME}}", cond, sev,
                              f"Componente parado: {macro}.", dep=(agg_name, agg_expr))
        else:
            out += trig_entry(f"{trig} em {{HOST.NAME}}", cond, sev, f"Componente indisponivel: {macro}.")
    out.append("      macros:")
    for label, macro, default, trig, sev, comp, status, k, cond in meta:
        out.append(f"        - macro: '{macro}'")
        out.append(f"          value: '{default}'")
        out.append(f"          description: '{mdesc}'")
    if kind == "service":
        out.append(valuemap_block(6, tname))
    return out

def agent_template_block():
    """Template base: detecta agente/host indisponivel via simple check na porta 10050.
    Chave unica para nao colidir com o agent.ping do template Windows oficial."""
    return [
        f"    - uuid: {u('tmpl:'+AGENT_TEMPLATE)}",
        f"      template: '{AGENT_TEMPLATE}'",
        f"      name: '{AGENT_TEMPLATE}'",
        "      description: 'Detecta indisponibilidade do agente/host via simple check na porta 10050 (executado pelo proxy). Base da dependencia anti-tempestade dos demais alertas.'",
        "      groups:",
        f"        - name: '{GROUP}'",
        "      items:",
        f"        - uuid: {u('item:'+AGENT_TEMPLATE+':'+AGENT_ITEM_KEY)}",
        "          name: 'Agente acessivel (porta TCP 10050)'",
        "          type: SIMPLE",
        f"          key: '{AGENT_ITEM_KEY}'",
        "          delay: 1m",
        "          value_type: UNSIGNED",
        "          tags:",
        "            - tag: component",
        "              value: 'zabbix-agent'",
        "          triggers:",
        f"            - uuid: {u('trig:'+AGENT_TEMPLATE+':'+DEP_NAME)}",
        f"              expression: '{DEP_EXPR}'",
        f"              name: '{DEP_NAME}'",
        "              priority: HIGH",
        "              description: 'Porta 10050 do agente inacessivel a partir do proxy: agente parado ou host fora do ar.'",
        "              tags:",
        "                - tag: scope",
        "                  value: availability",
        "      macros:",
        "        - macro: '{$ZBX.AGENT.PORT}'",
        "          value: '10050'",
        "          description: 'Porta TCP do Zabbix agent testada para disponibilidade.'",
    ]

def build():
    out = []
    out.append("zabbix_export:")
    out.append("  version: '7.0'")
    out.append("  template_groups:")
    out.append(f"    - uuid: {u('grp:'+GROUP)}")
    out.append(f"      name: '{GROUP}'")
    out.append(f"    - uuid: {u('grp:'+ROLE_GROUP)}")
    out.append(f"      name: '{ROLE_GROUP}'")
    out.append("  templates:")
    key_to_name = {key: tname for key, tname, *_ in SERVICES}
    key_to_name.update({key: tname for key, tname, *_ in MULTI})
    key_to_name.update({key: tname for key, tname, *_ in LINUX_SYSTEMD})
    key_to_name.update({key: tname for key, tname, *_ in PROCESS})
    key_to_name.update({key: tname for key, tname, *_ in PORT_LISTEN})
    # ---- Template base de disponibilidade do agente ----
    out += agent_template_block()
    # ---- Templates de servico unico (Windows service.info) ----
    for key, tname, macro, svc, trig, sev, comp in SERVICES:
        label = trig.replace(" parado", "").replace(" parada", "")
        out += avail_template(tname, f"Disponibilidade via Zabbix Agent. Ajuste o servico na macro {macro} por host se necessario.",
                              [(label, macro, svc, trig, sev, comp)], "service")
    # ---- Templates multi-servico (Windows service.info) ----
    for key, tname, desc, services in MULTI:
        out += avail_template(tname, desc, services, "service")
    # ---- Templates Linux (systemd) ----
    for key, tname, desc, units in LINUX_SYSTEMD:
        out += avail_template(tname, desc, units, "systemd")
    # ---- Templates por processo (proc.num) ----
    for key, tname, desc, procs in PROCESS:
        out += avail_template(tname, desc, procs, "proc")
    # ---- Templates por porta TCP (net.tcp.listen) ----
    for key, tname, desc, ports in PORT_LISTEN:
        out += avail_template(tname, desc, ports, "port")
    # ---- Role templates (agrupam os de servico via vinculo de template) ----
    for rname, rdesc, members in ROLES:
        out.append(f"    - uuid: {u('tmpl:'+rname)}")
        out.append(f"      template: '{rname}'")
        out.append(f"      name: '{rname}'")
        out.append(f"      description: '{rdesc}'")
        out.append("      groups:")
        out.append(f"        - name: '{ROLE_GROUP}'")
        out.append("      templates:")
        for mkey in members:
            out.append(f"        - name: '{key_to_name[mkey]}'")
    return "\n".join(out) + "\n"

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "app-availability-templates.yaml"
    with open(path, "w", encoding="utf-8") as f:
        f.write(build())
    print(f"Gerado: {path} ({len(SERVICES)} servico-unico + {len(MULTI)} multi + {len(ROLES)} roles)")
