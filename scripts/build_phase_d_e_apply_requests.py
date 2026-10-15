import json
from pathlib import Path

causes = json.loads(Path("backups/phase_d_verify_physical_causes_have_notify_teams_20260930.json").read_text(encoding="utf-8"))
for trigger in causes:
    has = any(tag["tag"] == "notify" and tag["value"] == "teams" for tag in trigger.get("tags", []))
    print(trigger["triggerid"], "teams=" + str(has), trigger.get("event_name") or trigger.get("description"))

aggs = json.loads(Path("backups/phase_d_aggregates_tags_before_strip_teams_20260930.json").read_text(encoding="utf-8"))
reqs = []
for trigger in aggs:
    new_tags = [
        {"tag": tag["tag"], "value": tag["value"]}
        for tag in trigger.get("tags", [])
        if not (tag["tag"] == "notify" and tag["value"] == "teams")
    ]
    if not any(tag["tag"] == "notify" for tag in new_tags):
        new_tags.append({"tag": "notify", "value": "telegram"})
    tid = trigger["triggerid"]
    print("agg", tid, "notify_after", [t for t in new_tags if t["tag"] == "notify"])
    reqs.append(
        {
            "arguments": {
                "method": "trigger.update",
                "params": {"triggerid": tid, "tags": new_tags},
            },
            "save": f"backups/phase_d_strip_teams_agg_{tid}_20260930.json",
        }
    )

reqs.append(
    {
        "arguments": {"method": "correlation.update", "params": {"correlationid": "16", "status": 1}},
        "save": "backups/phase_e_disable_correlation_16_20260930.json",
    }
)
reqs.append(
    {
        "arguments": {"method": "correlation.update", "params": {"correlationid": "45", "status": 1}},
        "save": "backups/phase_e_disable_correlation_45_20260930.json",
    }
)

Path("zabbix-requests/phase_d_e_strip_agg_teams_and_disable_close_new_20260930.json").write_text(
    json.dumps(reqs, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("requests", len(reqs))
