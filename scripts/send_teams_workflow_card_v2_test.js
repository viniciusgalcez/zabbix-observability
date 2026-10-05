const fs = require('fs');
const https = require('https');
const vm = require('vm');

const endpoint = process.env.TEAMS_ENDPOINT;
if (!endpoint) {
  console.error('TEAMS_ENDPOINT is required.');
  process.exit(1);
}

function buildCard() {
  const script = fs.readFileSync('scripts/teams_workflow_card_v2.js', 'utf8');
  let posted = null;
  const eventValue = process.env.ALERT_EVENT_VALUE || '1';
  const isResolved = eventValue === '0';
  const messageLines = isResolved
    ? [
      'Estado: ' + (process.env.ALERT_STATE || 'RESOLVIDO'),
      'Severidade: ' + (process.env.ALERT_SEVERITY || 'High'),
      'Host: ' + (process.env.ALERT_HOST || 'SRV-TESTE-01'),
      'Endereco: ' + (process.env.ALERT_ADDRESS || '127.0.0.1'),
      'Duracao: ' + (process.env.ALERT_DURATION || '1m 00s'),
      'Resolvido em: ' + (process.env.ALERT_RESOLVED_AT || '2026.09.09 14:31:00'),
      'Evento: ' + (process.env.ALERT_EVENT_ID || 'teams-card-v2-test-001'),
      'Contexto: ' + (process.env.ALERT_CONTEXT || 'teste controlado do card v2 enviado pelo Teams Workflow')
    ]
    : [
      'Estado: ' + (process.env.ALERT_STATE || 'INCIDENTE ATIVO'),
      'Severidade: ' + (process.env.ALERT_SEVERITY || 'High'),
      'Host: ' + (process.env.ALERT_HOST || 'SRV-TESTE-01'),
      'Endereco: ' + (process.env.ALERT_ADDRESS || '127.0.0.1'),
      'Inicio: ' + (process.env.ALERT_STARTED_AT || '2026.09.09 14:30:00'),
      'Dado operacional: ' + (process.env.ALERT_OPDATA || 'CPU 97%'),
      'Valor atual: ' + (process.env.ALERT_LAST_VALUE || '97%'),
      'Evento: ' + (process.env.ALERT_EVENT_ID || 'teams-card-v2-test-001'),
      'Contexto: ' + (process.env.ALERT_CONTEXT || 'teste controlado do card v2 enviado pelo Teams Workflow')
    ];

  const params = {
    alert_subject: process.env.ALERT_SUBJECT || '[Teste Teams] CPU elevada',
    alert_message: messageLines.join('\n'),
    zabbix_url: 'https://zabbix.capricornio.corp.br',
    teams_endpoint: endpoint,
    event_source: '0',
    event_value: eventValue,
    event_update_status: '0',
    event_nseverity: process.env.ALERT_NSEVERITY || '4',
    event_severity: process.env.ALERT_SEVERITY || 'High',
    event_update_nseverity: process.env.ALERT_NSEVERITY || '4',
    event_update_severity: process.env.ALERT_SEVERITY || 'High',
    host_ip: process.env.ALERT_HOST_IP || process.env.ALERT_ADDRESS || '127.0.0.1',
    trigger_id: process.env.ALERT_TRIGGER_ID || '12345',
    event_id: process.env.ALERT_EVENT_ID_NUMERIC || '1001'
  };

  const context = {
    value: JSON.stringify(params),
    Zabbix: { log: () => {} },
    HttpRequest: function () {
      this.status = 200;
      this.addHeader = () => {};
      this.clearHeader = () => {};
      this.setProxy = () => {};
      this.post = (_url, data) => {
        posted = JSON.parse(data);
        return '{}';
      };
      this.getStatus = () => this.status;
    }
  };

  vm.runInNewContext(`(function () {\n${script}\n})()`, context, { timeout: 1000 });
  return posted;
}

function sendCard(card) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(card);
    const url = new URL(endpoint);
    const req = https.request({
      hostname: url.hostname,
      port: url.port || 443,
      path: url.pathname + url.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
      }
    }, (res) => {
      let response = '';
      res.on('data', (chunk) => { response += chunk; });
      res.on('end', () => resolve({ status: res.statusCode, response }));
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

(async () => {
  const card = buildCard();
  const result = await sendCard(card);
  console.log(JSON.stringify({
    status: result.status,
    ok: result.status >= 200 && result.status < 300,
    response: result.response
  }, null, 2));
  if (result.status < 200 || result.status >= 300) {
    process.exit(1);
  }
})().catch((error) => {
  console.error(error.message || String(error));
  process.exit(1);
});
