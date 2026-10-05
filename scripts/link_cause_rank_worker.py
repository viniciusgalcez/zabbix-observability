"""Rank open link symptoms under their active Zabbix link-cause root.

Works across all Capricornio firewall host groups. Dry-run is the default.
Credentials come from environment variables, never from files.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

FIREWALL_GROUP_IDS = ["27", "28", "29", "30", "31", "98", "99", "100"]
MATRIX_PATH = Path("reports/link-correlation-matrix-20260930.csv")
TAG_KEYS = ("depends-on", "interface", "sdwan-if")


class ZabbixClient:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self.sequence = 0

    def call(self, method: str, params: dict):
        self.sequence += 1
        body = json.dumps(
            {"jsonrpc": "2.0", "method": method, "params": params, "id": self.sequence}
        ).encode("utf-8")
        request = Request(
            self.url,
            body,
            {
                "Content-Type": "application/json-rpc",
                "Authorization": "Bearer " + self.token,
            },
        )
        with urlopen(request, timeout=60) as response:
            result = json.load(response)
        if "error" in result:
            error = result["error"]
            raise RuntimeError(
                f"{method}: {error.get('message', 'API error')}: {error.get('data', '')}"
            )
        return result["result"]


def load_cause_dependencies(matrix_path: Path) -> dict[str, set[str]]:
    cause_deps: dict[str, set[str]] = defaultdict(set)
    with matrix_path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            for cause in row["causes"].split(";"):
                cause = cause.strip()
                if not cause:
                    continue
                for dep in row["dependencies"].split(";"):
                    dep = dep.strip()
                    if dep:
                        cause_deps[cause].add(dep)
    return cause_deps


def tag_map(problem: dict) -> dict[str, list[str]]:
    tags: dict[str, list[str]] = defaultdict(list)
    for tag in problem.get("tags", []):
        tags[tag["tag"]].append(tag["value"])
    return tags


def has_tag(problem: dict, tag: str, value: str) -> bool:
    return any(
        item.get("tag") == tag and item.get("value") == value
        for item in problem.get("tags", [])
    )


def dependency_values(problem: dict) -> list[str]:
    tags = tag_map(problem)
    values: list[str] = []
    for key in TAG_KEYS:
        values.extend(tags.get(key, []))
    return values


def match_dep(value: str, dependencies: set[str]) -> str | None:
    if not value:
        return None
    exact = [dep for dep in dependencies if dep and value == dep]
    if exact:
        return max(exact, key=len)

    candidates = []
    for dep in dependencies:
        if not dep:
            continue
        boundary = re.search(rf"(^|[_-]){re.escape(dep)}($|[_-])", value)
        concat = re.match(rf"^{re.escape(dep)}[A-Za-z0-9]", value)
        if boundary or concat:
            candidates.append(dep)
    if not candidates:
        return None

    best = max(candidates, key=len)
    longer = [
        dep for dep in dependencies
        if dep.startswith(best) and dep != best and value.startswith(dep)
    ]
    if longer:
        return max(longer, key=len)

    if value != best and value.startswith(best):
        rest = value[len(best):]
        variant = re.match(r"^[_-]W(\d)", rest)
        if variant:
            best_variant = re.search(r"W(\d)$", best)
            if best_variant and best_variant.group(1) != variant.group(1):
                return None
        elif re.match(r"^[_-]ISP", rest, re.I):
            return None
    return best


def matches_dependencies(problem: dict, dependencies: set[str]) -> str | None:
    for value in dependency_values(problem):
        matched = match_dep(value, dependencies)
        if matched:
            return matched
    return None


def choose_roots(problems: list[dict]) -> list[dict]:
    roots = []
    for problem in problems:
        if str(problem.get("cause_eventid", "0")) != "0":
            continue
        link_causes = tag_map(problem).get("link-cause", [])
        if len(link_causes) != 1:
            continue
        roots.append(problem)
    return roots


def reconcile(client: ZabbixClient, matrix_path: Path, backup_dir: Path, apply: bool) -> int:
    if not matrix_path.exists():
        raise RuntimeError(f"Correlation matrix not found: {matrix_path}")
    cause_deps = load_cause_dependencies(matrix_path)

    hosts = client.call(
        "host.get",
        {
            "output": ["hostid", "host"],
            "groupids": FIREWALL_GROUP_IDS,
            "filter": {"status": 0},
        },
    )
    hostids = [host["hostid"] for host in hosts]
    host_names = {host["hostid"]: host["host"] for host in hosts}
    if not hostids:
        raise RuntimeError("No enabled firewall hosts found")

    problems = client.call(
        "problem.get",
        {
            "output": "extend",
            "hostids": hostids,
            "source": 0,
            "object": 0,
            "selectTags": "extend",
            "sortfield": ["eventid"],
            "sortorder": "DESC",
            "limit": 1000,
        },
    )
    if len(problems) == 1000:
        raise RuntimeError("Problem list hit its limit; no changes made")

    # Attach host names via event.get for reporting only.
    event_hosts = {
        event["eventid"]: ",".join(item["host"] for item in event.get("hosts", []))
        for event in client.call(
            "event.get",
            {
                "eventids": [problem["eventid"] for problem in problems],
                "output": ["eventid"],
                "selectHosts": ["host"],
            },
        )
    }

    roots = choose_roots(problems)
    plan = []
    ambiguous = []
    for root in roots:
        link_cause = tag_map(root)["link-cause"][0]
        dependencies = cause_deps.get(link_cause, set())
        if not dependencies:
            ambiguous.append(
                {
                    "root_eventid": root["eventid"],
                    "link_cause": link_cause,
                    "reason": "no dependencies in matrix",
                }
            )
            continue
        for problem in problems:
            if problem["eventid"] == root["eventid"]:
                continue
            if str(problem.get("cause_eventid", "0")) != "0":
                continue
            if int(problem.get("clock", 0)) < int(root.get("clock", 0)):
                continue
            matched = matches_dependencies(problem, dependencies)
            if not matched and has_tag(problem, "link-cause", link_cause):
                # Aggregate cause on same circuit, e.g. SPO_ISP1_VPN under SPO_VIVO
                # is handled only when the open root's own link-cause equals the symptom.
                matched = link_cause
            if not matched:
                continue
            # If another open root also matches this symptom, skip to avoid wrong parent.
            other_matches = []
            for other in roots:
                if other["eventid"] == root["eventid"]:
                    continue
                other_cause = tag_map(other)["link-cause"][0]
                other_deps = cause_deps.get(other_cause, set())
                if matches_dependencies(problem, other_deps) or has_tag(
                    problem, "link-cause", other_cause
                ):
                    other_matches.append(other["eventid"])
            if other_matches:
                ambiguous.append(
                    {
                        "symptom_eventid": problem["eventid"],
                        "candidate_roots": [root["eventid"], *other_matches],
                        "reason": "ambiguous root",
                    }
                )
                continue
            plan.append(
                {
                    "cause_eventid": root["eventid"],
                    "link_cause": link_cause,
                    "symptom_eventid": problem["eventid"],
                    "matched_dep": matched,
                    "host": event_hosts.get(problem["eventid"], ""),
                    "name": problem.get("name", ""),
                }
            )

    summary = {
        "firewall_hosts": sorted(host_names.values()),
        "open_roots": [
            {
                "eventid": root["eventid"],
                "link_cause": tag_map(root)["link-cause"][0],
                "host": event_hosts.get(root["eventid"], ""),
                "name": root.get("name", ""),
            }
            for root in roots
        ],
        "candidates": plan,
        "ambiguous": ambiguous,
        "mode": "apply" if apply else "dry-run",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if not apply:
        return len(plan)

    backup_dir.mkdir(parents=True, exist_ok=True)
    for item in plan:
        cause_id = str(item["cause_eventid"])
        event_id = str(item["symptom_eventid"])
        fresh = client.call(
            "problem.get",
            {
                "output": "extend",
                "eventids": [event_id],
                "selectTags": "extend",
                "selectAcknowledges": "extend",
            },
        )
        roots_now = client.call(
            "problem.get",
            {"output": "extend", "eventids": [cause_id], "selectTags": "extend"},
        )
        if (
            len(fresh) != 1
            or len(roots_now) != 1
            or str(fresh[0].get("cause_eventid", "0")) != "0"
            or str(roots_now[0].get("cause_eventid", "0")) != "0"
        ):
            print(json.dumps({"skipped_eventid": event_id, "reason": "state changed"}))
            continue
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = backup_dir / f"link_cause_before_rank_{event_id}_{stamp}.json"
        backup.write_text(
            json.dumps({"root": roots_now[0], "symptom": fresh[0]}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        client.call(
            "event.acknowledge",
            {
                "eventids": [event_id],
                "action": 260,
                "cause_eventid": cause_id,
                "message": (
                    f"Sintoma da causa {item['link_cause']}. "
                    f"Causa: evento {cause_id}."
                ),
            },
        )
        # event.get can lag briefly after event.acknowledge; retry then continue
        # the batch instead of aborting remaining ranks.
        verified_cause = "0"
        for _ in range(12):
            verified = client.call(
                "event.get",
                {
                    "output": ["eventid", "cause_eventid"],
                    "eventids": [event_id],
                },
            )
            if verified and str(verified[0].get("cause_eventid", "0")) == cause_id:
                verified_cause = cause_id
                break
            time.sleep(0.5)
        if verified_cause != cause_id:
            print(
                json.dumps(
                    {
                        "rank_unverified_eventid": event_id,
                        "expected_cause_eventid": cause_id,
                        "observed_cause_eventid": (
                            verified[0].get("cause_eventid") if verified else None
                        ),
                        "backup": str(backup),
                    }
                )
            )
            continue
        print(json.dumps({"ranked_eventid": event_id, "cause_eventid": cause_id, "backup": str(backup)}))
    return len(plan)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write ranks after fresh backup")
    parser.add_argument("--backup-dir", type=Path, default=Path("backups"))
    parser.add_argument("--matrix", type=Path, default=MATRIX_PATH)
    parser.add_argument(
        "--allow-http",
        action="store_true",
        help="Allow plain HTTP to a non-loopback Zabbix URL (lab/internal only)",
    )
    args = parser.parse_args()

    url = os.environ.get("ZABBIX_URL", "")
    token = os.environ.get("ZABBIX_API_TOKEN") or os.environ.get("ZABBIX_TOKEN", "")
    if not url or not token:
        parser.error("ZABBIX_URL and ZABBIX_API_TOKEN (or ZABBIX_TOKEN) must be set")
    if not url.endswith("api_jsonrpc.php"):
        url = url.rstrip("/") + "/api_jsonrpc.php"
    parsed = urlparse(url)
    if parsed.scheme != "https" and not (
        parsed.scheme == "http"
        and (
            args.allow_http
            or parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        )
    ):
        parser.error("Use HTTPS for ZABBIX_URL, or pass --allow-http for internal HTTP")

    try:
        reconcile(ZabbixClient(url, token), args.matrix, args.backup_dir, args.apply)
    except Exception as exc:
        print(f"Link-cause reconciliation stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
