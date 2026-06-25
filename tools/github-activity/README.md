# GitHub Activity Analyzer

Collect and summarize a user's GitHub activity under an organization, with resume/self-review use cases in mind.

## Data model

The tool stores normalized JSON records in JSONL format. Each record is an `activity` event:

```json
{
  "source": "github",
  "org": "AutoMQ",
  "actor": "Gezi-lzq",
  "repo": "AutoMQ/automq-playground",
  "kind": "pr_authored | issue_authored | pr_involved | issue_involved | pr_reviewed | commented",
  "number": 1103,
  "title": "feat(gcp): add console terraform scaffold",
  "url": "https://github.com/AutoMQ/automq-playground/pull/1103",
  "state": "MERGED",
  "created_at": "2026-06-18T04:00:38Z",
  "updated_at": "2026-06-22T03:15:10Z",
  "closed_at": null,
  "repo_visibility": "PRIVATE",
  "labels": [],
  "raw": {}
}
```

Current collectors:

- `pr_authored`: PRs authored by the actor in the org.
- `issue_authored`: issues authored by the actor in the org.
- `pr_involved`: PRs where the actor is involved, excluding authored duplicates.
- `issue_involved`: issues where the actor is involved, excluding authored duplicates and PRs.
- `pr_reviewed`: PRs reviewed by the actor, excluding authored duplicates.

Notes:

- GitHub Search API is used through `gh search`, so results are subject to GitHub search limits and indexing delay.
- Fine-grained comments/reviews can be added later through GraphQL timeline queries; the MVP starts with search-level evidence because it is fast and robust.
- The output is evidence, not resume prose. Use the summary to find themes, then manually verify before writing a resume.

## Usage

```bash
python tools/github-activity/github_activity.py collect --org AutoMQ --actor Gezi-lzq --since 2024-01-01 --out /tmp/automq-activity.jsonl
python tools/github-activity/github_activity.py summarize --input /tmp/automq-activity.jsonl --markdown /tmp/automq-activity.md
```

Or via mise:

```bash
mise run github-activity:collect -- --org AutoMQ --actor Gezi-lzq --since 2024-01-01 --out /tmp/automq-activity.jsonl
mise run github-activity:summarize -- --input /tmp/automq-activity.jsonl --markdown /tmp/automq-activity.md
```

## Resume-oriented interpretation

The tool intentionally groups evidence by:

1. repository,
2. activity kind,
3. month,
4. title keywords.

This helps identify contribution threads such as:

- Agent / AI collaboration infrastructure,
- Playground / Infra resource model and automation,
- testing / verification / engineering quality,
- release / operational maintenance.
