import json
import subprocess
import time

from tests.controlled_evaluation_fixtures import (
    ENTRYPOINT,
    ControlledEvaluationCase,
)


class ControlledEvaluationRuntimeTests(ControlledEvaluationCase):
    def test_candidate_source_drift_refuses_evaluation(self):
        self.assert_ok(self.prepare())
        (self.candidate / "artifact.txt").write_text("changed after prepare\n", encoding="utf-8")

        result = self.evaluate()

        self.assert_failed(result)
        self.assertFalse((self.owner / "results/runs/run-1/admitted.json").exists())

    def test_config_tool_and_dependency_drift_are_refused(self):
        cases = ["config", "tool", "dependency"]
        for drift in cases:
            with self.subTest(drift=drift):
                self.tearDown()
                self.setUp()
                self.assert_ok(self.prepare())
                if drift == "config":
                    config = self.owner / "protected-owner/config.json"
                    value = json.loads(config.read_text(encoding="utf-8"))
                    value["timeout_seconds"] = 99
                    config.write_text(json.dumps(value), encoding="utf-8")
                elif drift == "tool":
                    self.fake_ruff.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
                else:
                    self.behavior.write_text(
                        json.dumps({"mode": "pass", "changed": True}), encoding="utf-8"
                    )

                result = self.evaluate()
                self.assert_failed(result)
                self.assertFalse(
                    (self.owner / "results/runs/run-1/admitted.json").exists()
                )

    def test_actual_timeout_invalidates_run(self):
        self.write_behavior("timeout", seconds=20)
        self.assert_ok(self.prepare())

        started = time.monotonic()
        result = self.evaluate(timeout=10)
        elapsed = time.monotonic() - started

        self.assert_failed(result)
        self.assertLess(elapsed, 8, result.stdout + result.stderr)
        self.assertFalse((self.owner / "results/runs/run-1/admitted.json").exists())

    def test_actual_sigterm_invalidates_run(self):
        self.write_behavior("sigterm")
        self.assert_ok(self.prepare())

        result = self.evaluate()

        self.assert_failed(result)
        self.assertFalse((self.owner / "results/runs/run-1/admitted.json").exists())

    def test_single_writer_lock_refuses_conflicting_evaluation(self):
        self.write_behavior("hold", seconds=1.5)
        self.assert_ok(self.prepare())
        first = subprocess.Popen(
            [
                str(self.spec_value()["tools"]["python"]),
                str(ENTRYPOINT),
                "evaluate",
                "--owner",
                str(self.owner),
                "--run",
                "run-1",
            ],
            cwd=ENTRYPOINT.parents[3],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        lock = self.owner / "results/writer.lock"
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and not lock.exists():
            time.sleep(0.02)
        time.sleep(0.2)

        second = self.evaluate("run-2")
        first_stdout, first_stderr = first.communicate(timeout=8)

        self.assertEqual(first.returncode, 0, first_stdout + first_stderr)
        self.assert_failed(second)
        self.assertFalse((self.owner / "results/runs/run-2/admitted.json").exists())

    def test_run_name_and_publish_eligibility_are_strict(self):
        self.assert_ok(self.prepare())
        for invalid in ["../run-1", "run/1", "run-0", "other-1", "run-01"]:
            with self.subTest(run=invalid):
                self.assert_failed(self.evaluate(invalid))
        self.assert_failed(self.publish("run-1"))

    def test_second_evaluation_cannot_replace_immutable_run(self):
        self.assert_ok(self.prepare())
        self.assert_ok(self.evaluate("run-1"))
        record = self.owner / "results/runs/run-1/record.json"
        before = record.read_bytes()

        result = self.evaluate("run-1")

        self.assert_failed(result)
        self.assertEqual(record.read_bytes(), before)
