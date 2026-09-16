import json
import hashlib
import os
from pathlib import Path

from tests.controlled_evaluation_fixtures import (
    ControlledEvaluationCase,
    git,
)


class ControlledEvaluationPrepareTests(ControlledEvaluationCase):
    def test_prepare_creates_protected_owner_without_changing_candidate(self):
        before = {
            path.relative_to(self.candidate): path.read_bytes()
            for path in self.candidate.rglob("*")
            if path.is_file() and ".git" not in path.parts
        }
        head = git(self.candidate, "rev-parse", "HEAD").stdout.strip()

        result = self.prepare()

        self.assert_ok(result)
        self.assertTrue((self.owner / "protected-owner/config.json").is_file())
        self.assertTrue((self.owner / "harness-adaptation").is_dir())
        self.assertTrue((self.owner / "results/writer.lock").is_file())
        self.assertTrue((self.owner / "results/checks").is_dir())
        self.assertTrue((self.owner / "results/runs").is_dir())
        self.assertTrue((self.owner / "results/published").is_dir())
        self.assertEqual(git(self.candidate, "rev-parse", "HEAD").stdout.strip(), head)
        after = {
            path.relative_to(self.candidate): path.read_bytes()
            for path in self.candidate.rglob("*")
            if path.is_file() and ".git" not in path.parts
        }
        self.assertEqual(after, before)

        config = json.loads(
            (self.owner / "protected-owner/config.json").read_text(encoding="utf-8")
        )
        rendered = json.dumps(config, sort_keys=True)
        self.assertIn(head, rendered)
        self.assertIn(str(self.candidate.resolve()), rendered)
        self.assertIn("test_candidate_file", rendered)
        self.assertIn("project-build", rendered)
        self.assertIn("manual-provider-check", rendered)

    def test_two_distinct_project_identities_and_paths_with_spaces_prepare(self):
        self.assert_ok(self.prepare())
        config_one = (self.owner / "protected-owner/config.json").read_bytes()

        owner_two = self.root / "second protected owner"
        candidate_two = self.root / "candidate project two with spaces"
        self.make_candidate(candidate_two, "project-two")
        result = self.cli(
            "prepare",
            "--owner",
            owner_two,
            "--candidate",
            candidate_two,
            "--spec",
            self.spec,
        )

        self.assert_ok(result)
        config_two = (owner_two / "protected-owner/config.json").read_bytes()
        self.assertNotEqual(config_one, config_two)
        self.assertIn(str(candidate_two.resolve()), config_two.decode("utf-8"))
        self.assertIn("project-two", (candidate_two / "PROJECT-ID.txt").read_text())

    def test_prepare_refuses_any_preexisting_owner_content_without_clobber(self):
        self.owner.mkdir()
        sentinel = self.owner / "keep-me.txt"
        sentinel.write_text("owner bytes\n", encoding="utf-8")

        result = self.prepare()

        self.assert_failed(result)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "owner bytes\n")
        self.assertEqual(list(self.owner.iterdir()), [sentinel])

    def test_prepare_refuses_same_nested_and_nonnative_paths(self):
        cases = [
            (self.candidate, self.candidate),
            (self.candidate / "nested owner", self.candidate),
            (self.root / "outer owner", self.root / "outer owner/candidate"),
        ]
        for index, (owner, candidate) in enumerate(cases):
            with self.subTest(index=index):
                if index == 2:
                    candidate.mkdir(parents=True)
                    (candidate / "PROJECT-ID.txt").write_text("nested\n", encoding="utf-8")
                    git(candidate, "init", "-q")
                    git(candidate, "add", ".")
                    git(
                        candidate,
                        "-c",
                        "user.name=Test Owner",
                        "-c",
                        "user.email=test-owner@example.invalid",
                        "commit",
                        "-qm",
                        "baseline",
                    )
                result = self.cli(
                    "prepare",
                    "--owner",
                    owner,
                    "--candidate",
                    candidate,
                    "--spec",
                    self.spec,
                )
                self.assert_failed(result)

        candidate_link = self.root / "candidate link"
        candidate_link.symlink_to(self.candidate, target_is_directory=True)
        result = self.cli(
            "prepare",
            "--owner",
            self.root / "owner for linked candidate",
            "--candidate",
            candidate_link,
            "--spec",
            self.spec,
        )
        self.assert_failed(result)

    def test_prepare_rejects_non_git_and_pins_uncommitted_candidate_bytes(self):
        nongit = self.root / "candidate without git"
        nongit.mkdir()
        (nongit / "file.txt").write_text("bytes\n", encoding="utf-8")
        result = self.cli(
            "prepare",
            "--owner",
            self.root / "owner nongit",
            "--candidate",
            nongit,
            "--spec",
            self.spec,
        )
        self.assert_failed(result)

        (self.candidate / "artifact.txt").write_text("dirty\n", encoding="utf-8")
        result = self.cli(
            "prepare",
            "--owner",
            self.root / "owner dirty",
            "--candidate",
            self.candidate,
            "--spec",
            self.spec,
        )
        self.assert_ok(result)
        config = json.loads(
            (self.root / "owner dirty/protected-owner/config.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            config["baseline_files"]["artifact.txt"],
            hashlib.sha256(b"dirty\n").hexdigest(),
        )
        (self.candidate / "artifact.txt").write_text(
            "changed after dirty baseline\n", encoding="utf-8"
        )
        original_owner = self.owner
        self.owner = self.root / "owner dirty"
        try:
            self.assert_failed(self.evaluate())
        finally:
            self.owner = original_owner

    def test_prepare_rejects_malformed_duplicate_unsorted_and_unsafe_spec(self):
        malformed = self.inputs / "malformed.json"
        malformed.write_text("{", encoding="utf-8")
        result = self.cli(
            "prepare",
            "--owner",
            self.root / "owner malformed",
            "--candidate",
            self.candidate,
            "--spec",
            malformed,
        )
        self.assert_failed(result)

        mutations = []
        duplicate_owner = self.spec_value()
        duplicate_owner["required_owner_tests"] = [
            "test_candidate_file",
            "test_candidate_file",
        ]
        mutations.append(duplicate_owner)
        duplicate_project = self.spec_value()
        duplicate_project["required_project_cases"] = ["project-build", "project-build"]
        mutations.append(duplicate_project)
        unsorted = self.spec_value()
        unsorted["required_project_cases"] = ["project-test", "project-build"]
        mutations.append(unsorted)
        traversal = self.spec_value()
        traversal["writable_files"] = ["../escape.txt"]
        mutations.append(traversal)
        absolute_write = self.spec_value()
        absolute_write["writable_files"] = [str((self.root / "escape.txt").resolve())]
        mutations.append(absolute_write)
        empty_required = self.spec_value()
        empty_required["required_owner_tests"] = []
        mutations.append(empty_required)

        for index, spec in enumerate(mutations):
            with self.subTest(index=index):
                self.write_spec(spec)
                result = self.cli(
                    "prepare",
                    "--owner",
                    self.root / f"owner invalid {index}",
                    "--candidate",
                    self.candidate,
                    "--spec",
                    self.spec,
                )
                self.assert_failed(result)

    def test_prepare_rejects_symlinked_input_and_nonabsolute_dependencies(self):
        dependency_link = self.inputs / "behavior link.json"
        dependency_link.symlink_to(self.behavior)
        linked = self.spec_value()
        linked["dependencies"] = [str(dependency_link.absolute())]
        self.write_spec(linked)
        self.assert_failed(self.prepare())

        relative = self.spec_value()
        relative["dependencies"] = [os.path.relpath(self.behavior, self.root)]
        self.write_spec(relative)
        result = self.cli(
            "prepare",
            "--owner",
            self.root / "owner relative dependency",
            "--candidate",
            self.candidate,
            "--spec",
            self.spec,
        )
        self.assert_failed(result)
