import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/vibeos/scripts/validate-canonical-closeout.py"


class CanonicalCloseoutTests(unittest.TestCase):
    def command(self, *args, cwd: Path, check: bool = True):
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=30)
        if check and result.returncode:
            self.fail(result.stdout + result.stderr)
        return result

    def commit(self, repo: Path, message: str) -> str:
        self.command("git", "add", ".", cwd=repo)
        self.command(
            "git", "-c", "user.name=Fixture", "-c",
            "user.email=fixture@example.invalid", "commit", "-qm", message, cwd=repo,
        )
        return self.command("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()

    def fixture(self, root: Path) -> tuple[Path, Path]:
        remote = root / "remote.git"
        repo = root / "repo"
        self.command("git", "init", "--bare", "-q", str(remote), cwd=root)
        self.command("git", "init", "-q", "-b", "main", str(repo), cwd=root)
        (repo / "README.md").write_text("# Fixture\n", encoding="utf-8")
        self.commit(repo, "initial")
        self.command("git", "remote", "add", "origin", str(remote), cwd=repo)
        self.command("git", "push", "-qu", "origin", "main", cwd=repo)
        return repo, remote

    def run_gate(self, repo: Path):
        return self.command(
            "python3", str(SCRIPT), "--project-dir", str(repo), check=False, cwd=repo
        )

    def write_manifest(self, repo: Path, payload: dict) -> None:
        target = repo / ".vibeos/canonical-closeout.json"
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def test_product_source_fails_until_accepted_commit_reaches_remote_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = self.fixture(Path(tmp))
            self.command("git", "switch", "-qc", "candidate", cwd=repo)
            (repo / "product.py").write_text("VALUE = 1\n", encoding="utf-8")
            accepted = self.commit(repo, "accepted product")
            tree = self.command("git", "rev-parse", "HEAD^{tree}", cwd=repo).stdout.strip()
            self.command("git", "push", "-q", "origin", "candidate", cwd=repo)
            self.command("git", "switch", "-q", "main", cwd=repo)
            self.write_manifest(repo, {
                "schema_version": 1, "classification": "product-source",
                "remote": "origin", "default_branch": "main",
                "accepted_commit": accepted, "accepted_tree": tree,
                "front_door_paths": ["README.md"],
            })
            self.commit(repo, "record acceptance")
            self.command("git", "push", "-q", "origin", "main", cwd=repo)
            blocked = self.run_gate(repo)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("accepted product commit", blocked.stdout)
            self.command(
                "git", "-c", "user.name=Fixture", "-c",
                "user.email=fixture@example.invalid", "merge", "--no-ff", "-qm",
                "promote accepted product", "candidate", cwd=repo,
            )
            self.command("git", "push", "-q", "origin", "main", cwd=repo)
            passed = self.run_gate(repo)
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)

    def test_evidence_only_requires_digest_bound_artifact_on_remote_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = self.fixture(Path(tmp))
            artifact = repo / "evidence/proof.json"
            artifact.parent.mkdir()
            artifact.write_text('{"result":"PASS"}\n', encoding="utf-8")
            self.write_manifest(repo, {
                "schema_version": 1, "classification": "evidence-only",
                "remote": "origin", "default_branch": "main",
                "accepted_identity": "proof-1", "evidence_path": "evidence/proof.json",
                "evidence_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "front_door_paths": ["README.md"],
            })
            self.commit(repo, "record evidence acceptance")
            self.command("git", "push", "-q", "origin", "main", cwd=repo)
            passed = self.run_gate(repo)
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
            manifest = json.loads((repo / ".vibeos/canonical-closeout.json").read_text())
            manifest["evidence_sha256"] = "0" * 64
            self.write_manifest(repo, manifest)
            self.commit(repo, "plant bad digest")
            self.command("git", "push", "-q", "origin", "main", cwd=repo)
            blocked = self.run_gate(repo)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("digest does not match", blocked.stdout)

    def test_unpushed_manifest_and_missing_front_door_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = self.fixture(Path(tmp))
            accepted = self.command("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
            tree = self.command("git", "rev-parse", "HEAD^{tree}", cwd=repo).stdout.strip()
            payload = {
                "schema_version": 1, "classification": "product-source",
                "remote": "origin", "default_branch": "main",
                "accepted_commit": accepted, "accepted_tree": tree,
                "front_door_paths": ["README.md"],
            }
            self.write_manifest(repo, payload)
            missing = self.run_gate(repo)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("manifest is missing", missing.stdout)
            payload["front_door_paths"] = ["CURRENT-TRUTH.md"]
            self.write_manifest(repo, payload)
            self.commit(repo, "record missing front door")
            self.command("git", "push", "-q", "origin", "main", cwd=repo)
            blocked = self.run_gate(repo)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("front-door file", blocked.stdout)

    def test_product_engineering_install_carries_closeout_validator(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            target.mkdir()
            self.command("git", "init", "-q", str(target), cwd=Path(tmp))
            (target / "README.md").write_text("# Target\n", encoding="utf-8")
            profile = target / "vibeos-profile.json"
            profile.write_text(json.dumps({
                "project_name": "Target", "mode": "product-engineering",
                "lead_runtime": "codex", "canon_paths": ["README.md"],
                "protected_files": ["README.md"],
            }), encoding="utf-8")
            plan = target / ".vibeos/install-plan.json"
            for args in [
                ["analyze", "--source", str(ROOT), "--target", str(target),
                 "--profile", str(profile)],
                ["apply", "--plan", str(plan)],
            ]:
                result = self.command(str(ROOT / "vibeos"), *args, cwd=ROOT, check=False)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(
                (target / ".vibeos/scripts/validate-canonical-closeout.py").is_file()
            )

    def test_front_door_symlink_escape_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = self.fixture(Path(tmp))
            outside = Path(tmp) / "outside"
            outside.mkdir()
            (outside / "truth.md").write_text("not repository truth\n", encoding="utf-8")
            (repo / "escape").symlink_to(outside, target_is_directory=True)
            accepted = self.command("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()
            tree = self.command("git", "rev-parse", "HEAD^{tree}", cwd=repo).stdout.strip()
            self.write_manifest(repo, {
                "schema_version": 1, "classification": "product-source",
                "remote": "origin", "default_branch": "main",
                "accepted_commit": accepted, "accepted_tree": tree,
                "front_door_paths": ["escape/truth.md"],
            })
            self.commit(repo, "plant symlink escape")
            self.command("git", "push", "-q", "origin", "main", cwd=repo)
            blocked = self.run_gate(repo)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("front-door file", blocked.stdout)


if __name__ == "__main__":
    unittest.main()
