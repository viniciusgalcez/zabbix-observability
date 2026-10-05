import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "backups" / "backup_mediatype_53_before_card_dedup_20260911.json"
OUT_SCRIPT = ROOT / "scripts" / "teams_workflow_card_v2.js"
OUT_REQUEST = ROOT / "zabbix-requests" / "update-teams-card-dedup-20260911.json"


def extract_script() -> str:
    data = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
    return data[0]["script"]


def main() -> None:
    source_data = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
    script = source_data[0]["script"]
    start = script.index("MSTeams.prototype.onCheckParams = function () {")
    end = script.index("\r\nMSTeams.prototype.sendRequest", start)

    replacement = r'''MSTeams.prototype.onCheckParams = function () {
	CParamValidator.validate({
		alert_subject: { type: 'string' }, alert_message: { type: 'string' },
		zabbix_url: { type: 'string', url: true }, teams_endpoint: { type: 'string', url: true }
	}, this.params);

	if (this.params.event_source === '0') {
		CParamValidator.validate({ event_id: { type: 'integer' }, trigger_id: { type: 'integer' } }, this.params);
	}

	var isResolved = (this.params.event_source === '0' && this.params.event_value === '0');
	var nsev = parseInt(this.params.event_nseverity || '0', 10);
	var title = this.params.alert_subject.replace(/^[\u26A0\uFE0F\uD83D\uDFE2\uD83D\uDD34\uD83D\uDFE0\uD83D\uDD35\s]+/, '').trim();
	var statusIcon = isResolved ? '\uD83D\uDFE2' : (nsev >= 4 ? '\uD83D\uDD34' : (nsev >= 2 ? '\uD83D\uDFE0' : '\uD83D\uDD35'));
	var statusStyle = isResolved ? 'good' : (nsev >= 4 ? 'attention' : (nsev >= 2 ? 'warning' : 'accent'));
	var actionUrl = CWebhookHelper.createProblemURL(this.params.event_source, this.params.zabbix_url, this.params.trigger_id, this.params.event_id);

	var parseLines = function(message) {
		var values = {};
		var notes = [];
		var lines = message.split('\n');

		for (var i = 0; i < lines.length; i++) {
			var line = lines[i].replace(/\*\*/g, '').trim();
			if (line === '') {
				continue;
			}

			if (line.length > 350) {
				line = line.substring(0, 347) + '...';
			}

			var sep = line.indexOf(': ');
			if (sep > 0 && sep <= 24) {
				values[line.substring(0, sep).trim()] = line.substring(sep + 2).trim();
			}
			else {
				notes.push(line);
			}
		}

		return { values: values, notes: notes };
	};

	var parsed = parseLines(this.params.alert_message);
	var values = parsed.values;
	var isIPAddress = function(value) {
		if (typeof value !== 'string') {
			return false;
		}
		return /^(?:\d{1,3}\.){3}\d{1,3}$/.test(value) || value.indexOf(':') !== -1;
	};

	var pick = function(keys, fallback) {
		for (var i = 0; i < keys.length; i++) {
			if (typeof values[keys[i]] === 'string' && values[keys[i]] !== '') {
				return values[keys[i]];
			}
		}
		return fallback || '-';
	};

	var formatBrazilDate = function(value) {
		if (typeof value !== 'string') {
			return value;
		}

		return value.replace(/\b(\d{4})\.(\d{2})\.(\d{2})(\s+\d{2}:\d{2}(?::\d{2})?)?/g, function(match, year, month, day, time) {
			return day + '/' + month + '/' + year + (time || '');
		});
	};

	var facts = [
		{ title: 'Severidade', value: pick(['Severidade', 'Severity'], this.params.event_severity || '-') },
		{ title: 'Host', value: pick(['Host'], '-') },
		{ title: 'Endereço', value: isIPAddress(pick(['Endereco', 'Endereço'], '-')) ? pick(['Endereco', 'Endereço'], '-') : (this.params.host_ip || pick(['Endereco', 'Endereço'], '-')) }
	];

	if (isResolved) {
		facts.push({ title: 'Duração', value: pick(['Duracao', 'Duração'], '-') });
		facts.push({ title: 'Resolvido em', value: formatBrazilDate(pick(['Resolvido em', 'Fim'], '-')) });
	}
	else {
		facts.push({ title: 'Início', value: formatBrazilDate(pick(['Inicio', 'Início'], '-')) });
		facts.push({ title: 'Dado operacional', value: pick(['Dado operacional', 'Operational data', 'Valor', 'Valor atual'], '-') });
	}

	var body = [
		{
			type: 'Container',
			style: statusStyle,
			bleed: true,
			spacing: 'None',
			items: [
				{
					type: 'TextBlock',
					text: statusIcon + ' ' + title,
					weight: 'Bolder',
					size: 'Medium',
					wrap: true,
					spacing: 'None'
				}
			]
		},
		{
			type: 'FactSet',
			facts: facts,
			spacing: 'Medium'
		}
	];

	if (parsed.notes.length > 0) {
		body.push({
			type: 'TextBlock',
			text: parsed.notes.join('\n'),
			wrap: true,
			isSubtle: true,
			spacing: 'Medium'
		});
	}

	body.push({
		type: 'TextBlock',
		text: 'Correlação Zabbix: evento ' + (this.params.event_id || '-'),
		wrap: true,
		isSubtle: true,
		size: 'Small',
		spacing: 'Medium'
	});

	this.body = {
		type: 'message',
		attachments: [
			{
				contentType: 'application/vnd.microsoft.card.adaptive',
				contentUrl: null,
				content: {
					$schema: 'http://adaptivecards.io/schemas/adaptive-card.json',
					type: 'AdaptiveCard',
					version: '1.4',
					msteams: { width: 'Full' },
					body: body,
					actions: [
						{
							type: 'Action.OpenUrl',
							title: 'Abrir no Zabbix',
							url: actionUrl
						}
					]
				}
			}
		]
	};
};'''

    new_script = script[:start] + replacement.replace("\n", "\r\n") + script[end:]
    OUT_SCRIPT.write_text(new_script, encoding="utf-8")

    parameters = source_data[0]["parameters"]
    if not any(param["name"] == "host_ip" for param in parameters):
        parameters.append({"name": "host_ip", "value": "{HOST.IP}"})

    request = [
        {
            "arguments": {
                "method": "mediatype.get",
                "params": {
                    "mediatypeids": ["53"],
                    "output": "extend",
                    "selectParameters": "extend",
                    "selectMessageTemplates": "extend"
                }
            },
            "save": "backups/backup_mediatype_53_before_card_dedup_apply_20260911.json",
            "quiet": True
        },
        {
            "arguments": {
                "method": "mediatype.update",
                "params": {
                    "mediatypeid": "53",
                    "script": new_script,
                    "parameters": parameters
                }
            }
        },
        {
            "arguments": {
                "method": "mediatype.get",
                "params": {
                    "mediatypeids": ["53"],
                    "output": ["mediatypeid", "name", "status", "maxattempts"],
                    "selectParameters": "extend",
                    "selectMessageTemplates": "extend"
                }
            },
            "save": "backups/verification_mediatype_53_card_dedup_20260911.json",
            "quiet": True
        }
    ]
    OUT_REQUEST.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "script": str(OUT_SCRIPT),
        "request": str(OUT_REQUEST),
        "bytes": len(new_script.encode("utf-8"))
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
