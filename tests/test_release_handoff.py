"""Executable regressions for the external Claude release audit."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SOURCE = Path(os.environ.get('VIBEOS_HANDOFF_SOURCE', Path(__file__).resolve().parents[1]))


class ReleaseHandoffTests(unittest.TestCase):
    def run_cmd(self, args, cwd, **kwargs):
        return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=45, **kwargs)

    def install(self, target, modules=None):
        self.run_cmd(['git', 'init', '-q'], target).check_returncode()
        (target / 'README.md').write_text('# Release handoff fixture\n')
        profile = target / 'vibeos-profile.json'
        profile.write_text(json.dumps({'project_name': 'Release handoff fixture',
            'mode': 'product-engineering', 'lead_runtime': 'codex',
            'canon_paths': ['README.md'], 'protected_files': ['README.md'],
            'enabled_modules': modules or []}))
        plan = target / '.vibeos/install-plan.json'
        for args in [
            ['analyze', '--source', str(SOURCE), '--target', str(target), '--profile', str(profile)],
            ['apply', '--plan', str(plan)],
        ]:
            result = self.run_cmd([str(SOURCE / 'vibeos'), *args], SOURCE)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return plan

    def test_documented_default_hook_step_keeps_audit_verify_and_commit_working(self):
        with tempfile.TemporaryDirectory(prefix='vibeos handoff ') as tmp:
            target = Path(tmp).resolve()
            plan = self.install(target)
            # An unrelated commit-msg hook must be left untouched by default.
            foreign = target / '.git/hooks/commit-msg'
            foreign.write_text('#!/bin/sh\n# user-owned hook\nexit 0\n')
            foreign.chmod(0o755)
            before = foreign.read_bytes()
            setup = self.run_cmd(['bash', '.vibeos/scripts/setup-git-hooks.sh', '--project-dir', '.'], target)
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
            self.assertEqual(foreign.read_bytes(), before)
            for args in [
                ['python3', '.vibeos/scripts/vibeos-active-surface-audit.py'],
                [str(SOURCE / 'vibeos'), 'verify', '--plan', str(plan)],
                ['git', 'add', 'README.md'],
                ['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'feat: prove default hook handoff'],
            ]:
                result = self.run_cmd(args, target)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_default_hook_setup_does_not_add_unrequested_commit_message_policy(self):
        with tempfile.TemporaryDirectory(prefix='vibeos default hooks ') as tmp:
            target = Path(tmp).resolve()
            plan = self.install(target)
            setup = self.run_cmd(['bash', '.vibeos/scripts/setup-git-hooks.sh', '--project-dir', '.'], target)
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
            self.assertFalse((target / '.git/hooks/commit-msg').exists())
            audit = self.run_cmd(['python3', '.vibeos/scripts/vibeos-active-surface-audit.py'], target)
            self.assertEqual(audit.returncode, 0, audit.stdout + audit.stderr)
            verify = self.run_cmd([str(SOURCE / 'vibeos'), 'verify', '--plan', str(plan)], target)
            self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)

    def test_explicit_commit_message_module_installs_real_validator(self):
        with tempfile.TemporaryDirectory(prefix='vibeos opt-in ') as tmp:
            target = Path(tmp).resolve()
            self.install(target, ['commit-msg-enforcement'])
            self.assertTrue((target / '.vibeos/scripts/validate-commit-msg.sh').is_file())
            setup = self.run_cmd(['bash', '.vibeos/scripts/setup-git-hooks.sh', '--project-dir', '.'], target)
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
            self.assertIn('VibeOS commit-msg validator', (target / '.git/hooks/commit-msg').read_text())
            message = target / '.git/test-message'
            message.write_text('WIP\n')
            rejected = self.run_cmd(['.git/hooks/commit-msg', str(message)], target)
            self.assertNotEqual(rejected.returncode, 0)
            message.write_text('feat: prove opted-in enforcement\n\nCo-Authored-By: Fixture <fixture@example.invalid>\n')
            accepted = self.run_cmd(['.git/hooks/commit-msg', str(message)], target)
            self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
            (target / '.vibeos/scripts/validate-commit-msg.sh').unlink()
            missing = self.run_cmd(['.git/hooks/commit-msg', str(message)], target)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn('validator is missing', missing.stdout + missing.stderr)
            audit = self.run_cmd(['python3', '.vibeos/scripts/vibeos-active-surface-audit.py'], target)
            self.assertEqual(audit.returncode, 0, audit.stdout + audit.stderr)

    def test_legacy_entrypoints_refuse_profile_install_without_any_mutation(self):
        with tempfile.TemporaryDirectory(prefix='vibeos protected ') as tmp:
            target = Path(tmp).resolve()
            (target / '.vibeos').mkdir()
            (target / '.vibeos/install-lock.json').write_text('{"schema_version":2}\n')
            (target / 'AGENTS.md').write_text('User-owned instructions\n')
            def inventory():
                return {str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
                        if p.is_file() else 'directory' for p in target.rglob('*')}
            before = inventory()
            for script in ['vibeos-init.sh', 'vibeos-init-codex.sh']:
                for flags in [[], ['--upgrade'], ['--uninstall'], ['--upgrade', '--force']]:
                    with self.subTest(script=script, flags=flags):
                        result = self.run_cmd(['bash', str(SOURCE / script), '--target', str(target), *flags], SOURCE)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('profile', result.stdout.lower() + result.stderr.lower())
                        self.assertEqual(inventory(), before)

    def test_old_python_wrapper_fails_with_actionable_prerequisite_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / 'python3'
            fake.write_text('#!/bin/sh\nexit 1\n')
            fake.chmod(0o755)
            env = dict(os.environ, PATH=f'{tmp}:/usr/bin:/bin')
            result = self.run_cmd(['bash', str(SOURCE / 'vibeos'), '--help'], SOURCE, env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Python 3.12', result.stdout + result.stderr)
            self.assertNotIn('Traceback', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
