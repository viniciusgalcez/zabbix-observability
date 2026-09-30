"""Associate unambiguous SPO/Vivo symptoms with their open Zabbix root event.

Run on the Zabbix server or another approved server-side executor. Dry-run is the
default. Credentials are supplied through environment variables, never files.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


HOST_ID = "10758"
ROOT_TRIGGER_ID = "50308"
VPN_AGGREGATE_TRIGGER_ID = "55144"
ROOT_TAG = ("link-cause", "SPO_VIVO")


class ZabbixClient:
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.sequence = 0

    def call(self, method, params):
        self.sequence += 1
        body = json.dumps({"jsonrpc": "2.0", "method": method,
                           "params": params, "id": self.sequence}).encode("utf-8")
        request = Request(self.url, body, {
            "Content-Type": "application/json-rpc",
            "Authorization": "Bearer " + self.token,
        })
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
        if "error" in result:
            error = result["error"]
            raise RuntimeError(f"{method}: {error.get('message', 'API error')}: "
                               f"{error.get('data', '')}")
        return result["result"]


def has_tag(problem, tag, value):
    return any(t.get("tag") == tag and t.get("value") == value
               for t in problem.get("tags", []))


def choose_root(problems):
    roots = [p for p in problems if str(p.get("objectid")) == ROOT_TRIGGER_ID
             and str(p.get("cause_eventid", "0")) == "0"
             and has_tag(p, *ROOT_TAG)]
    if len(roots) != 1:
        raise RuntimeError(f"Expected one open SPO/Vivo root, found {len(roots)}; no changes made")
    return roots[0]


def is_proven_symptom(problem, root):
    if problem.get("eventid") == root.get("eventid"):
        return False
    if str(problem.get("cause_eventid", "0")) != "0":
        return False
    if int(problem.get("clock", 0)) < int(root.get("clock", 0)):
        return False
    if str(problem.get("objectid")) == VPN_AGGREGATE_TRIGGER_ID:
        return True
    # A named ISP1_VIVO interface is direct evidence of this physical link.
    # Other tunnels/SD-WAN checks need a confirmed topology map first.
    return (has_tag(problem, "component", "sd-wan") and
            (has_tag(problem, "interface", "ISP1_VIVO") or
             has_tag(problem, "sdwan-if", "ISP1_VIVO")))


def reconcile(client, backup_dir, apply=False):
    problems = client.call("problem.get", {
        "output": "extend", "hostids": [HOST_ID], "source": 0, "object": 0,
        "selectTags": "extend", "sortfield": ["eventid"],
        "sortorder": "DESC", "limit": 500,
    })
    if len(problems) == 500:
        raise RuntimeError("Problem list hit its limit; no changes made")
    root = choose_root(problems)
    cause_id = str(root["eventid"])
    candidates = [p for p in problems if is_proven_symptom(p, root)]
    print(json.dumps({"root_eventid": cause_id,
                      "candidate_eventids": [p["eventid"] for p in candidates],
                      "mode": "apply" if apply else "dry-run"}))
    if not apply:
        return len(candidates)
    backup_dir.mkdir(parents=True, exist_ok=True)
    for problem in candidates:
        event_id = str(problem["eventid"])
        # Re-read immediately before the mutation to avoid ranking a recovered
        # or already processed event. Save both objects as the required backup.
        fresh = client.call("problem.get", {
            "output": "extend", "eventids": [event_id],
            "selectTags": "extend", "selectAcknowledges": "extend",
        })
        roots = client.call("problem.get", {
            "output": "extend", "eventids": [cause_id], "selectTags": "extend",
        })
        if (len(fresh) != 1 or len(roots) != 1 or
                str(roots[0].get("objectid")) != ROOT_TRIGGER_ID or
                str(roots[0].get("cause_eventid", "0")) != "0" or
                not has_tag(roots[0], *ROOT_TAG) or
                not is_proven_symptom(fresh[0], roots[0])):
            print(json.dumps({"skipped_eventid": event_id, "reason": "state changed"}))
            continue
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = backup_dir / f"spo_vivo_before_rank_{event_id}_{stamp}.json"
        backup.write_text(json.dumps({"root": roots[0], "symptom": fresh[0]},
                                     ensure_ascii=False, indent=2), encoding="utf-8")
        client.call("event.acknowledge", {
            "eventids": [event_id], "action": 256, "cause_eventid": cause_id,
        })
        verified = client.call("problem.get", {
            "output": ["eventid", "cause_eventid"], "eventids": [event_id],
        })
        if len(verified) != 1 or str(verified[0].get("cause_eventid")) != cause_id:
            raise RuntimeError(f"Rank verification failed for event {event_id}; stopped")
        print(json.dumps({"ranked_eventid": event_id, "backup": str(backup)}))
    return len(candidates)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write ranks after fresh backup")
    parser.add_argument("--backup-dir", type=Path, default=Path("backups"))
    args = parser.parse_args()
    url = os.environ.get("ZABBIX_URL", "")
    token = os.environ.get("ZABBIX_API_TOKEN", "")
    if not url or not token:
        parser.error("ZABBIX_URL and ZABBIX_API_TOKEN must be set")
    parsed = urlparse(url)
    if parsed.scheme != "https" and not (parsed.scheme == "http" and
                                         parsed.hostname in {"127.0.0.1", "localhost", "::1"}):
        parser.error("Use HTTPS for ZABBIX_URL, or HTTP only on loopback")
    try:
        reconcile(ZabbixClient(url, token), args.backup_dir, args.apply)
    except Exception as exc:
        print(f"SPO/Vivo reconciliation stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
