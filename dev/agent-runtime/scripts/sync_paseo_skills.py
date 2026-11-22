#!/usr/bin/env python3
"""Copy Paseo's bundled skills from the installed CLI into SelfOps."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = (
    "paseo",
    "paseo-advisor",
    "paseo-committee",
    "paseo-handoff",
    "paseo-help",
    "paseo-plugin",
)


def installed_cli_root() -> Path:
    result = subprocess.run(
        ["mise", "where", "npm:@getpaseo/cli"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(result.stdout.strip())


def main() -> None:
    cli_root = installed_cli_root()
    package_json = cli_root / "lib/node_modules/@getpaseo/cli/package.json"
    package = json.loads(package_json.read_text(encoding="utf-8"))
    version = package["version"]
    source_root = cli_root / "lib/node_modules/@getpaseo/cli/node_modules/@getpaseo/server/dist/server/skills"
    target_root = ROOT / "materialized/skills"

    for name in SKILLS:
        source = source_root / name
        target = target_root / name
        if not (source / "SKILL.md").exists():
            raise SystemExit(f"missing bundled Paseo skill: {source}")
        if target.exists() or target.is_symlink():
            shutil.rmtree(target)
        shutil.copytree(source, target)

    registry = ROOT / "registry/paseo.toml"
    registry.write_text(
        "[upstreams.paseo]\n"
        'package = "@getpaseo/cli"\n'
        f'version = "{version}"\n'
        'source = "getpaseo/paseo"\n'
        'skills_path = "@getpaseo/server/dist/server/skills"\n',
        encoding="utf-8",
    )
    print(f"Synced {len(SKILLS)} Paseo skills from @getpaseo/cli {version}")


if __name__ == "__main__":
    main()
