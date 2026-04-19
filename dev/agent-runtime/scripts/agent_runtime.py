#!/usr/bin/env python3
"""SelfOps agent runtime reconciler.

The registry is intentionally small:
- skills.toml defines skills and bundles
- projects.toml defines project -> agents -> desired skills
- mise.toml owns tool installation and task entrypoints

scan observes concrete project-target-skill facts.
plan expands bundles and computes skill-level actions.
apply syncs sources and reconciles target directories.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── ANSI colors ──

def _supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

_COLOR = _supports_color()

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _COLOR else text

def dim(t: str) -> str: return _c("2", t)
def bold(t: str) -> str: return _c("1", t)
def green(t: str) -> str: return _c("32", t)
def red(t: str) -> str: return _c("31", t)
def yellow(t: str) -> str: return _c("33", t)
def cyan(t: str) -> str: return _c("36", t)
def magenta(t: str) -> str: return _c("35", t)
def blue(t: str) -> str: return _c("34", t)

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        print("Python 3.11+ or tomli is required", file=sys.stderr)
        sys.exit(2)


ROOT = Path(os.environ.get("SELFOPS_AGENT_RUNTIME_ROOT", Path(__file__).resolve().parents[1])).resolve()
REGISTRY_DIR = Path(os.environ.get("SELFOPS_AGENT_RUNTIME_REGISTRY", ROOT / "registry")).resolve()
STATE_DIR = Path(os.environ.get("SELFOPS_AGENT_RUNTIME_STATE", ROOT / ".state")).resolve()
CACHE_DIR = Path(os.environ.get("SELFOPS_AGENT_RUNTIME_CACHE", ROOT / ".cache" / "skills")).resolve()
SKILLS_PATH = REGISTRY_DIR / "skills.toml"
PROJECTS_PATH = REGISTRY_DIR / "projects.toml"
SCAN_PATH = STATE_DIR / "scan.json"
PLAN_PATH = STATE_DIR / "plan.json"
APPLY_LOG_PATH = STATE_DIR / "apply-log.jsonl"


@dataclass(frozen=True)
class Action:
    type: str
    skill: str | None = None
    project: str | None = None
    agent: str | None = None
    path: str | None = None
    points_to: str | None = None
    source: dict[str, Any] | None = None
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"type": self.type}
        for key in ("skill", "project", "agent", "path", "points_to", "source", "reason"):
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        return data


def fail(message: str, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def read_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        fail(f"missing config: {path}")
    with path.open("rb") as fh:
        return tomllib.load(fh)


def load_registry() -> tuple[dict[str, Any], dict[str, Any]]:
    return read_toml(SKILLS_PATH), read_toml(PROJECTS_PATH)


def resolve_repo_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def target_path(project: str, agent: str) -> Path:
    if project == "@global":
        return Path.home() / f".{agent}" / "skills"
    return Path(project).expanduser().resolve() / f".{agent}" / "skills"


def is_skill_entry(path: Path) -> bool:
    if path.is_symlink():
        return True  # include broken symlinks so plan can remove them
    return path.is_dir() and (path / "SKILL.md").exists()


AGENTS = ("kiro", "claude", "codex")


def scan_project(project_name: str, agents: list[str]) -> dict[str, Any]:
    """Scan a single project's agent skill directories."""
    project_state: dict[str, Any] = {"agents": {}}
    for agent in agents:
        root = target_path(project_name, agent)
        skills: dict[str, Any] = {}
        if root.is_dir():
            for child in sorted(root.iterdir()):
                if not is_skill_entry(child):
                    continue
                kind = "symlink" if child.is_symlink() else "directory"
                skills[child.name] = {
                    "path": str(child),
                    "kind": kind,
                    "points_to": str(child.resolve()) if child.is_symlink() else None,
                }
        project_state["agents"][agent] = {
            "target": str(root),
            "skills": skills,
        }
    return project_state


def discover_projects(scan_dirs: list[str]) -> dict[str, list[str]]:
    """Discover projects with agent skill directories under given paths."""
    found: dict[str, list[str]] = {}
    for scan_dir in scan_dirs:
        base = Path(scan_dir).expanduser().resolve()
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            agents = [a for a in AGENTS if (child / f".{a}" / "skills").is_dir()]
            if agents:
                found[str(child)] = agents
    # Also check @global
    global_agents = [a for a in AGENTS if (Path.home() / f".{a}" / "skills").is_dir()]
    if global_agents:
        found["@global"] = global_agents
    return found


def scan(discover: list[str] | None = None) -> dict[str, Any]:
    _, projects_cfg = load_registry()
    projects: dict[str, Any] = {}

    # Registered projects
    for project_name, project in projects_cfg.get("projects", {}).items():
        agents = project.get("agents", [])
        projects[project_name] = scan_project(project_name, agents)
        projects[project_name]["managed"] = True

    # Discover unregistered projects
    if discover:
        discovered = discover_projects(discover)
        for project_path, agents in discovered.items():
            if project_path not in projects:
                projects[project_path] = scan_project(project_path, agents)
                projects[project_path]["managed"] = False

    result = {
        "scanned_at": now_iso(),
        "root": str(ROOT),
        "projects": projects,
    }
    ensure_state_dir()
    SCAN_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


def print_scan(result: dict[str, Any]) -> None:
    home = str(Path.home())
    skills_cfg, _ = load_registry()

    source_types: dict[str, str] = {}
    for name, s in skills_cfg.get("skills", {}).items():
        source_types[name] = s.get("source", {}).get("type", "owned")

    def skill_tag(name: str, info: dict[str, Any]) -> str:
        st = source_types.get(name, "")
        broken = info["kind"] == "symlink" and not Path(info.get("points_to") or "").exists()
        if broken:
            return red(f"⚠ {name} (broken)")
        if not st:
            return yellow(f"⊘ {name} (unmanaged)")
        if st == "public":
            return cyan(f"☁ {name}")
        if st == "local_path":
            return f"📁 {name}"
        if st == "owned":
            return magenta(f"✎ {name}")
        return dim(f"? {name}")

    for project_name, project_state in sorted(result["projects"].items()):
        short = project_name.replace(home + "/Dev/", "").replace(home, "~")
        agents = project_state.get("agents", {})
        total = sum(len(a.get("skills", {})) for a in agents.values())
        managed = project_state.get("managed", True)
        label = bold(short) if managed else yellow(f"{short} (unregistered)")
        print(f"\n{label} {dim(f'({total} skills)')}")
        print(dim("─" * 50))
        for agent, agent_state in sorted(agents.items()):
            skills = agent_state.get("skills", {})
            if not skills:
                print(f"  {bold(agent)}: {dim('(empty)')}")
                continue
            names = sorted(skills.keys())
            if len(names) <= 5:
                tagged = [skill_tag(n, skills[n]) for n in names]
                print(f"  {bold(agent)}: {', '.join(tagged)}")
            else:
                print(f"  {bold(agent)} {dim(f'({len(names)})')}:")
                for name in names:
                    print(f"    {skill_tag(name, skills[name])}")
    print(f"\n{cyan('☁ public')}  📁 local  {magenta('✎ owned')}  {yellow('⊘ unmanaged')}  {red('⚠ broken')}")
    print(dim(f"Scan saved to {SCAN_PATH}"))


def unique(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def expand_bundle(skills_cfg: dict[str, Any], bundle_name: str, stack: tuple[str, ...] = ()) -> list[str]:
    if bundle_name in stack:
        fail(f"bundle cycle detected: {' -> '.join((*stack, bundle_name))}")
    bundle = skills_cfg.get("bundles", {}).get(bundle_name)
    if bundle is None:
        fail(f"unknown bundle: {bundle_name}")
    expanded: list[str] = []
    for parent in bundle.get("extends", []):
        expanded.extend(expand_bundle(skills_cfg, parent, (*stack, bundle_name)))
    expanded.extend(bundle.get("skills", []))
    return unique(expanded)


def desired_skills_for_config(skills_cfg: dict[str, Any], cfg: dict[str, Any]) -> list[str]:
    desired: list[str] = []
    for bundle in cfg.get("bundles", []):
        desired.extend(expand_bundle(skills_cfg, bundle))
    desired.extend(cfg.get("include", []))
    excluded = set(cfg.get("exclude", []))
    return unique([skill for skill in desired if skill not in excluded])


def desired_skills_for_agent(skills_cfg: dict[str, Any], project: dict[str, Any], agent: str) -> list[str]:
    override = project.get("agent_overrides", {}).get(agent)
    if override is not None:
        return desired_skills_for_config(skills_cfg, override)
    return desired_skills_for_config(skills_cfg, project)


def skill_dest(skill_name: str, skill: dict[str, Any]) -> Path:
    """Return the local path a skill should be linked from.

    - owned / local_path: materialized_path (under materialized/)
    - public: .cache/skills/<name> (git-ignored, managed by npx)
    """
    source_type = skill.get("source", {}).get("type", "owned")
    if source_type == "public":
        return CACHE_DIR / skill_name
    raw = skill.get("materialized_path")
    if not raw:
        raw = f"materialized/skills/{skill_name}"
    return resolve_repo_path(raw)


def source_sync_action(skill_name: str, skill: dict[str, Any]) -> Action | None:
    source = skill.get("source", {})
    source_type = source.get("type", "owned")
    dest = skill_dest(skill_name, skill)

    if source_type == "owned":
        if not dest.exists():
            return Action("missing_source", skill=skill_name, path=str(dest), source=source, reason="owned path is missing")
        return None

    if source_type == "local_path":
        src = Path(source.get("path", "")).expanduser()
        if not src.exists():
            return Action("missing_source", skill=skill_name, path=str(src), source=source, reason="local source path is missing")
        return Action("sync_source", skill=skill_name, path=str(dest), points_to=str(src.resolve()), source=source)

    if source_type == "public":
        spec = source.get("spec") or source.get("repo")
        if not spec:
            return Action("config_error", skill=skill_name, source=source, reason="public source requires spec or repo")
        if dest.exists() and (dest / "SKILL.md").exists():
            return None  # already cached
        return Action("sync_source", skill=skill_name, path=str(dest), points_to=str(spec), source=source)

    return Action("config_error", skill=skill_name, source=source, reason=f"unsupported source type: {source_type}")


def plan() -> dict[str, Any]:
    skills_cfg, projects_cfg = load_registry()
    actual = scan()
    actions: list[Action] = []
    desired_tree: dict[str, Any] = {}
    all_desired_skills: set[str] = set()

    for project_name, project in projects_cfg.get("projects", {}).items():
        agents = project.get("agents", [])
        per_agent: dict[str, list[str]] = {}
        for agent in agents:
            skills = desired_skills_for_agent(skills_cfg, project, agent)
            per_agent[agent] = skills
            for skill_name in skills:
                if skill_name not in skills_cfg.get("skills", {}):
                    actions.append(Action("config_error", skill=skill_name, project=project_name, reason="skill is referenced but not declared"))
                    continue
                all_desired_skills.add(skill_name)
        desired_tree[project_name] = {
            "agents": agents,
            "per_agent": per_agent,
        }

    for skill_name in sorted(all_desired_skills):
        action = source_sync_action(skill_name, skills_cfg["skills"][skill_name])
        if action is not None:
            actions.append(action)

    for project_name, project in projects_cfg.get("projects", {}).items():
        for agent in project.get("agents", []):
            desired_skills = set(desired_tree[project_name]["per_agent"].get(agent, []))
            target = target_path(project_name, agent)
            actual_skills = actual["projects"].get(project_name, {}).get("agents", {}).get(agent, {}).get("skills", {})

            for skill_name in sorted(desired_skills):
                skill = skills_cfg.get("skills", {}).get(skill_name)
                if skill is None:
                    continue
                link = target / skill_name
                dest = skill_dest(skill_name, skill)
                observed = actual_skills.get(skill_name)
                if observed is None:
                    actions.append(Action("create_link", skill=skill_name, project=project_name, agent=agent, path=str(link), points_to=str(dest)))
                elif observed.get("kind") == "symlink" and observed.get("points_to") != str(dest):
                    actions.append(Action("update_link", skill=skill_name, project=project_name, agent=agent, path=str(link), points_to=str(dest), reason=f"currently points to {observed.get('points_to')}"))
                elif observed.get("kind") != "symlink":
                    actions.append(Action("replace_path", skill=skill_name, project=project_name, agent=agent, path=str(link), points_to=str(dest), reason="target path is not a symlink"))

            for skill_name in sorted(set(actual_skills) - desired_skills):
                observed = actual_skills[skill_name]
                actions.append(Action("remove_path", skill=skill_name, project=project_name, agent=agent, path=observed["path"], reason="not in desired skills"))

    result = {
        "planned_at": now_iso(),
        "root": str(ROOT),
        "desired": desired_tree,
        "summary": summarize(actions),
        "actions": [action.as_dict() for action in actions],
    }
    ensure_state_dir()
    PLAN_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


def summarize(actions: list[Action]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for action in actions:
        summary[action.type] = summary.get(action.type, 0) + 1
    return summary


def copy_tree(src: Path, dest: Path) -> None:
    if src.resolve() == dest.resolve():
        return  # same path, nothing to do
    if dest.exists() or dest.is_symlink():
        remove_path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, symlinks=True)


def sync_public(spec: str, skill_name: str) -> None:
    """Download a public skill repo into .cache/skills/ via npx skills add."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    command = ["npx", "skills", "add", spec, "--skill", skill_name, "--copy", "--all", "-y"]
    subprocess.run(command, cwd=CACHE_DIR, check=True)
    dest = CACHE_DIR / skill_name
    if not (dest / "SKILL.md").exists():
        # npx may place it under an agent subdir; search and relocate
        candidates = [p for p in CACHE_DIR.rglob(f"{skill_name}/SKILL.md") if p.is_file()]
        if not candidates:
            fail(f"public skill did not produce {skill_name}/SKILL.md: {spec}")
        src = candidates[0].parent
        if src != dest:
            copy_tree(src, dest)


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


DESTRUCTIVE_ACTIONS = {"remove_path", "replace_path", "update_link"}


def apply_plan(force: bool = False) -> dict[str, Any]:
    planned = plan()
    applied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    warned: list[dict[str, Any]] = []

    for action in planned["actions"]:
        action_type = action["type"]
        path = Path(action["path"]).expanduser() if action.get("path") else None

        try:
            if action_type in {"missing_source", "config_error"}:
                skipped.append(action)
                continue

            # Destructive actions require --force
            if action_type in DESTRUCTIVE_ACTIONS and not force:
                warned.append(action)
                continue

            if action_type == "sync_source":
                assert path is not None
                source = action.get("source", {})
                if source.get("type") == "local_path":
                    copy_tree(Path(action["points_to"]).expanduser().resolve(), path)
                elif source.get("type") == "public":
                    sync_public(action["points_to"], action["skill"])
                else:
                    skipped.append({**action, "reason": "unsupported sync source"})
                    continue
                applied.append(action)
                continue

            if action_type in {"create_link", "update_link", "replace_path"}:
                assert path is not None
                if path.exists() or path.is_symlink():
                    remove_path(path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(action["points_to"], target_is_directory=True)
                applied.append(action)
                continue

            if action_type == "remove_path":
                assert path is not None
                if path.exists() or path.is_symlink():
                    remove_path(path)
                    applied.append(action)
                continue

            skipped.append({**action, "reason": "unknown action"})
        except Exception as exc:  # pragma: no cover - reported to caller
            skipped.append({**action, "error": str(exc)})

    result = {
        "applied_at": now_iso(),
        "applied": applied,
        "skipped": skipped,
        "warned": warned,
    }
    ensure_state_dir()
    with APPLY_LOG_PATH.open("a") as fh:
        fh.write(json.dumps(result, ensure_ascii=False) + "\n")
    print_apply(result)
    return result


def print_apply(result: dict[str, Any]) -> None:
    applied = result["applied"]
    skipped = result["skipped"]
    warned = result.get("warned", [])
    home = str(Path.home())

    if not applied and not skipped:
        print(green("✅ Nothing to do."))
        return

    def short_project(p: str) -> str:
        return p.replace(home + "/Dev/", "").replace(home, "~")

    type_counts: dict[str, int] = {}
    for a in applied:
        type_counts[a["type"]] = type_counts.get(a["type"], 0) + 1

    action_style = {
        "create_link":  ("+", green),
        "update_link":  ("~", yellow),
        "replace_path": ("!", yellow),
        "remove_path":  ("-", red),
    }

    # Synced
    syncs = [a for a in applied if a["type"] == "sync_source"]
    if syncs:
        print(f"\n{bold('📦 Synced')} {dim(f'({len(syncs)})')}")
        print(dim("─" * 50))
        for a in syncs:
            src_type = a.get("source", {}).get("type", "")
            if src_type == "public":
                print(f"  {green('✅')} {a['skill']} {dim('←')} {cyan(a['points_to'])}")
            else:
                src = a.get("points_to", "").replace(home + "/Dev/", "~/Dev/").replace(home, "~")
                print(f"  {green('✅')} {a['skill']} {dim('←')} {src}")

    # Group by project
    proj_groups: dict[str, dict[str, dict[str, list[str]]]] = {}
    for a in applied:
        if a["type"] not in action_style:
            continue
        proj = short_project(a.get("project", "?"))
        agent = a.get("agent", "?")
        proj_groups.setdefault(proj, {}).setdefault(agent, {}).setdefault(a["type"], []).append(a["skill"])

    for proj in sorted(proj_groups.keys()):
        agents = proj_groups[proj]
        agent_sigs: dict[tuple, list[str]] = {}
        for agent, types in agents.items():
            sig = tuple(sorted((t, tuple(sorted(s))) for t, s in types.items()))
            agent_sigs.setdefault(sig, []).append(agent)

        for sig, agent_list in agent_sigs.items():
            agent_label = ", ".join(sorted(agent_list))
            types = dict(sig)
            total = sum(len(s) for s in types.values())
            print(f"\n{bold(proj)} {dim(f'[{agent_label}]')} {dim(f'({total} applied)')}")
            print(dim("─" * 50))
            for action_type in ("create_link", "update_link", "replace_path", "remove_path"):
                skills = sorted(types.get(action_type, []))
                if not skills:
                    continue
                icon, color = action_style[action_type]
                print(f"  {color(icon)} {', '.join(skills)}")

    # Skipped
    if skipped:
        print(f"\n{yellow(f'⚠️  Skipped ({len(skipped)})')}")
        print(dim("─" * 50))
        for s in skipped:
            reason = s.get("reason", "") or s.get("error", "")
            print(f"  {yellow(s.get('skill','?'))}: {reason}")

    # Warned (destructive actions held back)
    if warned:
        warn_types: dict[str, list[str]] = {}
        for w in warned:
            key = w.get("type", "?")
            proj = w.get("project", "?").replace(home + "/Dev/", "").replace(home, "~")
            warn_types.setdefault(key, []).append(f"{w.get('skill','?')} ({proj}/{w.get('agent','?')})")
        print(f"\n{yellow(bold(f'⚠️  {len(warned)} destructive actions held back (use --force to execute):'))}")
        print(dim("─" * 50))
        for wtype, items in warn_types.items():
            print(f"  {yellow(wtype)}: {', '.join(items)}")

    # Summary
    parts = [f"{v} {k}" for k, v in sorted(type_counts.items())]
    summary_detail = ", ".join(parts)
    print(f"\n{bold(f'Applied: {len(applied)}')} {dim(f'({summary_detail})')}")
    if skipped:
        print(yellow(f"Skipped: {len(skipped)}"))
    if warned:
        print(yellow(f"Held back: {len(warned)} (--force to apply)"))


def print_plan(result: dict[str, Any]) -> None:
    actions = result["actions"]
    summary = result["summary"]
    if not actions:
        print(green("✅ No changes needed — everything is up to date."))
        return

    home = str(Path.home())
    skills_cfg, _ = load_registry()

    bundle_skills: dict[str, set[str]] = {}
    for bname, b in skills_cfg.get("bundles", {}).items():
        bundle_skills[bname] = set(expand_bundle(skills_cfg, bname))

    def short_project(p: str) -> str:
        return p.replace(home + "/Dev/", "").replace(home, "~")

    def group_by_bundle(skill_list: list[str]) -> str:
        remaining = set(skill_list)
        parts: list[str] = []
        for bname, bskills in sorted(bundle_skills.items(), key=lambda x: -len(x[1])):
            if bskills and bskills <= remaining:
                parts.append(blue(f"[{bname}]({len(bskills)})"))
                remaining -= bskills
        for sk in sorted(remaining):
            parts.append(sk)
        return ", ".join(parts)

    # Sync source
    syncs = [a for a in actions if a["type"] == "sync_source"]
    if syncs:
        public = [a for a in syncs if a.get("source", {}).get("type") == "public"]
        local = [a for a in syncs if a.get("source", {}).get("type") != "public"]
        print(f"\n{bold('📦 Sync source')} {dim(f'({len(syncs)})')}")
        print(dim("─" * 60))
        if public:
            by_spec: dict[str, list[str]] = {}
            for a in public:
                by_spec.setdefault(a.get("points_to", "?"), []).append(a["skill"])
            for spec, skills in sorted(by_spec.items()):
                print(f"  {cyan(spec)}: {', '.join(skills)}")
        for a in local:
            src = a.get("points_to", "").replace(home + "/Dev/", "~/Dev/").replace(home, "~")
            print(f"  {a['skill']:40s} {dim('←')} {src}")

    # Group by project
    action_style = {
        "create_link":  ("+", "add",     green),
        "update_link":  ("~", "update",  yellow),
        "replace_path": ("!", "replace", yellow),
        "remove_path":  ("-", "remove",  red),
    }

    proj_groups: dict[str, dict[str, dict[str, list[str]]]] = {}
    for a in actions:
        if a["type"] not in action_style:
            continue
        proj = short_project(a.get("project", "?"))
        agent = a.get("agent", "?")
        proj_groups.setdefault(proj, {}).setdefault(agent, {}).setdefault(a["type"], []).append(a["skill"])

    for proj in sorted(proj_groups.keys()):
        agents = proj_groups[proj]
        agent_sigs: dict[tuple, list[str]] = {}
        for agent, types in agents.items():
            sig = tuple(sorted((t, tuple(sorted(s))) for t, s in types.items()))
            agent_sigs.setdefault(sig, []).append(agent)

        for sig, agent_list in agent_sigs.items():
            agent_label = ", ".join(sorted(agent_list))
            types = dict(sig)
            total = sum(len(s) for s in types.values())
            print(f"\n{bold(proj)} {dim(f'[{agent_label}]')} {dim(f'({total} changes)')}")
            print(dim("─" * 60))
            for action_type in ("create_link", "update_link", "replace_path", "remove_path"):
                skills = sorted(types.get(action_type, []))
                if not skills:
                    continue
                icon, label, color = action_style[action_type]
                display = group_by_bundle(skills) if action_type == "create_link" else ", ".join(skills)
                print(f"  {color(icon)} {color(label)}: {display}")

    # Errors
    errors = [a for a in actions if a["type"] in ("missing_source", "config_error")]
    if errors:
        print(f"\n{red(f'⚠️  Errors ({len(errors)})')}")
        print(dim("─" * 60))
        for a in errors:
            print(f"  {red(a.get('skill','?'))}: {a.get('reason','')}")

    total = sum(summary.values())
    parts = [f"{v} {k}" for k, v in summary.items()]
    summary_detail = ", ".join(parts)
    print(f"\n{bold(f'Total: {total} actions')} {dim(f'({summary_detail})')}")
    print(dim(f"Plan saved to {PLAN_PATH}"))


def main() -> None:
    parser = argparse.ArgumentParser(description="SelfOps agent runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    scan_cmd = sub.add_parser("scan")
    scan_cmd.add_argument("--discover", nargs="*", metavar="DIR",
                          help="Also scan directories for unregistered projects (default: ~/Dev)")
    sub.add_parser("plan")
    apply_cmd = sub.add_parser("apply")
    apply_cmd.add_argument("--force", action="store_true",
                           help="Execute destructive actions (remove, replace, update)")
    args = parser.parse_args()

    if args.command == "scan":
        discover = args.discover
        if discover is not None and len(discover) == 0:
            _, projects_cfg = load_registry()
            discover = projects_cfg.get("scan_dirs", ["~/Dev"])
        print_scan(scan(discover=discover))
    elif args.command == "plan":
        print_plan(plan())
    elif args.command == "apply":
        apply_plan(force=args.force)


if __name__ == "__main__":
    main()
