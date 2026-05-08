import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "agent_runtime.py"


def load_agent_runtime(root: Path):
    module_name = f"agent_runtime_test_{next(tempfile._get_candidate_names())}"
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    original_env = os.environ.copy()
    os.environ.update(
        {
            "SELFOPS_AGENT_RUNTIME_ROOT": str(root),
            "SELFOPS_AGENT_RUNTIME_REGISTRY": str(root / "registry"),
            "SELFOPS_AGENT_RUNTIME_STATE": str(root / ".state"),
            "SELFOPS_AGENT_RUNTIME_CACHE": str(root / ".agents"),
        }
    )
    try:
        spec.loader.exec_module(module)
    finally:
        os.environ.clear()
        os.environ.update(original_env)
    return module


class AgentRuntimeProjectsPathTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        (self.root / "registry").mkdir(parents=True)
        (self.root / "materialized" / "skills" / "contrib-workflow").mkdir(parents=True)
        (self.root / "materialized" / "skills" / "contrib-workflow" / "SKILL.md").write_text(
            "# test skill\n",
            encoding="utf-8",
        )
        (self.root / "registry" / "skills.toml").write_text(
            '[skills.contrib-workflow]\nsource = { type = "owned" }\n',
            encoding="utf-8",
        )

        self.project_root = self.root / "workspace" / "SelfOps"
        self.project_root.mkdir(parents=True)
        self.projects_path = self.root / "projects.toml"
        self.projects_path.write_text(
            f'''[projects."{self.project_root}"]\nagents = ["agents"]\nbundles = []\ninclude = ["contrib-workflow"]\nexclude = []\n''',
            encoding="utf-8",
        )

        self.agent_runtime = load_agent_runtime(self.root)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_plan_uses_custom_projects_file(self):
        result = self.agent_runtime.plan(projects_path=self.projects_path)

        self.assertEqual(list(result["desired"].keys()), [str(self.project_root)])
        action = next(
            action for action in result["actions"] if action["type"] == "create_link"
        )
        self.assertEqual(
            action["path"],
            str(self.project_root / ".agents" / "skills" / "contrib-workflow"),
        )

    def test_apply_creates_agents_skill_symlink(self):
        self.agent_runtime.apply_plan(force=True, projects_path=self.projects_path)

        link_path = self.project_root / ".agents" / "skills" / "contrib-workflow"
        self.assertTrue(link_path.is_symlink())
        self.assertEqual(
            link_path.resolve(),
            self.root / "materialized" / "skills" / "contrib-workflow",
        )
