import json
import shutil

from tests.controlled_evaluation_fixtures import ControlledEvaluationCase


class ControlledEvaluationEvidenceTests(ControlledEvaluationCase):
    def prepare_and_evaluate(self, mode="pass", **extra):
        self.write_behavior(mode, **extra)
        self.assert_ok(self.prepare())
        return self.evaluate()

    def test_positive_evaluation_publication_and_exact_idempotent_retry(self):
        result = self.prepare_and_evaluate()
        self.assert_ok(result)
        self.assertTrue((self.owner / "results/current.json").is_file())
        self.assertTrue(
            (self.owner / "results/checks/run-1/owner-report.xml").is_file()
        )
        self.assertTrue((self.owner / "results/checks/run-1/checks.json").is_file())
        self.assertTrue((self.owner / "results/checks/run-1/project.json").is_file())
        self.assertTrue(
            (self.owner / "results/checks/run-1/project-evidence/identity.txt").is_file()
        )
        current = json.loads(
            (self.owner / "results/current.json").read_text(encoding="utf-8")
        )
        self.assertTrue(current["eligible"])
        self.assertFalse((self.owner / "results/runs/run-1/admitted.json").exists())

        first = self.publish()
        self.assert_ok(first)
        published = self.owner / "results/published/run-1.json"
        packet = json.loads(published.read_text(encoding="utf-8"))
        self.assertEqual(packet["status"], "PRE_REVIEW")
        self.assertFalse(packet["project_qualified"])
        self.assertFalse(packet["runtime_qualified"])
        self.assertTrue((self.owner / "results/runs/run-1/admitted.json").is_file())
        before = published.read_bytes()
        first_stat = published.stat()

        retry = self.publish()
        self.assert_ok(retry)
        self.assertEqual(published.read_bytes(), before)
        self.assertEqual(published.stat().st_ino, first_stat.st_ino)
        self.assertEqual(published.stat().st_mtime_ns, first_stat.st_mtime_ns)

    def test_evaluation_seals_exact_source_artifacts(self):
        self.assert_ok(self.prepare_and_evaluate())
        pairs = [
            ("owner-report.xml", "sealed-owner-report.xml"),
            ("checks.json", "sealed-checks.json"),
            ("project.json", "sealed-project.json"),
        ]
        for live_name, sealed_name in pairs:
            with self.subTest(name=live_name):
                live = self.owner / "results/checks/run-1" / live_name
                sealed = self.owner / "results/runs/run-1" / sealed_name
                self.assertEqual(sealed.read_bytes(), live.read_bytes())

    def test_required_owner_case_anomalies_are_refused(self):
        for mode in ["missing", "empty", "failed", "skipped", "duplicate"]:
            with self.subTest(mode=mode):
                self.tearDown()
                self.setUp()
                result = self.prepare_and_evaluate(mode)
                self.assert_failed(result)
                self.assertFalse(
                    (self.owner / "results/runs/run-1/admitted.json").exists()
                )

    def test_malformed_and_duplicate_project_or_check_evidence_is_refused(self):
        for mode in [
            "malformed_xml",
            "malformed_project",
            "duplicate_project",
            "missing_project",
            "malformed_checks",
        ]:
            with self.subTest(mode=mode):
                self.tearDown()
                self.setUp()
                result = self.prepare_and_evaluate(mode)
                self.assert_failed(result)
                self.assertFalse(
                    (self.owner / "results/runs/run-1/admitted.json").exists()
                )

    def test_nonzero_codex_exit_one_through_six_refuses_successful_xml(self):
        for exit_code in range(1, 7):
            with self.subTest(exit_code=exit_code):
                self.tearDown()
                self.setUp()
                result = self.prepare_and_evaluate("pass", exit_code=exit_code)
                self.assert_failed(result)
                report = self.owner / "results/checks/run-1/owner-report.xml"
                self.assertTrue(report.is_file(), result.stdout + result.stderr)
                self.assertFalse(
                    (self.owner / "results/runs/run-1/admitted.json").exists()
                )

    def test_publish_rejects_tampered_or_stale_evidence_and_noncurrent_run(self):
        self.assert_ok(self.prepare_and_evaluate())
        sealed = self.owner / "results/runs/run-1/sealed-checks.json"
        sealed.write_text("{}", encoding="utf-8")
        self.assert_failed(self.publish())

        self.tearDown()
        self.setUp()
        self.assert_ok(self.prepare_and_evaluate())
        current = self.owner / "results/current.json"
        current.write_text(
            json.dumps({"schema": "vibeos.controlled-evaluation.current.v1", "run": "run-2"}),
            encoding="utf-8",
        )
        self.assert_failed(self.publish("run-1"))

    def test_publish_refuses_links_and_wrong_artifact_types(self):
        self.assert_ok(self.prepare_and_evaluate())
        sealed = self.owner / "results/runs/run-1/sealed-project.json"
        replacement = self.root / "replacement.json"
        replacement.write_bytes(sealed.read_bytes())
        sealed.unlink()
        sealed.symlink_to(replacement)
        self.assert_failed(self.publish())

        self.tearDown()
        self.setUp()
        self.assert_ok(self.prepare_and_evaluate())
        evidence = self.owner / "results/checks/run-1/project-evidence"
        shutil.rmtree(evidence)
        evidence.write_text("wrong type\n", encoding="utf-8")
        self.assert_failed(self.publish())
