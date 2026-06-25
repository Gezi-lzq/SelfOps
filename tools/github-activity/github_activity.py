#!/usr/bin/env python3
"""Collect and summarize GitHub activity for resume/self-review.

This script shells out to `gh search` so it works with the existing GitHub CLI auth.
"""
from __future__ import annotations

import argparse
import collections
import dataclasses
import datetime as dt
import json
import pathlib
import subprocess
import sys
from typing import Any, Iterable

PR_JSON_FIELDS = "assignees,author,authorAssociation,body,closedAt,commentsCount,createdAt,id,isDraft,isLocked,isPullRequest,labels,number,repository,state,title,updatedAt,url"
ISSUE_JSON_FIELDS = "assignees,author,authorAssociation,body,closedAt,commentsCount,createdAt,id,isLocked,isPullRequest,labels,number,repository,state,title,updatedAt,url"


@dataclasses.dataclass(frozen=True)
class Activity:
    source: str
    org: str
    actor: str
    repo: str
    kind: str
    number: int
    title: str
    url: str
    state: str | None
    created_at: str | None
    updated_at: str | None
    closed_at: str | None
    labels: list[str]
    raw: dict[str, Any]

    @property
    def key(self) -> tuple[str, int, str]:
        return (self.repo, self.number, self.kind)


def run_json(cmd: list[str]) -> Any:
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{proc.stderr.strip()}")
    if not proc.stdout.strip():
        return []
    return json.loads(proc.stdout)


def repo_name(item: dict[str, Any]) -> str:
    repo = item.get("repository") or {}
    if isinstance(repo, dict):
        return repo.get("nameWithOwner") or repo.get("fullName") or repo.get("name") or ""
    return str(repo)


def normalize(item: dict[str, Any], *, org: str, actor: str, kind: str) -> Activity:
    labels = []
    for label in item.get("labels") or []:
        if isinstance(label, dict):
            labels.append(label.get("name", ""))
        else:
            labels.append(str(label))
    return Activity(
        source="github",
        org=org,
        actor=actor,
        repo=repo_name(item),
        kind=kind,
        number=int(item.get("number") or 0),
        title=item.get("title") or "",
        url=item.get("url") or "",
        state=item.get("state"),
        created_at=item.get("createdAt"),
        updated_at=item.get("updatedAt"),
        closed_at=item.get("closedAt"),
        labels=[x for x in labels if x],
        raw=item,
    )


def gh_search_prs(*, org: str, actor: str, qualifier: str, since: str | None, limit: int) -> list[dict[str, Any]]:
    cmd = ["gh", "search", "prs", f"org:{org}", f"{qualifier}:{actor}", "--limit", str(limit), "--json", PR_JSON_FIELDS]
    if since:
        # `updated:` is better for involvement discovery than `created:`.
        cmd += ["--updated", f">={since}"]
    return run_json(cmd)


def gh_search_issues(*, org: str, actor: str, qualifier: str, since: str | None, limit: int) -> list[dict[str, Any]]:
    cmd = ["gh", "search", "issues", f"org:{org}", f"{qualifier}:{actor}", "--limit", str(limit), "--json", ISSUE_JSON_FIELDS]
    if since:
        cmd += ["--updated", f">={since}"]
    return run_json(cmd)


def collect(org: str, actor: str, since: str | None, limit: int) -> list[Activity]:
    activities: list[Activity] = []
    specs = [
        ("pr_authored", gh_search_prs, "author"),
        ("issue_authored", gh_search_issues, "author"),
        ("pr_involved", gh_search_prs, "involves"),
        ("issue_involved", gh_search_issues, "involves"),
        ("pr_reviewed", gh_search_prs, "reviewed-by"),
    ]
    for kind, func, qualifier in specs:
        for item in func(org=org, actor=actor, qualifier=qualifier, since=since, limit=limit):
            # gh search issues may include PRs on some query shapes; keep issue_* as issues only.
            if kind.startswith("issue") and item.get("isPullRequest"):
                continue
            activities.append(normalize(item, org=org, actor=actor, kind=kind))

    # Deduplicate exact kind records while preserving distinct evidence kinds for same PR/issue.
    seen: set[tuple[str, int, str]] = set()
    out: list[Activity] = []
    for a in sorted(activities, key=lambda x: (x.updated_at or "", x.repo, x.number, x.kind), reverse=True):
        if a.key in seen:
            continue
        seen.add(a.key)
        out.append(a)
    return out


def write_jsonl(path: pathlib.Path, activities: Iterable[Activity]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for a in activities:
            f.write(json.dumps(dataclasses.asdict(a), ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def month_of(value: str | None) -> str:
    if not value:
        return "unknown"
    return value[:7]


def keyword_buckets(title: str) -> list[str]:
    t = title.lower()
    buckets = []
    rules = {
        "agent/ai": ["agent", "skill", "mcp", "codex", "claude", "bub", "rig"],
        "playground/infra": ["playground", "terraform", "gcp", "aws", "aliyun", "pve", "console", "cmp", "cluster", "resource", "registry"],
        "testing/verification": ["test", "e2e", "verification", "smoke", "marathon", "jepsen"],
        "observability/ops": ["log", "metric", "monitor", "observability", "health", "triage", "ops"],
        "release/maintenance": ["release", "chore", "fix", "cleanup", "refactor"],
        "data/storage": ["s3", "wal", "iceberg", "table", "stream", "storage", "object"],
    }
    for bucket, words in rules.items():
        if any(w in t for w in words):
            buckets.append(bucket)
    return buckets or ["other"]


def summarize(records: list[dict[str, Any]]) -> str:
    by_repo = collections.Counter(r["repo"] for r in records)
    by_kind = collections.Counter(r["kind"] for r in records)
    by_month = collections.Counter(month_of(r.get("updated_at") or r.get("created_at")) for r in records)
    by_bucket: collections.Counter[str] = collections.Counter()
    for r in records:
        for b in keyword_buckets(r.get("title") or ""):
            by_bucket[b] += 1

    lines = []
    lines.append("# GitHub Activity Summary")
    lines.append("")
    if records:
        actor = records[0].get("actor")
        org = records[0].get("org")
        lines.append(f"- Actor: `{actor}`")
        lines.append(f"- Organization: `{org}`")
    lines.append(f"- Records: {len(records)}")
    lines.append("")

    def section(title: str, counter: collections.Counter[str], n: int = 15):
        lines.append(f"## {title}")
        lines.append("")
        for k, v in counter.most_common(n):
            lines.append(f"- {k}: {v}")
        lines.append("")

    section("By repository", by_repo)
    section("By activity kind", by_kind)
    section("By month", by_month, 24)
    section("Resume-oriented keyword buckets", by_bucket)

    lines.append("## Recent evidence")
    lines.append("")
    for r in sorted(records, key=lambda x: x.get("updated_at") or x.get("created_at") or "", reverse=True)[:40]:
        when = (r.get("updated_at") or r.get("created_at") or "")[:10]
        lines.append(f"- {when} `{r['kind']}` {r['repo']}#{r['number']} {r['title']} — {r['url']}")
    lines.append("")

    lines.append("## How to use this for a resume")
    lines.append("")
    lines.append("Do not copy raw activity lines directly. First cluster them into contribution threads, then write impact-oriented bullets:")
    lines.append("")
    lines.append("- Problem/context → action/mechanism → measurable or qualitative impact.")
    lines.append("- Prefer a few coherent threads over many fragmented tasks.")
    lines.append("- Manually verify each bullet against code/PR evidence before using it externally.")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("collect")
    p.add_argument("--org", default="AutoMQ")
    p.add_argument("--actor", default="Gezi-lzq")
    p.add_argument("--since", help="YYYY-MM-DD; filters by updated date")
    p.add_argument("--limit", type=int, default=1000, help="per query limit")
    p.add_argument("--out", required=True)

    p = sub.add_parser("summarize")
    p.add_argument("--input", required=True)
    p.add_argument("--markdown", required=True)

    args = parser.parse_args(argv)
    if args.cmd == "collect":
        activities = collect(args.org, args.actor, args.since, args.limit)
        write_jsonl(pathlib.Path(args.out), activities)
        print(f"wrote {len(activities)} records to {args.out}")
        return 0
    if args.cmd == "summarize":
        records = read_jsonl(pathlib.Path(args.input))
        md = summarize(records)
        out = pathlib.Path(args.markdown)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"wrote summary to {out}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
