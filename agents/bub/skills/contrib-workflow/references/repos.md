# Repository Relationships

## Upstream

- **bubbuild/bub** — Core framework
- **bubbuild/bub-contrib** — Official plugins (bub-schedule, bub-codex, bub-tapestore-sqlite, bub-qq, bub-feishu, etc.)

## Fork (Gezi-lzq)

- **Gezi-lzq/bub-contrib** — Fork of bubbuild/bub-contrib. Used for patches before upstream merges.
- **Gezi-lzq/bub** — Fork of bubbuild/bub.

## Deployment

- **Gezi-lzq/SelfOps** — Declarative deployment repo. Contains agent profiles under `agents/bub/profiles/<name>/`.
  - `bub-reqs.txt` — Plugin dependencies (pip requirements format with git+https URLs)
  - `docker-compose.yml` — Container config
  - `env.template` — Required env vars

## Dependency Pinning Convention

In `bub-reqs.txt`:
- Upstream (unpinned): `bub-schedule @ git+https://github.com/bubbuild/bub-contrib.git#subdirectory=packages/bub-schedule`
- Fork (pinned to commit): `bub-schedule @ git+https://github.com/Gezi-lzq/bub-contrib.git@<commit-hash>#subdirectory=packages/bub-schedule`

Always pin to a specific commit hash when using fork, never to a branch name.
