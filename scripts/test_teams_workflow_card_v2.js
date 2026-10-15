const fs = require('fs');
const vm = require('vm');

const script = fs.readFileSync('scripts/teams_workflow_card_v2.js', 'utf8');

function runWebhook(params) {
  let posted = null;
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

const base = {
  alert_subject: 'SRV-TESTE-01 · CPU elevada',
  zabbix_url: 'https://zabbix.capricornio.corp.br',
  teams_endpoint: 'https://example.invalid/workflow',
  host_ip: '127.0.0.1',
  event_source: '0',
  event_update_status: '0',
  event_update_nseverity: '4',
  event_update_severity: 'High',
  event_nseverity: '4',
  event_severity: 'High',
  trigger_id: '12345',
  event_id: 'teams-card-v2-test-001'
};

const active = runWebhook({
  ...base,
  event_value: '1',
  event_id: '1001',
  alert_message: [
    'Estado: INCIDENTE ATIVO',
    'Severidade: High',
    'Host: SRV-TESTE-01',
    'Endereco: BGP-ADM-UPS01',
    'Inicio: 2026.09.09 14:30:00',
    'Dado operacional: CPU 97%',
    'Valor atual: 97%',
    'Evento: 1001'
  ].join('\n')
});

const resolved = runWebhook({
  ...base,
  event_value: '0',
  event_id: '1002',
  alert_message: [
    'Estado: RESOLVIDO',
    'Severidade: High',
    'Host: SRV-TESTE-01',
    'Endereco: BGP-ADM-UPS01',
    'Duracao: 1m 00s',
    'Resolvido em: 2026.09.09 14:31:00',
    'Evento: 1002'
  ].join('\n')
});

function inspect(card) {
  const content = card.attachments[0].content;
  const header = content.body[0];
  const facts = content.body[1].facts;
  return {
    type: card.type,
    contentType: card.attachments[0].contentType,
    version: content.version,
    headerStyle: header.style,
    headerText: header.items.map((item) => item.text),
    facts,
    action: content.actions[0]
  };
}

const activeInfo = inspect(active);
const resolvedInfo = inspect(resolved);

if (activeInfo.headerStyle !== 'attention') throw new Error('active card style mismatch');
if (activeInfo.headerText.length !== 1 || !activeInfo.headerText[0].startsWith('🔴 ')) throw new Error('active header should only show status dot and title');
if (activeInfo.headerText.join(' ').includes('INCIDENTE ATIVO')) throw new Error('active status text should not be shown');
if (activeInfo.facts.some((fact) => fact.title === 'Estado')) throw new Error('status must appear only in header');
if (activeInfo.facts.some((fact) => fact.title === 'Evento')) throw new Error('event id must appear only in correlation footer');
if (!activeInfo.facts.some((fact) => fact.title === 'Dado operacional' && fact.value === 'CPU 97%')) {
  throw new Error('active operational data missing');
}
if (!activeInfo.facts.some((fact) => fact.title === 'Endereço' && fact.value === '127.0.0.1')) {
  throw new Error('host IP fallback missing');
}
if (JSON.stringify(active).includes('Ação sugerida')) {
  throw new Error('suggested action must not appear in card');
}
if (JSON.stringify(active).includes('serviços afetados')) {
  throw new Error('recommendation text must not appear in card');
}
if (resolvedInfo.headerStyle !== 'good') throw new Error('resolved card style mismatch');
if (resolvedInfo.headerText.length !== 1 || !resolvedInfo.headerText[0].startsWith('🟢')) throw new Error('resolved header must contain only the green icon and title');
if (resolvedInfo.facts.some((fact) => fact.title === 'Estado')) throw new Error('resolved status must appear only in header');
if (resolvedInfo.facts.some((fact) => fact.title === 'Evento')) throw new Error('resolved event id must appear only in correlation footer');
if ((JSON.stringify(active).match(/Correlação Zabbix: evento/g) || []).length !== 1) {
  throw new Error('active correlation must appear exactly once');
}
if (!activeInfo.facts.some((fact) => fact.title === 'Início' && fact.value === '09/09/2026 14:30:00')) {
  throw new Error('active date format mismatch');
}
if (!resolvedInfo.facts.some((fact) => fact.title === 'Resolvido em' && fact.value === '09/09/2026 14:31:00')) {
  throw new Error('resolved timestamp missing');
}
if (activeInfo.action.title !== 'Abrir no Zabbix') throw new Error('zabbix action missing');

console.log(JSON.stringify({ active: activeInfo, resolved: resolvedInfo }, null, 2));
