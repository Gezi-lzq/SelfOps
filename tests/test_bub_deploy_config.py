from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BubDeployConfigTest(unittest.TestCase):
    def test_compose_uses_official_image_and_profile_scoped_runtime(self) -> None:
        compose = (ROOT / "agents/bub/docker-compose.yml").read_text(encoding="utf-8")

        self.assertIn("image: ghcr.io/bubbuild/bub:latest", compose)
        self.assertIn("container_name: bub-yuna", compose)
        self.assertIn("network_mode: host", compose)
        self.assertIn("/opt/bub/profiles/yuna/env", compose)
        self.assertIn("/opt/bub/profiles/yuna/workspace:/workspace", compose)
        self.assertIn("/opt/bub/profiles/yuna/home:/root", compose)
        self.assertIn("/opt/bub/profiles/yuna/home/.bub:/root/.bub", compose)
        self.assertIn("/opt/bub/profiles/yuna/cache/pip:/root/.cache/pip", compose)
        self.assertIn("/opt/bub/profiles/yuna/cache/uv:/root/.cache/uv", compose)

    def test_deploy_script_preserves_existing_profile_tape_and_migrates_legacy_yuna_tape(self) -> None:
        deploy = (ROOT / "agents/bub/deploy.sh").read_text(encoding="utf-8")

        self.assertIn('LEGACY_HOME="/opt/bub/home"', deploy)
        self.assertIn('PROFILE_ROOT="/opt/bub/profiles/${profile}"', deploy)
        self.assertIn('if [ -f "${new_bub_home}/tapes.sqlite3" ]; then', deploy)
        self.assertIn('docker stop bub >/dev/null 2>&1 || true', deploy)
        self.assertIn('cp -a "${legacy_bub_home}/tapes.sqlite3"', deploy)
        self.assertIn('cp -a "${legacy_bub_home}/tapes.sqlite3-wal"', deploy)
        self.assertIn('cp -a "${legacy_bub_home}/tapes.sqlite3-shm"', deploy)
        self.assertIn('docker compose -f "${COMPOSE_FILE}" up -d "${profile}"', deploy)

    def test_backup_workflow_uses_profile_scoped_tape_and_profile_release_name(self) -> None:
        workflow = (ROOT / ".github/workflows/bub-tape-backup.yml").read_text(encoding="utf-8")

        self.assertIn("/opt/bub/profiles/yuna/home/.bub/tapes.sqlite3", workflow)
        self.assertIn("tape-backup-yuna-", workflow)
        self.assertIn("runs-on: self-hosted", workflow)


if __name__ == "__main__":
    unittest.main()
