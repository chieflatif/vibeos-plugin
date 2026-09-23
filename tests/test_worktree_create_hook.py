"""Spec-first tests for the WorktreeCreate hook (WO-168).

Contract (Claude Code hooks reference, WorktreeCreate): the hook receives JSON
on stdin with at least ``name`` and ``cwd``; it must print the absolute path of
the created worktree as the last non-empty stdout line; empty stdout or a
non-zero exit means worktree creation fails. A registered hook replaces Claude
Code's default creation, so it must work in every repository, VibeOS or not.
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / "plugins/vibeos/hooks/scripts/worktree-scope-setup.sh"


class WorktreeCreateHookTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name).resolve()
        self.home = self.base / "home"
        self.home.mkdir()
        self.env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(self.home),
            "LANG": "C",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "VibeOS Test",
            "GIT_AUTHOR_EMAIL": "vibeos-test@example.com",
            "GIT_COMMITTER_NAME": "VibeOS Test",
            "GIT_COMMITTER_EMAIL": "vibeos-test@example.com",
        }

    # -- helpers ---------------------------------------------------------------

    def git(self, cwd: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=cwd, env=self.env, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()

    def commit(self, repo: Path, filename: str, content: str, message: str) -> str:
        (repo / filename).write_text(content, encoding="utf-8")
        self.git(repo, "add", filename)
        self.git(repo, "commit", "-q", "-m", message)
        return self.git(repo, "rev-parse", "HEAD")

    def make_repo(self, name: str = "project", with_origin: bool = False):
        """Plain (non-VibeOS) repo. With origin: first commit pushed, second unpushed."""
        repo = self.base / name
        repo.mkdir()
        self.git(repo, "init", "-q", "-b", "main")
        pushed = self.commit(repo, "README.md", "# fixture\n", "first")
        unpushed = None
        if with_origin:
            origin = self.base / f"{name}-origin.git"
            self.git(self.base, "init", "-q", "--bare", "-b", "main", str(origin))
            self.git(repo, "remote", "add", "origin", str(origin))
            self.git(repo, "push", "-q", "origin", "main")
            self.git(repo, "remote", "set-head", "origin", "main")
            unpushed = self.commit(repo, "local.txt", "unpushed\n", "second, not pushed")
        return repo, pushed, unpushed

    def write_settings(self, path: Path, base_ref=None, raw=None):
        path.parent.mkdir(parents=True, exist_ok=True)
        if raw is not None:
            path.write_text(raw, encoding="utf-8")
        else:
            path.write_text(json.dumps({"worktree": {"baseRef": base_ref}}) + "\n", encoding="utf-8")

    def run_hook(self, name: str, cwd: Path, extra_env=None):
        env = dict(self.env)
        env["CLAUDE_PROJECT_DIR"] = str(cwd)
        if extra_env:
            env.update(extra_env)
        payload = {
            "session_id": "test-session",
            "transcript_path": str(self.base / "transcript.jsonl"),
            "cwd": str(cwd),
            "hook_event_name": "WorktreeCreate",
            "name": name,
        }
        return subprocess.run(
            ["bash", str(HOOK)], input=json.dumps(payload), capture_output=True, text=True, env=env
        )

    def returned_path(self, result) -> Path:
        # Contract: on success stdout is exactly one absolute path and a newline.
        self.assertTrue(result.stdout.endswith("\n"), f"stdout={result.stdout!r} stderr={result.stderr!r}")
        self.assertEqual(result.stdout.count("\n"), 1, f"stdout must be one line: {result.stdout!r}")
        path = Path(result.stdout[:-1])
        self.assertTrue(path.is_absolute(), f"not absolute: {result.stdout!r}")
        return path

    def assert_refused(self, result):
        self.assertNotEqual(result.returncode, 0, f"expected refusal; stdout={result.stdout!r}")
        self.assertEqual(result.stdout, "", "a refusal must print nothing on stdout")

    # -- behaviour -------------------------------------------------------------

    def test_creates_worktree_in_repository_without_vibeos_marker(self):
        repo, _, _ = self.make_repo()
        self.assertFalse((repo / ".vibeos").exists())

        result = self.run_hook("plain-one", repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.returned_path(result)
        self.assertTrue(target.is_absolute())
        self.assertTrue(target.is_dir())
        self.assertEqual(target.resolve(), (repo / ".claude/worktrees/plain-one").resolve())
        self.assertEqual(self.git(target, "rev-parse", "--abbrev-ref", "HEAD"), "worktree-plain-one")
        self.assertEqual(Path(self.git(target, "rev-parse", "--show-toplevel")).resolve(), target.resolve())
        self.assertNotEqual(
            Path(self.git(target, "rev-parse", "--git-dir")).resolve(),
            Path(self.git(repo, "rev-parse", "--git-dir")).resolve(),
            "expected a linked worktree, not the main checkout",
        )

    def test_path_is_the_only_stdout_line(self):
        repo, _, _ = self.make_repo()

        result = self.run_hook("quiet-one", repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, str(self.returned_path(result)) + "\n")

    def test_base_ref_head_uses_current_head_including_unpushed_commits(self):
        repo, _, unpushed = self.make_repo(with_origin=True)
        self.write_settings(self.home / ".claude/settings.json", base_ref="head")

        result = self.run_hook("from-head", repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.returned_path(result)
        self.assertEqual(self.git(target, "rev-parse", "HEAD"), unpushed)

    def test_base_ref_fresh_uses_origin_default_branch(self):
        repo, pushed, _ = self.make_repo(with_origin=True)
        self.write_settings(self.home / ".claude/settings.json", base_ref="fresh")

        result = self.run_hook("from-origin", repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.returned_path(result)
        self.assertEqual(self.git(target, "rev-parse", "HEAD"), pushed)

    def test_no_setting_defaults_to_fresh(self):
        repo, pushed, _ = self.make_repo(with_origin=True)

        result = self.run_hook("default-mode", repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git(self.returned_path(result), "rev-parse", "HEAD"), pushed)

    def test_fresh_without_remote_falls_back_to_head(self):
        repo, pushed, _ = self.make_repo(with_origin=False)
        self.write_settings(self.home / ".claude/settings.json", base_ref="fresh")

        result = self.run_hook("no-remote", repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git(self.returned_path(result), "rev-parse", "HEAD"), pushed)

    def test_project_settings_override_user_settings(self):
        repo, _, unpushed = self.make_repo(with_origin=True)
        self.write_settings(self.home / ".claude/settings.json", base_ref="fresh")
        self.write_settings(repo / ".claude/settings.json", base_ref="head")

        result = self.run_hook("project-wins", repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git(self.returned_path(result), "rev-parse", "HEAD"), unpushed)

    def test_local_settings_override_project_settings(self):
        repo, pushed, _ = self.make_repo(with_origin=True)
        self.write_settings(repo / ".claude/settings.json", base_ref="head")
        self.write_settings(repo / ".claude/settings.local.json", base_ref="fresh")

        result = self.run_hook("local-wins", repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git(self.returned_path(result), "rev-parse", "HEAD"), pushed)

    def test_malformed_settings_file_is_ignored(self):
        repo, pushed, _ = self.make_repo(with_origin=True)
        self.write_settings(self.home / ".claude/settings.json", raw="{ not json")

        result = self.run_hook("bad-settings", repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git(self.returned_path(result), "rev-parse", "HEAD"), pushed)

    def test_existing_worktree_of_same_name_is_reopened(self):
        repo, _, _ = self.make_repo()
        first = self.run_hook("again", repo)
        self.assertEqual(first.returncode, 0, first.stderr)

        second = self.run_hook("again", repo)

        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.returned_path(second).resolve(), self.returned_path(first).resolve())

    def test_invalid_name_fails_with_empty_stdout(self):
        repo, _, _ = self.make_repo()

        self.assert_refused(self.run_hook("../escape", repo))

    def test_cwd_outside_git_fails_with_empty_stdout(self):
        not_a_repo = self.base / "plain-dir"
        not_a_repo.mkdir()

        self.assert_refused(self.run_hook("outside", not_a_repo))

    def test_multiline_name_is_refused(self):
        repo, _, _ = self.make_repo()

        self.assert_refused(self.run_hook("ok\n../escape", repo))
        self.assert_refused(self.run_hook("ok\nbad name", repo))

    def test_dot_names_are_refused(self):
        repo, _, _ = self.make_repo()

        self.assert_refused(self.run_hook(".", repo))
        self.assert_refused(self.run_hook("..", repo))

    def test_symlink_to_main_checkout_is_not_accepted_as_existing_worktree(self):
        repo, _, _ = self.make_repo()
        (repo / ".claude/worktrees").mkdir(parents=True)
        (repo / ".claude/worktrees/alias").symlink_to(repo)

        self.assert_refused(self.run_hook("alias", repo))

    def test_plain_directory_is_not_accepted_as_existing_worktree(self):
        repo, _, _ = self.make_repo()
        (repo / ".claude/worktrees/not-a-worktree").mkdir(parents=True)

        self.assert_refused(self.run_hook("not-a-worktree", repo))

    def test_registered_worktree_with_broken_git_link_is_not_reopened(self):
        repo, _, _ = self.make_repo()
        first = self.run_hook("broken", repo)
        target = self.returned_path(first)
        # Simulate a damaged worktree: its .git link file is moved aside, but
        # the registration in the main repository remains.
        (target / ".git").rename(target / "git-link-moved-aside")

        self.assert_refused(self.run_hook("broken", repo))

    def test_reopen_returns_existing_worktree_unchanged(self):
        repo, _, _ = self.make_repo()
        (repo / ".gitignore").write_text(".env.local\n", encoding="utf-8")
        (repo / ".worktreeinclude").write_text(".env.local\n", encoding="utf-8")
        (repo / ".env.local").write_text("LOCAL_ONLY=1\n", encoding="utf-8")
        target = self.returned_path(self.run_hook("keep-edits", repo))
        (target / ".env.local").write_text("EDITED_IN_WORKTREE=1\n", encoding="utf-8")

        again = self.run_hook("keep-edits", repo)

        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(self.returned_path(again).resolve(), target.resolve())
        self.assertEqual((target / ".env.local").read_text(encoding="utf-8"), "EDITED_IN_WORKTREE=1\n")

    def test_new_worktree_gets_current_scope_manifest_over_tracked_base_copy(self):
        repo, _, _ = self.make_repo()
        (repo / ".vibeos").mkdir()
        (repo / ".vibeos/config.json").write_text("{}\n", encoding="utf-8")
        (repo / ".vibeos/worktree-scopes.json").write_text('{"version": "base"}\n', encoding="utf-8")
        self.git(repo, "add", ".vibeos/worktree-scopes.json")
        self.git(repo, "commit", "-q", "-m", "tracked base copy of the scope manifest")
        (repo / ".vibeos/worktree-scopes.json").write_text('{"version": "current"}\n', encoding="utf-8")

        target = self.returned_path(self.run_hook("fresh-scopes", repo))

        self.assertEqual(
            (target / ".vibeos/worktree-scopes.json").read_text(encoding="utf-8"), '{"version": "current"}\n'
        )

    def test_symlinked_worktrees_directory_is_refused(self):
        repo, _, _ = self.make_repo()
        outside = self.base / "outside"
        outside.mkdir()
        (repo / ".claude").mkdir()
        (repo / ".claude/worktrees").symlink_to(outside)

        self.assert_refused(self.run_hook("escape-attempt", repo))
        self.assertEqual(list(outside.iterdir()), [], "nothing may be created outside the repository")

    def test_symlinked_claude_directory_is_refused(self):
        repo, _, _ = self.make_repo()
        outside = self.base / "outside-claude"
        outside.mkdir()
        (repo / ".claude").symlink_to(outside)

        self.assert_refused(self.run_hook("escape-attempt", repo))
        self.assertEqual(list(outside.iterdir()), [], "nothing may be created outside the repository")

    def test_worktreeinclude_copies_gitignored_files_in_any_repository(self):
        repo, _, _ = self.make_repo()
        (repo / ".gitignore").write_text(".env.local\n", encoding="utf-8")
        (repo / ".worktreeinclude").write_text(".env.local\n", encoding="utf-8")
        (repo / ".env.local").write_text("LOCAL_ONLY=1\n", encoding="utf-8")

        result = self.run_hook("with-include", repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (self.returned_path(result) / ".env.local").read_text(encoding="utf-8"), "LOCAL_ONLY=1\n"
        )

    def test_vibeos_scope_manifest_still_copied_in_vibeos_project(self):
        repo, _, _ = self.make_repo()
        (repo / ".vibeos").mkdir()
        (repo / ".vibeos/config.json").write_text("{}\n", encoding="utf-8")
        (repo / ".vibeos/worktree-scopes.json").write_text(
            json.dumps({"branches": {}, "shared_paths": []}) + "\n", encoding="utf-8"
        )

        result = self.run_hook("vibeos-lane", repo)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.returned_path(result) / ".vibeos/worktree-scopes.json").is_file())


if __name__ == "__main__":
    unittest.main()
