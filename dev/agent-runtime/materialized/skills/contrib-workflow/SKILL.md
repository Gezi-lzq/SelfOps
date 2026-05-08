---
name: contrib-workflow
description: |
  Full workflow for managing bub plugins: modify existing plugins, create new plugins, and configure which plugins each agent uses.
  Plugins can live in Gezi-lzq/bub-contrib (shared) or SelfOps (deployment-specific).
  Use when Bub needs to: (1) Fix a bug or add a feature to an existing plugin, (2) Create a new plugin,
  (3) Configure which plugins an agent profile uses, (4) Submit PRs and manage the fork workflow,
  (5) Merge approved PRs.
---

# Contrib Workflow

End-to-end procedure for managing bub plugins: modify, create, configure, and deploy.

## Repository Context

See [references/repos.md](references/repos.md) for repo relationships and pinning conventions.

## Where Plugins Live

| Location | When to use |
|----------|-------------|
| `Gezi-lzq/bub-contrib` (packages/) | Shared plugins usable by any agent. Fork of upstream bubbuild/bub-contrib. |
| `Gezi-lzq/SelfOps` (agents/bub/plugins/) | Deployment-specific plugins, tightly coupled to a particular agent setup. |

## Workflow A: Modify an Existing Plugin (fix or feat)

### 1. Identify the target

- Installed source: `/app/.venv/lib/python3.12/site-packages/<package_name>/`
- Repo source: `packages/<plugin>/src/` in bub-contrib

### 2. Create branch on fork

```bash
cd /tmp
git clone https://x-access-token:$(gh auth token)@github.com/Gezi-lzq/bub-contrib.git
cd bub-contrib
git checkout -b <type>/<short-description>   # type: fix or feat
```

### 3. Implement changes

Edit files under `packages/<plugin>/src/`. Test locally if possible.

### 4. Commit, push, PR

```bash
git add <files>
git commit -m "<type>(<plugin>): <description>"
git push -u origin <type>/<short-description>
gh pr create --repo Gezi-lzq/bub-contrib --base main --head <branch> \
  --title "<type>(<plugin>): <short title>" --body "<description>"
```

### 5. Update SelfOps to use the change

See "Workflow D: Configure Agent Plugins" below.

## Workflow B: Create a New Plugin in bub-contrib

### 1. Scaffold

```bash
cd /tmp/bub-contrib
mkdir -p packages/<plugin-name>/src/<package_name>
```

Structure:
```
packages/<plugin-name>/
├── pyproject.toml
├── src/
│   └── <package_name>/
│       ├── __init__.py
│       └── plugin.py
└── tests/
```

### 2. pyproject.toml

```toml
[project]
name = "<plugin-name>"
version = "0.1.0"
dependencies = ["bub"]

[project.entry-points.bub]
<plugin-name> = "<package_name>.plugin:main"
```

### 3. Implement plugin

```python
# plugin.py
from bub import hookimpl
from bub.types import Envelope, State

class MyPluginImpl:
    def __init__(self):
        pass  # import tools module here if needed

    @hookimpl
    def load_state(self, message: Envelope, session_id: str) -> State:
        return {"my_key": "my_value"}

main = MyPluginImpl()
```

### 4. Commit, push, PR (same as Workflow A step 4)

## Workflow C: Create a Plugin in SelfOps

For deployment-specific plugins that don't belong in bub-contrib.

### 1. Scaffold in SelfOps

```bash
cd /tmp/SelfOps
mkdir -p agents/bub/plugins/<plugin-name>/src/<package_name>
```

Same structure as Workflow B.

### 2. Reference in bub-reqs.txt

```
<plugin-name> @ file:///app/plugins/<plugin-name>
```

### 3. Ensure deploy.sh syncs plugins/ into the container

## Workflow D: Configure Agent Plugins

Each agent profile declares its plugins in:
```
agents/bub/profiles/<profile>/bub-reqs.txt
```

### Add/change a plugin

```bash
cd /tmp
git clone https://x-access-token:$(gh auth token)@github.com/Gezi-lzq/SelfOps.git
cd SelfOps
git checkout -b <type>/update-<profile>-plugins
```

Edit `bub-reqs.txt`. Formats:

```
# From upstream (pinned)
<plugin> @ git+https://github.com/bubbuild/bub-contrib.git@<commit>#subdirectory=packages/<plugin>

# From fork (pinned)
<plugin> @ git+https://github.com/Gezi-lzq/bub-contrib.git@<commit>#subdirectory=packages/<plugin>

# Local plugin in SelfOps
<plugin> @ file:///app/plugins/<plugin>
```

### Get commit hash

```bash
# Fork latest
cd /tmp/bub-contrib && git rev-parse HEAD

# Or specific branch
cd /tmp/bub-contrib && git rev-parse <branch-name>

# Upstream latest
gh api repos/bubbuild/bub-contrib/commits/main --jq .sha
```

### Submit PR

```bash
git add agents/bub/profiles/<profile>/bub-reqs.txt
git commit -m "<type>(<profile>): <description>"
git push -u origin <branch>
gh pr create --repo Gezi-lzq/SelfOps --base main --head <branch> \
  --title "<type>(<profile>): <short title>" --body "<description>"
```

## Workflow E: Merge Approved PRs

When user approves:
```bash
gh pr merge <PR-number> --repo <owner/repo> --squash
```

## Workflow F: Upstream a Fork Fix/Feat

After validation on fork:
1. Create PR from `Gezi-lzq/bub-contrib` → `bubbuild/bub-contrib`
2. Once merged upstream, update `bub-reqs.txt` to point back to upstream commit

## Available Hook Points

Plugins implement hooks from `bub/hookspecs.py`:

| Hook | Type | Purpose |
|------|------|---------|
| `resolve_session` | firstresult | Map message to session ID |
| `build_prompt` | firstresult | Construct LLM prompt |
| `run_model` | firstresult | Execute LLM call |
| `run_model_stream` | firstresult | Execute LLM call (streaming) |
| `load_state` | collect | Load state for session |
| `save_state` | collect | Persist state after turn |
| `system_prompt` | collect | Provide system prompt fragment |
| `render_outbound` | collect | Render output messages |
| `dispatch_outbound` | collect | Send messages to channels |
| `provide_channels` | collect | Register input channels |
| `provide_tape_store` | firstresult | Provide tape storage backend |
| `build_tape_context` | firstresult | Configure tape context rules |
| `on_error` | collect | Handle errors |

`firstresult`: first non-None return wins (later-registered plugin has higher priority).
`collect`: all implementations run, results collected.

## Conventions

- Commit messages: `fix(scope):` or `feat(scope):`
- Always pin to commit hash in production, never to branch
- PR titles under 70 chars
- Use `gh auth token` for HTTPS auth in container environments
- Test changes locally before pushing when possible
