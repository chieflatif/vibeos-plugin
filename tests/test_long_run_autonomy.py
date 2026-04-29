import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HEARTBEAT = REPO_ROOT / "plugins/vibeos/scripts/autonomy-heartbeat.py"
LOOP = REPO_ROOT / "plugins/vibeos/scripts/autonomy-loop.py"
ADAPTER = REPO_ROOT / "plugins/vibeos/scripts/autonomy-runtime-adapter.py"
DETECTOR = REPO_ROOT / "plugins/vibeos/scripts/autonomy-failure-detector.py"
RECOVERY = REPO_ROOT / "plugins/vibeos/scripts/autonomy-recovery-planner.py"
RESOLUTION = REPO_ROOT / "plugins/vibeos/scripts/autonomy-recovery-resolution.py"
GUARD = REPO_ROOT / "plugins/vibeos/scripts/autonomy-scheduler-guard.py"
SCHEDULER = REPO_ROOT / "plugins/vibeos/scripts/autonomy-scheduler-profile.py"
SMOKE = REPO_ROOT / "plugins/vibeos/scripts/autonomy-smoke.py"
VALIDATOR = REPO_ROOT / "plugins/vibeos/scripts/validate-long-run-autonomy.py"
SUPERVISOR = REPO_ROOT / "plugins/vibeos/scripts/autonomy-supervisor.py"
RUNNER = REPO_ROOT / "plugins/vibeos/scripts/autonomy-runner.py"


class LongRunAutonomyTests(unittest.TestCase):
    def run_heartbeat(self, root: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                "python3",
                str(HEARTBEAT),
                "--project-dir",
                str(root),
                "--now",
                "2026-04-29T00:00:00Z",
                "--status",
                "running",
                "--iteration",
                "1",
                "--wo",
                "WO-001",
                "--summary",
                "started long-run loop",
                "--next-action",
                "continue build",
                *extra,
            ],
            capture_output=True,
            text=True,
        )

    def validate(self, root: Path, now: str, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(VALIDATOR), "--project-dir", str(root), "--now", now, "--json", *extra],
            capture_output=True,
            text=True,
        )

    def supervise(self, root: Path, now: str, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(SUPERVISOR), "--project-dir", str(root), "--now", now, "--json", *extra],
            capture_output=True,
            text=True,
        )

    def run_runner(self, root: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(RUNNER), "--project-dir", str(root), "--json", *extra],
            capture_output=True,
            text=True,
        )

    def run_loop(self, root: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(LOOP), "--project-dir", str(root), "--json", *extra],
            capture_output=True,
            text=True,
        )

    def run_adapter(self, root: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(ADAPTER), "--project-dir", str(root), "--json", *extra],
            capture_output=True,
            text=True,
        )

    def run_detector(self, root: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(DETECTOR), "--project-dir", str(root), "--json", *extra],
            capture_output=True,
            text=True,
        )

    def run_recovery(self, root: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(RECOVERY), "--project-dir", str(root), "--json", *extra],
            capture_output=True,
            text=True,
        )

    def run_resolution(self, root: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(RESOLUTION), "--project-dir", str(root), "--json", *extra],
            capture_output=True,
            text=True,
        )

    def run_guard(self, root: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(GUARD), "--project-dir", str(root), "--json", *extra],
            capture_output=True,
            text=True,
        )

    def run_scheduler(self, root: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python3", str(SCHEDULER), "--project-dir", str(root), "--json", *extra],
            capture_output=True,
            text=True,
        )

    def install_autonomy_scripts(self, root: Path, *scripts: Path) -> None:
        scripts_dir = root / ".vibeos/scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        for source in scripts:
            target = scripts_dir / source.name
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            target.chmod(0o755)

    def write_lease(self, root: Path, expires_at: str) -> Path:
        lease_path = root / ".vibeos/autonomy/run-lease.json"
        lease_path.parent.mkdir(parents=True, exist_ok=True)
        lease_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "token": "existing-token",
                    "owner": "test-owner",
                    "operation": "existing-driver",
                    "acquired_at": "2026-04-29T00:00:00Z",
                    "expires_at": expires_at,
                }
            ),
            encoding="utf-8",
        )
        return lease_path

    def test_heartbeat_starts_long_run_and_validator_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_heartbeat(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            config = json.loads((root / ".vibeos/config.json").read_text(encoding="utf-8"))
            session = json.loads((root / ".vibeos/session-state.json").read_text(encoding="utf-8"))
            self.assertTrue(config["autonomy"]["long_run"]["active"])
            self.assertTrue(session["long_run"]["active"])
            self.assertTrue((root / ".vibeos/autonomy/heartbeats").is_dir())

            validation = self.validate(root, "2026-04-29T00:20:00Z")

        self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
        payload = json.loads(validation.stdout)
        self.assertEqual(payload["status"], "pass")

    def test_supervisor_continues_when_cadence_is_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_heartbeat(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            supervisor = self.supervise(root, "2026-04-29T00:05:00Z")
            self.assertTrue((root / ".vibeos/autonomy/resume-plan.json").is_file())

        self.assertEqual(supervisor.returncode, 0, supervisor.stdout + supervisor.stderr)
        payload = json.loads(supervisor.stdout)
        self.assertEqual(payload["decision"]["action"], "continue_build")
        self.assertEqual(payload["decision"]["next_resume_after"], "2026-04-29T00:20:00Z")

    def test_runner_dry_run_classifies_continue_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_heartbeat(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            supervisor = self.supervise(root, "2026-04-29T00:05:00Z")
            self.assertEqual(supervisor.returncode, 0, supervisor.stdout + supervisor.stderr)

            runner = self.run_runner(root)
            self.assertTrue((root / ".vibeos/autonomy/runner-report.json").is_file())

        self.assertEqual(runner.returncode, 0, runner.stdout + runner.stderr)
        payload = json.loads(runner.stdout)
        self.assertEqual(payload["summary"]["status"], "handoff_required")
        self.assertEqual(payload["summary"]["executable"], 1)
        self.assertEqual(payload["summary"]["handoff_required"], 1)
        self.assertTrue(any(item["classification"] == "handoff_required" for item in payload["items"]))

    def test_runner_executes_allowed_heartbeat_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts_dir = root / ".vibeos/scripts"
            scripts_dir.mkdir(parents=True)
            heartbeat_target = scripts_dir / "autonomy-heartbeat.py"
            heartbeat_target.write_text(HEARTBEAT.read_text(encoding="utf-8"), encoding="utf-8")
            heartbeat_target.chmod(0o755)
            plan = {
                "schema_version": "1.0",
                "decision": {"action": "record_heartbeat", "next_resume_after": "2026-04-29T00:00:00Z"},
                "commands": [
                    'python3 ".vibeos/scripts/autonomy-heartbeat.py" --status running '
                    '--iteration 2 --wo "WO-096" --summary "runner execution" --next-action "continue build"'
                ],
            }
            plan_path = root / ".vibeos/autonomy/resume-plan.json"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(json.dumps(plan), encoding="utf-8")

            runner = self.run_runner(root, "--execute")
            heartbeats = list((root / ".vibeos/autonomy/heartbeats").glob("*.json"))

        self.assertEqual(runner.returncode, 0, runner.stdout + runner.stderr)
        payload = json.loads(runner.stdout)
        self.assertEqual(payload["summary"]["status"], "pass")
        self.assertEqual(payload["items"][0]["status"], "passed")
        self.assertTrue(heartbeats)

    def test_runner_blocks_untrusted_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_path = root / ".vibeos/autonomy/resume-plan.json"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(
                json.dumps({"schema_version": "1.0", "commands": ["rm -rf ."]}),
                encoding="utf-8",
            )

            runner = self.run_runner(root)

        self.assertEqual(runner.returncode, 2)
        payload = json.loads(runner.stdout)
        self.assertEqual(payload["summary"]["status"], "blocked")
        self.assertEqual(payload["items"][0]["classification"], "blocked")

    def test_loop_stops_at_model_handoff_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.install_autonomy_scripts(root, SUPERVISOR, RUNNER)
            result = self.run_heartbeat(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            loop = self.run_loop(root, "--now", "2026-04-29T00:05:00Z")
            self.assertTrue((root / ".vibeos/autonomy/loop-state.json").is_file())

        self.assertEqual(loop.returncode, 0, loop.stdout + loop.stderr)
        payload = json.loads(loop.stdout)
        self.assertEqual(payload["summary"]["status"], "handoff_required")
        self.assertEqual(payload["summary"]["iterations"], 1)
        self.assertEqual(payload["iterations"][0]["runner_summary"]["handoff_required"], 1)

    def test_failure_detector_passes_clean_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            history = root / ".vibeos/autonomy/loop-history.jsonl"
            history.parent.mkdir(parents=True)
            history.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-04-29T00:05:00Z",
                        "status": "scheduled",
                        "decision_action": "continue_build",
                        "decision_reason": "cadence and failure controls are within policy",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            detector = self.run_detector(root)
            report_exists = (root / ".vibeos/autonomy/failure-report.json").is_file()

        self.assertEqual(detector.returncode, 0, detector.stdout + detector.stderr)
        payload = json.loads(detector.stdout)
        self.assertEqual(payload["summary"]["status"], "pass")
        self.assertTrue(report_exists)

    def test_failure_detector_flags_repeated_handoff_loop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            history = root / ".vibeos/autonomy/loop-history.jsonl"
            history.parent.mkdir(parents=True)
            rows = [
                {
                    "generated_at": f"2026-04-29T00:0{index}:00Z",
                    "status": "handoff_required",
                    "decision_action": "continue_build",
                    "decision_reason": "cadence and failure controls are within policy",
                }
                for index in range(3)
            ]
            history.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            detector = self.run_detector(root)

        self.assertEqual(detector.returncode, 1, detector.stdout + detector.stderr)
        payload = json.loads(detector.stdout)
        finding_ids = {finding["id"] for finding in payload["findings"]}
        self.assertIn("AUTONOMY-REPEATED-HANDOFF", finding_ids)
        self.assertEqual(payload["summary"]["status"], "fail")

    def test_failure_detector_flags_provider_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter_plan = root / ".vibeos/autonomy/runtime-adapter-plan.json"
            adapter_plan.parent.mkdir(parents=True)
            adapter_plan.write_text(
                json.dumps(
                    {
                        "summary": {"status": "failed", "provider": "codex"},
                        "execution": {
                            "exit_code": 1,
                            "stdout": "",
                            "stderr": "provider rate limit reached; try again later",
                        },
                    }
                ),
                encoding="utf-8",
            )

            detector = self.run_detector(root)

        self.assertEqual(detector.returncode, 1, detector.stdout + detector.stderr)
        payload = json.loads(detector.stdout)
        finding_ids = {finding["id"] for finding in payload["findings"]}
        self.assertIn("AUTONOMY-PROVIDER-LIMIT", finding_ids)
        self.assertIn("AUTONOMY-RUNTIME-FAILED", finding_ids)

    def test_recovery_planner_passes_clean_failure_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / ".vibeos/autonomy/failure-report.json"
            report.parent.mkdir(parents=True)
            report.write_text(
                json.dumps(
                    {
                        "summary": {"status": "pass", "finding_count": 0, "blocking_count": 0},
                        "findings": [],
                    }
                ),
                encoding="utf-8",
            )

            recovery = self.run_recovery(root)
            plan_exists = (root / ".vibeos/autonomy/recovery-plan.json").is_file()

        self.assertEqual(recovery.returncode, 0, recovery.stdout + recovery.stderr)
        payload = json.loads(recovery.stdout)
        self.assertEqual(payload["summary"]["status"], "pass")
        self.assertEqual(payload["summary"]["next_action"], "continue_autonomy")
        self.assertTrue(plan_exists)

    def test_recovery_planner_maps_repeated_handoff_to_runtime_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / ".vibeos/autonomy/failure-report.json"
            report.parent.mkdir(parents=True)
            report.write_text(
                json.dumps(
                    {
                        "summary": {"status": "fail", "finding_count": 1, "blocking_count": 1},
                        "findings": [
                            {
                                "id": "AUTONOMY-REPEATED-HANDOFF",
                                "blocking": True,
                                "message": "handoff repeated",
                                "evidence": {"history": ".vibeos/autonomy/loop-history.jsonl"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            recovery = self.run_recovery(root)

        self.assertEqual(recovery.returncode, 1, recovery.stdout + recovery.stderr)
        payload = json.loads(recovery.stdout)
        self.assertEqual(payload["summary"]["status"], "recovery_required")
        self.assertEqual(payload["actions"][0]["id"], "RECOVERY-RUNTIME-HANDOFF")
        self.assertTrue(any("autonomy-runtime-adapter.py" in command for command in payload["actions"][0]["commands"]))

    def test_recovery_planner_maps_provider_limit_to_pause(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / ".vibeos/autonomy/failure-report.json"
            report.parent.mkdir(parents=True)
            report.write_text(
                json.dumps(
                    {
                        "summary": {"status": "fail", "finding_count": 1, "blocking_count": 1},
                        "findings": [
                            {
                                "id": "AUTONOMY-PROVIDER-LIMIT",
                                "blocking": True,
                                "message": "rate limit",
                                "evidence": {"pattern": "rate limit"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            recovery = self.run_recovery(root)

        self.assertEqual(recovery.returncode, 1, recovery.stdout + recovery.stderr)
        payload = json.loads(recovery.stdout)
        self.assertEqual(payload["actions"][0]["id"], "RECOVERY-PROVIDER-SESSION-LIMIT")
        self.assertTrue(payload["summary"]["stop_scheduler_until_resolved"])
        self.assertTrue(any("provider_or_session_limit" in command for command in payload["actions"][0]["commands"]))

    def test_scheduler_guard_passes_without_recovery_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            guard = self.run_guard(root)
            report_exists = (root / ".vibeos/autonomy/scheduler-guard-report.json").is_file()

        self.assertEqual(guard.returncode, 0, guard.stdout + guard.stderr)
        payload = json.loads(guard.stdout)
        self.assertEqual(payload["summary"]["status"], "pass")
        self.assertTrue(report_exists)

    def test_recovery_resolution_passes_without_recovery_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / ".vibeos/autonomy/recovery-plan.json"
            plan.parent.mkdir(parents=True)
            plan.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-04-29T00:00:00Z",
                        "summary": {"status": "pass", "blocking_action_count": 0},
                        "actions": [],
                    }
                ),
                encoding="utf-8",
            )

            resolution = self.run_resolution(root)
            state_exists = (root / ".vibeos/autonomy/recovery-resolution.json").is_file()

        self.assertEqual(resolution.returncode, 0, resolution.stdout + resolution.stderr)
        payload = json.loads(resolution.stdout)
        self.assertEqual(payload["summary"]["status"], "no_recovery_required")
        self.assertTrue(state_exists)

    def test_recovery_resolution_records_action_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / ".vibeos/autonomy/recovery-plan.json"
            plan.parent.mkdir(parents=True)
            plan.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-04-29T00:00:00Z",
                        "summary": {
                            "status": "recovery_required",
                            "blocking_action_count": 1,
                            "stop_scheduler_until_resolved": True,
                        },
                        "actions": [
                            {
                                "id": "RECOVERY-RUNTIME-HANDOFF",
                                "title": "Resume the model handoff path",
                                "requires_review": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            resolution = self.run_resolution(
                root,
                "--action-id",
                "RECOVERY-RUNTIME-HANDOFF",
                "--summary",
                "runtime adapter executed successfully",
                "--evidence",
                ".vibeos/autonomy/runtime-adapter-plan.json",
            )
            state = json.loads((root / ".vibeos/autonomy/recovery-resolution.json").read_text(encoding="utf-8"))
            history_exists = (root / ".vibeos/autonomy/recovery-resolution-history.jsonl").is_file()

        self.assertEqual(resolution.returncode, 0, resolution.stdout + resolution.stderr)
        payload = json.loads(resolution.stdout)
        self.assertEqual(payload["summary"]["status"], "resolved")
        self.assertEqual(state["resolutions"][0]["action_id"], "RECOVERY-RUNTIME-HANDOFF")
        self.assertTrue(history_exists)

    def test_scheduler_guard_blocks_unresolved_recovery_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / ".vibeos/autonomy/recovery-plan.json"
            plan.parent.mkdir(parents=True)
            plan.write_text(
                json.dumps(
                    {
                        "summary": {
                            "status": "recovery_required",
                            "blocking_action_count": 1,
                            "stop_scheduler_until_resolved": True,
                        },
                        "actions": [
                            {
                                "id": "RECOVERY-PROVIDER-SESSION-LIMIT",
                                "requires_review": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            guard = self.run_guard(root)

        self.assertEqual(guard.returncode, 2, guard.stdout + guard.stderr)
        payload = json.loads(guard.stdout)
        self.assertEqual(payload["summary"]["status"], "blocked")
        self.assertEqual(payload["reasons"][0]["id"], "SCHEDULER-GUARD-RECOVERY-REQUIRED")

    def test_scheduler_guard_passes_resolved_recovery_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / ".vibeos/autonomy/recovery-plan.json"
            plan.parent.mkdir(parents=True)
            plan.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-04-29T00:00:00Z",
                        "summary": {
                            "status": "recovery_required",
                            "blocking_action_count": 1,
                            "stop_scheduler_until_resolved": True,
                        },
                        "actions": [{"id": "RECOVERY-RUNTIME-HANDOFF", "requires_review": True}],
                    }
                ),
                encoding="utf-8",
            )
            resolution = root / ".vibeos/autonomy/recovery-resolution.json"
            resolution.write_text(
                json.dumps(
                    {
                        "resolutions": [
                            {
                                "action_id": "RECOVERY-RUNTIME-HANDOFF",
                                "recovery_plan_generated_at": "2026-04-29T00:00:00Z",
                                "resolved_at": "2026-04-29T00:05:00Z",
                                "resolved_by": "test",
                                "summary": "handoff completed",
                                "evidence": [".vibeos/autonomy/runtime-adapter-plan.json"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            guard = self.run_guard(root)

        self.assertEqual(guard.returncode, 0, guard.stdout + guard.stderr)
        payload = json.loads(guard.stdout)
        self.assertEqual(payload["summary"]["status"], "pass")

    def test_scheduler_guard_blocks_failure_report_without_recovery_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / ".vibeos/autonomy/failure-report.json"
            report.parent.mkdir(parents=True)
            report.write_text(
                json.dumps(
                    {
                        "summary": {"status": "fail", "finding_count": 1, "blocking_count": 1},
                        "findings": [{"id": "AUTONOMY-RUNTIME-FAILED", "blocking": True}],
                    }
                ),
                encoding="utf-8",
            )

            guard = self.run_guard(root)

        self.assertEqual(guard.returncode, 2, guard.stdout + guard.stderr)
        payload = json.loads(guard.stdout)
        self.assertEqual(payload["reasons"][0]["id"], "SCHEDULER-GUARD-MISSING-RECOVERY-PLAN")

    def test_loop_blocks_when_recovery_plan_has_blocking_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / ".vibeos/autonomy/recovery-plan.json"
            plan.parent.mkdir(parents=True)
            plan.write_text(
                json.dumps(
                    {
                        "summary": {
                            "status": "recovery_required",
                            "blocking_action_count": 1,
                            "stop_scheduler_until_resolved": True,
                        },
                        "actions": [{"id": "RECOVERY-RUNTIME-HANDOFF", "requires_review": True}],
                    }
                ),
                encoding="utf-8",
            )

            loop = self.run_loop(root, "--now", "2026-04-29T00:05:00Z")

        self.assertEqual(loop.returncode, 2, loop.stdout + loop.stderr)
        payload = json.loads(loop.stdout)
        self.assertEqual(payload["summary"]["status"], "scheduler_guard_blocked")

    def test_loop_runs_when_recovery_plan_actions_are_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.install_autonomy_scripts(root, SUPERVISOR, RUNNER)
            result = self.run_heartbeat(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            plan = root / ".vibeos/autonomy/recovery-plan.json"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-04-29T00:00:00Z",
                        "summary": {
                            "status": "recovery_required",
                            "blocking_action_count": 1,
                            "stop_scheduler_until_resolved": True,
                        },
                        "actions": [{"id": "RECOVERY-RUNTIME-HANDOFF", "requires_review": True}],
                    }
                ),
                encoding="utf-8",
            )
            resolution = root / ".vibeos/autonomy/recovery-resolution.json"
            resolution.write_text(
                json.dumps(
                    {
                        "resolutions": [
                            {
                                "action_id": "RECOVERY-RUNTIME-HANDOFF",
                                "recovery_plan_generated_at": "2026-04-29T00:00:00Z",
                                "resolved_at": "2026-04-29T00:05:00Z",
                                "resolved_by": "test",
                                "summary": "handoff completed",
                                "evidence": [".vibeos/autonomy/runtime-adapter-plan.json"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            loop = self.run_loop(root, "--now", "2026-04-29T00:05:00Z")

        self.assertEqual(loop.returncode, 0, loop.stdout + loop.stderr)
        payload = json.loads(loop.stdout)
        self.assertNotEqual(payload["summary"]["status"], "scheduler_guard_blocked")

    def test_loop_blocks_when_active_lease_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_lease(root, "2999-01-01T00:00:00Z")

            loop = self.run_loop(root, "--now", "2026-04-29T00:05:00Z")
            conflict = root / ".vibeos/autonomy/lease-conflict.json"
            conflict_exists = conflict.is_file()

        self.assertEqual(loop.returncode, 2)
        payload = json.loads(loop.stdout)
        self.assertEqual(payload["summary"]["status"], "lease_conflict")
        self.assertEqual(payload["active_lease"]["owner"], "test-owner")
        self.assertTrue(conflict_exists)

    def test_loop_recovers_stale_lease(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.install_autonomy_scripts(root, SUPERVISOR, RUNNER)
            result = self.run_heartbeat(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            lease_path = self.write_lease(root, "2026-04-28T00:00:00Z")

            loop = self.run_loop(root, "--now", "2026-04-29T00:05:00Z")
            last_lease = json.loads((root / ".vibeos/autonomy/last-lease.json").read_text(encoding="utf-8"))
            lease_exists = lease_path.exists()

        self.assertEqual(loop.returncode, 0, loop.stdout + loop.stderr)
        payload = json.loads(loop.stdout)
        self.assertEqual(payload["summary"]["status"], "handoff_required")
        self.assertFalse(lease_exists)
        self.assertIn("recovered_stale_lease", last_lease)

    def test_loop_executes_due_heartbeat_tick(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.install_autonomy_scripts(root, HEARTBEAT, SUPERVISOR, RUNNER)
            result = self.run_heartbeat(root, "--heartbeat-interval-minutes", "10")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            loop = self.run_loop(root, "--now", "2026-04-29T00:10:00Z", "--execute")
            heartbeats = list((root / ".vibeos/autonomy/heartbeats").glob("*.json"))

        self.assertEqual(loop.returncode, 0, loop.stdout + loop.stderr)
        payload = json.loads(loop.stdout)
        self.assertEqual(payload["summary"]["status"], "iteration_limit")
        self.assertEqual(payload["iterations"][0]["runner_summary"]["executed"], 1)
        self.assertGreaterEqual(len(heartbeats), 2)

    def test_runtime_adapter_builds_codex_handoff_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".vibeos/autonomy").mkdir(parents=True)
            (root / ".vibeos/runtime-capabilities.json").write_text(
                json.dumps(
                    {
                        "runtimes": {"codex": {"available": True}, "claude": {"available": False}},
                        "strategy": {"recommended_primary": "codex"},
                    }
                ),
                encoding="utf-8",
            )
            (root / ".vibeos/autonomy/loop-state.json").write_text(
                json.dumps({"summary": {"status": "handoff_required"}}),
                encoding="utf-8",
            )

            adapter = self.run_adapter(root)

        self.assertEqual(adapter.returncode, 0, adapter.stdout + adapter.stderr)
        payload = json.loads(adapter.stdout)
        self.assertEqual(payload["summary"]["status"], "ready")
        self.assertEqual(payload["command"]["provider"], "codex")
        self.assertEqual(payload["command"]["argv"][:2], ["codex", "exec"])
        self.assertIn(".vibeos/autonomy/loop-state.json", payload["prompt"])

    def test_runtime_adapter_reports_no_handoff_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".vibeos/autonomy").mkdir(parents=True)
            (root / ".vibeos/runtime-capabilities.json").write_text(
                json.dumps(
                    {
                        "runtimes": {"codex": {"available": True}, "claude": {"available": False}},
                        "strategy": {"recommended_primary": "codex"},
                    }
                ),
                encoding="utf-8",
            )
            (root / ".vibeos/autonomy/loop-state.json").write_text(
                json.dumps({"summary": {"status": "scheduled"}}),
                encoding="utf-8",
            )

            adapter = self.run_adapter(root)

        self.assertEqual(adapter.returncode, 0, adapter.stdout + adapter.stderr)
        payload = json.loads(adapter.stdout)
        self.assertEqual(payload["summary"]["status"], "no_handoff")

    def test_runtime_adapter_blocks_when_active_lease_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".vibeos/autonomy").mkdir(parents=True)
            (root / ".vibeos/runtime-capabilities.json").write_text(
                json.dumps(
                    {
                        "runtimes": {"codex": {"available": True}, "claude": {"available": False}},
                        "strategy": {"recommended_primary": "codex"},
                    }
                ),
                encoding="utf-8",
            )
            (root / ".vibeos/autonomy/loop-state.json").write_text(
                json.dumps({"summary": {"status": "handoff_required"}}),
                encoding="utf-8",
            )
            self.write_lease(root, "2999-01-01T00:00:00Z")

            adapter = self.run_adapter(root)

        self.assertEqual(adapter.returncode, 2)
        payload = json.loads(adapter.stdout)
        self.assertEqual(payload["summary"]["status"], "lease_conflict")

    def test_scheduler_profile_generates_shell_and_cron_profiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_scheduler(root, "--profile", "shell,cron", "--interval-minutes", "10")

            shell_profile = root / ".vibeos/autonomy/scheduler/vibeos-autonomy-tick.sh"
            cron_profile = root / ".vibeos/autonomy/scheduler/vibeos-autonomy.cron"
            state = root / ".vibeos/autonomy/scheduler-profile.json"
            shell_exists = shell_profile.is_file()
            cron_exists = cron_profile.is_file()
            state_exists = state.is_file()
            shell_text = shell_profile.read_text(encoding="utf-8")
            cron_text = cron_profile.read_text(encoding="utf-8")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["profile_count"], 2)
        self.assertTrue(shell_exists)
        self.assertTrue(cron_exists)
        self.assertTrue(state_exists)
        self.assertIn("autonomy-scheduler-guard.py", shell_text)
        self.assertIn("autonomy-loop.py", shell_text)
        self.assertIn("*/10 * * * *", cron_text)

    def test_smoke_runs_disposable_autonomy_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "smoke-target"
            result = subprocess.run(
                [
                    "python3",
                    str(SMOKE),
                    "--project-dir",
                    str(root),
                    "--runtime-provider",
                    "codex",
                    "--json",
                ],
                capture_output=True,
                text=True,
            )
            report_path = root / ".vibeos/autonomy/smoke-report.json"
            loop_state = root / ".vibeos/autonomy/loop-state.json"
            adapter_plan = root / ".vibeos/autonomy/runtime-adapter-plan.json"
            report_exists = report_path.is_file()
            loop_exists = loop_state.is_file()
            adapter_exists = adapter_plan.is_file()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["status"], "pass")
        self.assertTrue(report_exists)
        self.assertTrue(loop_exists)
        self.assertTrue(adapter_exists)
        self.assertEqual([step["name"] for step in payload["steps"]][-1], "scheduler-guard")

    def test_supervisor_requests_checkpoint_when_due(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_heartbeat(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            supervisor = self.supervise(root, "2026-04-29T01:00:00Z")

        self.assertEqual(supervisor.returncode, 0, supervisor.stdout + supervisor.stderr)
        payload = json.loads(supervisor.stdout)
        self.assertEqual(payload["decision"]["action"], "run_checkpoint")
        self.assertEqual(payload["decision"]["next_resume_after"], "2026-04-29T01:00:00Z")
        self.assertTrue(any("autonomy-heartbeat.py" in command for command in payload["commands"]))

    def test_supervisor_requests_audit_when_due(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_heartbeat(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            supervisor = self.supervise(root, "2026-04-29T03:00:00Z")

        self.assertEqual(supervisor.returncode, 0, supervisor.stdout + supervisor.stderr)
        payload = json.loads(supervisor.stdout)
        self.assertEqual(payload["decision"]["action"], "run_audit")
        self.assertTrue(any("gate-runner.sh" in command for command in payload["commands"]))

    def test_supervisor_stops_when_iteration_budget_exceeded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_heartbeat(root, "--iteration", "512")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            supervisor = self.supervise(root, "2026-04-29T00:05:00Z")

        self.assertEqual(supervisor.returncode, 0, supervisor.stdout + supervisor.stderr)
        payload = json.loads(supervisor.stdout)
        self.assertEqual(payload["decision"]["action"], "stop")
        self.assertTrue(payload["decision"]["requires_human"])

    def test_validator_fails_stale_heartbeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_heartbeat(root, "--heartbeat-interval-minutes", "10")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            validation = self.validate(root, "2026-04-29T01:00:00Z")

        self.assertEqual(validation.returncode, 1)
        payload = json.loads(validation.stdout)
        self.assertTrue(any(item["id"] == "LONGRUN-HEARTBEAT-STALE" for item in payload["findings"]))

    def test_validator_fails_duration_above_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_heartbeat(root, "--target-hours", "72", "--max-hours", "72")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            validation = self.validate(root, "2026-04-29T00:20:00Z")

        self.assertEqual(validation.returncode, 1)
        payload = json.loads(validation.stdout)
        self.assertTrue(any(item["id"] == "LONGRUN-DURATION-POLICY" for item in payload["findings"]))
        self.assertTrue(any(item["id"] == "LONGRUN-MAX-DURATION-POLICY" for item in payload["findings"]))

    def test_complete_heartbeat_closes_long_run_for_session_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            start = self.run_heartbeat(root)
            self.assertEqual(start.returncode, 0, start.stdout + start.stderr)

            complete = subprocess.run(
                [
                    "python3",
                    str(HEARTBEAT),
                    "--project-dir",
                    str(root),
                    "--now",
                    "2026-04-29T01:00:00Z",
                    "--status",
                    "complete",
                    "--iteration",
                    "2",
                    "--summary",
                    "long-run loop complete",
                    "--next-action",
                    "session audit",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(complete.returncode, 0, complete.stdout + complete.stderr)

            validation = self.validate(root, "2026-04-29T01:05:00Z", "--require-closed")

        self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
        payload = json.loads(validation.stdout)
        self.assertEqual(payload["status"], "pass")


if __name__ == "__main__":
    unittest.main()
