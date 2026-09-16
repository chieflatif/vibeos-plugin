import json
import copy
import fcntl
import os
import shutil
import signal
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VIBEOS = REPO_ROOT / "vibeos"


class ProfileInstallReleaseTests(unittest.TestCase):
    def make_target(self, root: Path, name: str = "Release Fixture") -> None:
        (root / "README.md").write_text(f"# {name}\n", encoding="utf-8")
        (root / "tools").mkdir()
        (root / "tools/validate_all.py").write_text("print('ok')\n", encoding="utf-8")

    def run_cli(self, *args: str, check: bool = True, env: dict | None = None):
        result = subprocess.run(
            [str(VIBEOS), *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        if check and result.returncode:
            self.fail(result.stdout + result.stderr)
        return result

    def analyze(self, target: Path, profile: Path | None = None) -> Path:
        args = [
            "analyze",
            "--target",
            str(target),
            "--source",
            str(REPO_ROOT),
            "--mode",
            "product-engineering",
        ]
        if profile:
            args.extend(["--profile", str(profile)])
        self.run_cli(*args)
        return target / ".vibeos/install-plan.json"

    @staticmethod
    def tree_snapshot(root: Path) -> dict[str, tuple]:
        snapshot: dict[str, tuple] = {}
        for path in sorted(root.rglob("*")):
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                snapshot[rel] = ("symlink", os.readlink(path))
            elif path.is_dir():
                snapshot[rel] = ("directory",)
            elif path.is_file():
                snapshot[rel] = ("file", path.read_bytes(), path.stat().st_mode & 0o777)
            else:
                snapshot[rel] = ("other",)
        return snapshot

    def test_install_carries_controlled_evaluation_without_running_it(self):
        entrypoint = REPO_ROOT / "plugins/vibeos/scripts/controlled-evaluation.py"
        package = REPO_ROOT / "plugins/vibeos/scripts/controlled_evaluation"
        guide = REPO_ROOT / "docs/CONTROLLED-EVALUATION.md"
        self.assertTrue(
            entrypoint.is_file(),
            "controlled evaluation owner has not landed entrypoint",
        )
        self.assertTrue(
            package.is_dir(), "controlled evaluation owner has not landed package"
        )

        with tempfile.TemporaryDirectory(
            prefix="vibeos release path with spaces "
        ) as tmp:
            target = Path(tmp)
            self.make_target(target)
            plan_path = self.analyze(target)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))

            self.assertEqual(
                plan["source_binding"]["commit"],
                subprocess.run(
                    ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip(),
            )
            self.assertIn("plan_payload_hash", plan)
            self.run_cli("verify", "--plan", str(plan_path))
            applied = self.run_cli("apply", "--plan", str(plan_path))
            self.assertNotIn("controlled-evaluation.py prepare", applied.stdout)

            installed_entrypoint = target / ".vibeos/scripts/controlled-evaluation.py"
            self.assertEqual(installed_entrypoint.read_bytes(), entrypoint.read_bytes())
            help_result = subprocess.run(
                ["python3", str(installed_entrypoint), "--help"],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                help_result.returncode, 0, help_result.stdout + help_result.stderr
            )
            self.assertIn("prepare", help_result.stdout)
            installed_files = sorted(
                path.relative_to(
                    target / ".vibeos/scripts/controlled_evaluation"
                ).as_posix()
                for path in (target / ".vibeos/scripts/controlled_evaluation").rglob(
                    "*"
                )
                if path.is_file() and "__pycache__" not in path.parts
            )
            source_files = sorted(
                path.relative_to(package).as_posix()
                for path in package.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts
            )
            self.assertEqual(installed_files, source_files)
            if guide.is_file():
                self.assertEqual(
                    (target / ".vibeos/controlled-evaluation-guide.md").read_bytes(),
                    guide.read_bytes(),
                )
            agents = (target / "AGENTS.md").read_text(encoding="utf-8")
            skill = (target / ".agents/skills/vibeos-build/SKILL.md").read_text(
                encoding="utf-8"
            )
            for text in (agents, skill):
                self.assertIn(".vibeos/scripts/controlled-evaluation.py --help", text)
                self.assertIn("PRE_REVIEW", text)

            lock = json.loads(
                (target / ".vibeos/install-lock.json").read_text(encoding="utf-8")
            )
            self.assertEqual(lock["transaction_status"], "complete")
            self.assertEqual(
                lock["source_binding"]["commit"], plan["source_binding"]["commit"]
            )
            self.run_cli("verify", "--plan", str(plan_path))

    def test_plan_profile_source_output_and_target_drift_are_rejected(self):
        scenarios = ["plan", "profile", "source", "target"]
        for scenario in scenarios:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp)
                self.make_target(target, f"Drift {scenario}")
                profile = target / "profile.json"
                profile.write_text(
                    json.dumps(
                        {
                            "project_name": f"Drift {scenario}",
                            "mode": "product-engineering",
                        }
                    ),
                    encoding="utf-8",
                )
                plan_path = self.analyze(target, profile)
                plan = json.loads(plan_path.read_text(encoding="utf-8"))

                if scenario == "plan":
                    plan["mode"] = "minimal"
                    plan_path.write_text(json.dumps(plan), encoding="utf-8")
                elif scenario == "profile":
                    profile.write_text(
                        '{"project_name":"changed","mode":"minimal"}', encoding="utf-8"
                    )
                elif scenario == "source":
                    plan["source_binding"]["files"]["scripts/profile_install.py"] = (
                        "0" * 64
                    )
                    payload = {
                        key: value
                        for key, value in plan.items()
                        if key != "plan_payload_hash"
                    }
                    plan["plan_payload_hash"] = self.compact_hash(payload)
                    plan_path.write_text(json.dumps(plan), encoding="utf-8")
                else:
                    readme = target / "README.md"
                    readme.write_text(
                        readme.read_text(encoding="utf-8") + "target changed\n",
                        encoding="utf-8",
                    )

                result = self.run_cli("verify", "--plan", str(plan_path), check=False)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertRegex(result.stderr, "drift|hash mismatch|baseline")

    def test_actual_source_bytes_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            shutil.copytree(REPO_ROOT / "plugins/vibeos", source)
            target.mkdir()
            self.make_target(target)
            subprocess.run(["git", "init", "-q", str(source)], check=True)
            subprocess.run(["git", "-C", str(source), "add", "."], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(source),
                    "-c",
                    "user.name=VibeOS Test",
                    "-c",
                    "user.email=vibeos@example.invalid",
                    "commit",
                    "-qm",
                    "fixture",
                ],
                check=True,
            )
            plan_path = target / ".vibeos/install-plan.json"
            self.run_cli(
                "analyze",
                "--target",
                str(target),
                "--source",
                str(source),
                "--mode",
                "product-engineering",
            )
            clean_plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertFalse(clean_plan["source_binding"]["source_worktree_dirty"])
            self.assertEqual(
                clean_plan["source_binding"]["relevant_files_sha256"],
                self.compact_hash(clean_plan["source_binding"]["files"]),
            )
            installer = source / "scripts/profile_install.py"
            installer.write_text(
                installer.read_text(encoding="utf-8") + "\n", encoding="utf-8"
            )
            dirty_target = root / "dirty-target"
            dirty_target.mkdir()
            self.make_target(dirty_target, "Dirty Source")
            self.run_cli(
                "analyze",
                "--target",
                str(dirty_target),
                "--source",
                str(source),
                "--mode",
                "product-engineering",
            )
            dirty_plan_path = dirty_target / ".vibeos/install-plan.json"
            dirty_plan = json.loads(dirty_plan_path.read_text(encoding="utf-8"))
            self.assertTrue(dirty_plan["source_binding"]["source_worktree_dirty"])
            self.run_cli("verify", "--plan", str(dirty_plan_path))
            installer.write_text(
                installer.read_text(encoding="utf-8") + "# second drift\n",
                encoding="utf-8",
            )
            result = self.run_cli("verify", "--plan", str(dirty_plan_path), check=False)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("source drift", result.stderr)

    @staticmethod
    def compact_hash(payload: dict) -> str:
        import hashlib

        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def test_symlink_and_traversal_outputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            outside = Path(tmp) / "outside"
            target.mkdir()
            outside.mkdir()
            self.make_target(target)
            (target / ".codex").symlink_to(outside, target_is_directory=True)
            result = self.run_cli(
                "analyze",
                "--target",
                str(target),
                "--source",
                str(REPO_ROOT),
                check=False,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("symlink", result.stderr)

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            plan_path = self.analyze(target)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["analyzed_outputs"][0]["path"] = "../escape"
            plan["analyzed_outputs_hash"] = self.compact_hash(plan["analyzed_outputs"])
            payload = {
                key: value for key, value in plan.items() if key != "plan_payload_hash"
            }
            plan["plan_payload_hash"] = self.compact_hash(payload)
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            result = self.run_cli("verify", "--plan", str(plan_path), check=False)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("traversal", result.stderr)

    def test_customization_upgrade_preserves_original_and_separate_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            first_plan = self.analyze(target)
            self.run_cli("apply", "--plan", str(first_plan))
            customized = target / ".codex/agents/backend.toml"
            customized.write_text(
                customized.read_text(encoding="utf-8") + "\n# customer-owned setting\n",
                encoding="utf-8",
            )
            customized_bytes = customized.read_bytes()

            second_plan = self.analyze(target)
            self.run_cli("apply", "--plan", str(second_plan))
            self.assertEqual(customized.read_bytes(), customized_bytes)
            candidate = (
                target
                / ".vibeos/merge-conflicts/.codex__agents__backend.toml.generated"
            )
            self.assertTrue(candidate.is_file())
            lock = json.loads(
                (target / ".vibeos/install-lock.json").read_text(encoding="utf-8")
            )
            row = next(
                row
                for row in lock["installed_state"]
                if row["path"] == ".codex/agents/backend.toml"
            )
            self.assertEqual(row["action"], "preserved-local-customization")

    def test_upgrade_never_clobbers_an_existing_merge_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            first = self.analyze(target)
            self.run_cli("apply", "--plan", str(first))
            customized = target / ".codex/agents/backend.toml"
            customized.write_text(
                customized.read_text(encoding="utf-8") + "\n# local\n", encoding="utf-8"
            )
            occupied = (
                target
                / ".vibeos/merge-conflicts/.codex__agents__backend.toml.generated"
            )
            occupied.parent.mkdir(parents=True, exist_ok=True)
            occupied.write_text("prior candidate\n", encoding="utf-8")
            second = self.analyze(target)
            plan = json.loads(second.read_text(encoding="utf-8"))
            row = next(
                row
                for row in plan["overwrite_plan"]
                if row["path"] == ".codex/agents/backend.toml"
            )
            self.assertNotEqual(
                row["candidate"], occupied.relative_to(target).as_posix()
            )
            self.run_cli("apply", "--plan", str(second))
            self.assertEqual(occupied.read_text(encoding="utf-8"), "prior candidate\n")

    def test_actual_sigterm_requires_recovery_and_restores_exact_preapply_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target, "Interrupted Fixture")
            plan_path = self.analyze(target)
            readme_before = (target / "README.md").read_bytes()
            tree_before = self.tree_snapshot(target)
            env = os.environ.copy()
            env["VIBEOS_INSTALL_TEST_INTERRUPT_AFTER"] = "3"
            interrupted = self.run_cli(
                "apply", "--plan", str(plan_path), check=False, env=env
            )
            self.assertEqual(
                interrupted.returncode,
                -signal.SIGTERM,
                interrupted.stdout + interrupted.stderr,
            )
            self.assertTrue((target / ".vibeos/install-recovery.json").is_file())
            self.assertFalse((target / ".vibeos/install-lock.json").exists())

            retry = self.run_cli("apply", "--plan", str(plan_path), check=False)
            self.assertEqual(retry.returncode, 2, retry.stdout + retry.stderr)
            self.assertIn("recover", retry.stderr)

            recovered = self.run_cli("recover", "--plan", str(plan_path))
            self.assertIn("rollback verified", recovered.stdout)
            self.assertEqual((target / "README.md").read_bytes(), readme_before)
            self.assertFalse((target / "AGENTS.md").exists())
            self.assertFalse((target / ".vibeos/install-recovery.json").exists())
            self.assertEqual(self.tree_snapshot(target), tree_before)
            self.run_cli("verify", "--plan", str(plan_path))
            self.run_cli("apply", "--plan", str(plan_path))

    def test_sigterm_between_final_lock_binding_and_write_recovers_verifying_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target, "Lock Transition")
            plan_path = self.analyze(target)
            tree_before = self.tree_snapshot(target)
            env = os.environ.copy()
            env["VIBEOS_INSTALL_TEST_INTERRUPT_BEFORE_COMPLETE_LOCK"] = "1"
            interrupted = self.run_cli(
                "apply", "--plan", str(plan_path), check=False, env=env
            )
            self.assertEqual(
                interrupted.returncode,
                -signal.SIGTERM,
                interrupted.stdout + interrupted.stderr,
            )
            lock = json.loads(
                (target / ".vibeos/install-lock.json").read_text(encoding="utf-8")
            )
            self.assertEqual(lock["transaction_status"], "verifying")
            journal = json.loads(
                (target / ".vibeos/install-recovery.json").read_text(encoding="utf-8")
            )
            lock_entry = next(
                row
                for row in journal["entries"]
                if row["path"] == ".vibeos/install-lock.json"
            )
            self.assertIsInstance(lock_entry["after"], list)
            self.assertEqual(len(lock_entry["after"]), 2)
            self.run_cli("recover", "--plan", str(plan_path))
            self.assertEqual(self.tree_snapshot(target), tree_before)

    def test_installed_verify_detects_post_install_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            plan_path = self.analyze(target)
            self.run_cli("apply", "--plan", str(plan_path))
            (target / "AGENTS.md").write_text("tampered\n", encoding="utf-8")
            result = self.run_cli("verify", "--plan", str(plan_path), check=False)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("installed target drift", result.stderr)

    def test_forged_complete_lock_cannot_verify_an_unapplied_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            plan_path = self.analyze(target)
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            (target / ".vibeos/install-lock.json").write_text(
                json.dumps(
                    {
                        "transaction_status": "complete",
                        "plan_payload_hash": plan["plan_payload_hash"],
                        "installed_state": [],
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_cli("verify", "--plan", str(plan_path), check=False)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("install lock", result.stderr)

    def test_installed_lock_rejects_missing_empty_duplicate_extra_and_fabricated_rows(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            plan_path = self.analyze(target)
            self.run_cli("apply", "--plan", str(plan_path))
            lock_path = target / ".vibeos/install-lock.json"
            original = json.loads(lock_path.read_text(encoding="utf-8"))

            variants: dict[str, dict] = {}
            missing = copy.deepcopy(original)
            missing.pop("installed_state")
            variants["missing"] = missing
            empty = copy.deepcopy(original)
            empty["installed_state"] = []
            variants["empty"] = empty
            duplicate = copy.deepcopy(original)
            duplicate["installed_state"].append(
                copy.deepcopy(duplicate["installed_state"][0])
            )
            variants["duplicate"] = duplicate
            extra = copy.deepcopy(original)
            extra["installed_state"].append(
                {
                    "path": "fabricated.txt",
                    "kind": "file",
                    "sha256": "0" * 64,
                    "mode": 0o644,
                    "action": "created",
                }
            )
            variants["extra"] = extra
            fabricated = copy.deepcopy(original)
            fabricated["installed_state"][0]["sha256"] = "0" * 64
            variants["fabricated"] = fabricated

            for name, lock in variants.items():
                with self.subTest(name=name):
                    lock_path.write_text(json.dumps(lock), encoding="utf-8")
                    result = self.run_cli(
                        "verify", "--plan", str(plan_path), check=False
                    )
                    self.assertEqual(
                        result.returncode, 2, result.stdout + result.stderr
                    )
                    self.assertIn("install lock", result.stderr)

    def test_fresh_install_audits_exact_pending_instruction_inventory_before_completion(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target, "Audit Ordering")
            profile = target / "profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "project_name": "Audit Ordering",
                        "mode": "product-engineering",
                        "primary_gates": [
                            "autonomous, self-governing development engine"
                        ],
                    }
                ),
                encoding="utf-8",
            )
            plan_path = self.analyze(target, profile)
            tree_before = self.tree_snapshot(target)
            result = self.run_cli("apply", "--plan", str(plan_path), check=False)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("generic active-instruction phrase", result.stderr)
            lock = json.loads(
                (target / ".vibeos/install-lock.json").read_text(encoding="utf-8")
            )
            self.assertEqual(lock["transaction_status"], "verifying")
            self.assertEqual(
                lock["generated_files"],
                json.loads(plan_path.read_text(encoding="utf-8"))["analyzed_outputs"],
            )
            self.assertTrue((target / ".vibeos/install-recovery.json").is_file())
            self.run_cli("recover", "--plan", str(plan_path))
            self.assertEqual(self.tree_snapshot(target), tree_before)

    def test_recovery_refuses_concurrent_edit_without_mutating_other_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            plan_path = self.analyze(target)
            env = os.environ.copy()
            env["VIBEOS_INSTALL_TEST_INTERRUPT_AFTER"] = "3"
            interrupted = self.run_cli(
                "apply", "--plan", str(plan_path), check=False, env=env
            )
            self.assertEqual(interrupted.returncode, -signal.SIGTERM)
            journal = json.loads(
                (target / ".vibeos/install-recovery.json").read_text(encoding="utf-8")
            )
            written = [
                row
                for row in journal["entries"]
                if row.get("after") and (target / row["path"]).is_file()
            ]
            self.assertGreaterEqual(len(written), 2)
            edited = target / written[0]["path"]
            untouched = target / written[1]["path"]
            untouched_bytes = untouched.read_bytes()
            edited.write_text("user edit after interruption\n", encoding="utf-8")

            result = self.run_cli("recover", "--plan", str(plan_path), check=False)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("unexpected current bytes", result.stderr)
            self.assertEqual(
                edited.read_text(encoding="utf-8"), "user edit after interruption\n"
            )
            self.assertEqual(untouched.read_bytes(), untouched_bytes)

    def test_recovery_preflights_corrupt_backup_before_any_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target, "Before")
            first = self.analyze(target)
            self.run_cli("apply", "--plan", str(first))
            profile = target / "upgrade-profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "project_name": "After",
                        "mode": "product-engineering",
                    }
                ),
                encoding="utf-8",
            )
            second = self.analyze(target, profile)
            env = os.environ.copy()
            env["VIBEOS_INSTALL_TEST_INTERRUPT_AFTER"] = "2"
            interrupted = self.run_cli(
                "apply", "--plan", str(second), check=False, env=env
            )
            self.assertEqual(interrupted.returncode, -signal.SIGTERM)
            journal_path = target / ".vibeos/install-recovery.json"
            journal = json.loads(journal_path.read_text(encoding="utf-8"))
            backed = next(row for row in journal["entries"] if row.get("backup"))
            backup = target / journal["backup_root"] / backed["backup"]
            backup.write_bytes(b"corrupt")
            changed = [
                target / row["path"]
                for row in journal["entries"]
                if row.get("after") and (target / row["path"]).is_file()
            ]
            snapshots = {path: path.read_bytes() for path in changed}

            result = self.run_cli("recover", "--plan", str(second), check=False)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("backup hash mismatch", result.stderr)
            self.assertEqual({path: path.read_bytes() for path in changed}, snapshots)

    def test_apply_refuses_concurrent_writer_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            plan_path = self.analyze(target)
            lock_path = target / ".vibeos/install-transaction.lock"
            lock_path.touch()
            with lock_path.open("a+b") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                result = self.run_cli("apply", "--plan", str(plan_path), check=False)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("another install transaction", result.stderr)
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


if __name__ == "__main__":
    unittest.main()
