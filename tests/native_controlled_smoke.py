"""Manual native Codex proof; no provider calls and no sandbox emulation."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "plugins/vibeos/scripts/controlled-evaluation.py"


def command(argv, cwd=None):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
    return {"argv": [str(item) for item in argv], "exit": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def require(result):
    if result["exit"]:
        raise RuntimeError(json.dumps(result))
    return result


def tool(name):
    value = shutil.which(name)
    if not value:
        raise RuntimeError(f"required native tool unavailable: {name}")
    return str(Path(value).resolve(strict=True))


def candidate(root, language):
    project = root / f"{language} candidate with spaces"
    project.mkdir()
    if language == "python":
        filename = "total.py"
        source = """import sys


def total(values):
    return sum(int(value) for value in values)


if __name__ == '__main__':
    try:
        print(total(sys.argv[1:]))
    except ValueError:
        raise SystemExit(2)
"""
        invocation = [str(Path(sys.executable).resolve()), "-I", "-B", str(project / filename)]
    else:
        filename = "total.js"
        source = """const values = process.argv.slice(2).map(Number);
if (values.some(value => !Number.isInteger(value))) process.exit(2);
console.log(values.reduce((sum, value) => sum + value, 0));
"""
        invocation = [tool("node"), str(project / filename)]
    (project / filename).write_text(source)
    (project / "README.md").write_text(f"# {language} native smoke\n")
    for args in [["init", "-q"], ["add", "."],
                 ["-c", "user.name=VibeOS Test", "-c", "user.email=tests@example.invalid",
                  "commit", "-qm", "native smoke baseline"]]:
        require(command(["git", *args], cwd=project))
    return project, filename, invocation


def inputs(root, language, project, filename, invocation):
    directory = root / f"{language} owner inputs"
    directory.mkdir()
    owner_test = directory / "test_native.py"
    owner_test.write_text("""import json
from pathlib import Path
import subprocess


""" + f"INVOCATION = {invocation!r}\nFILENAME = {filename!r}\n" + """

def test_calculation():
    result = subprocess.run(INVOCATION + ['3', '-2', '8'], capture_output=True, text=True)
    assert result.returncode == 0 and result.stdout.strip() == '9'


def test_candidate_write_denied():
    config = json.loads(Path('protected-owner/config.json').read_text())
    path = Path(config['candidate_root']) / FILENAME
    before = path.read_bytes()
    try:
        with path.open('ab') as stream:
            stream.write(b'forbidden')
    except PermissionError:
        pass
    else:
        raise AssertionError('native sandbox allowed candidate mutation')
    assert path.read_bytes() == before


def test_owner_write_denied():
    path = Path('protected-owner/config.json')
    before = path.read_bytes()
    try:
        with path.open('ab') as stream:
            stream.write(b'forbidden')
    except PermissionError:
        pass
    else:
        raise AssertionError('native sandbox allowed protected-owner mutation')
    assert path.read_bytes() == before
""")
    adapter = directory / "project_checks.py"
    adapter.write_text("""import json
from pathlib import Path
import subprocess
import sys


""" + f"INVOCATION = {invocation!r}\n" + """output = Path(sys.argv[2])
evidence = output / 'project-evidence'
evidence.mkdir()
results = []
for identity, arguments, expected_exit, expected_output in [
    ('calculation', ['4', '5', '-3'], 0, '6'),
    ('invalid-input', ['bad'], 2, ''),
]:
    result = subprocess.run(INVOCATION + arguments, capture_output=True, text=True)
    ok = result.returncode == expected_exit and result.stdout.strip() == expected_output
    (evidence / (identity + '.json')).write_text(json.dumps({
        'argv': INVOCATION + arguments, 'exit': result.returncode,
        'stdout': result.stdout, 'stderr': result.stderr,
    }, sort_keys=True))
    results.append({'id': identity, 'status': 'PASS' if ok else 'FAIL'})
(output / 'project.json').write_text(json.dumps({
    'schema': 'vibeos.project-checks.v1', 'cases': results, 'held': [],
    'project_qualified': False, 'runtime_qualified': False,
}, sort_keys=True))
raise SystemExit(0 if all(row['status'] == 'PASS' for row in results) else 1)
""")
    spec = directory / "spec.json"
    spec.write_text(json.dumps({
        "schema": "vibeos.controlled-evaluation.spec.v1",
        "owner_tests": [str(owner_test)], "project_adapter": str(adapter),
        "required_owner_tests": ["test_calculation", "test_candidate_write_denied", "test_owner_write_denied"],
        "required_project_cases": ["calculation", "invalid-input"],
        "held_project_checks": [], "writable_files": [filename],
        "tools": {"python": str(Path(sys.executable).resolve()), "ruff": tool("ruff"), "codex": tool("codex")},
        "dependencies": sorted(set([invocation[0], str(Path(__file__).resolve())])),
        "timeout_seconds": 30, "max_lines": 300, "max_complexity": 10,
    }, indent=2))
    return spec


def run_one(root, language, install=False):
    project, filename, invocation = candidate(root, language)
    installer_steps = []
    cli = CLI
    if install:
        profile = project / "vibeos-profile.json"
        profile.write_text(json.dumps({"project_name": language + " native proof",
            "mode": "product-engineering", "lead_runtime": "codex",
            "canon_paths": ["README.md"], "protected_files": ["README.md"]}))
        plan = project / ".vibeos/install-plan.json"
        for arguments in [
            ["analyze", "--source", str(ROOT), "--target", str(project), "--profile", str(profile)],
            ["verify", "--plan", str(plan)], ["apply", "--plan", str(plan)],
            ["verify", "--plan", str(plan)],
        ]:
            installer_steps.append(require(command([str(ROOT / "vibeos"), *arguments])))
        cli = project / ".vibeos/scripts/controlled-evaluation.py"
        require(command([sys.executable, str(cli), "--help"]))
    spec = inputs(root, language, project, filename, invocation)
    owner = root / f"{language} protected owner"
    before = (project / filename).read_bytes()
    steps = []
    for arguments in [
        ["prepare", "--owner", str(owner), "--candidate", str(project), "--spec", str(spec)],
        ["evaluate", "--owner", str(owner), "--run", "run-1"],
        ["publish", "--owner", str(owner), "--run", "run-1"],
        ["publish", "--owner", str(owner), "--run", "run-1"],
    ]:
        result = command([sys.executable, "-B", str(cli), *arguments])
        steps.append(result)
        if result["exit"]:
            break
    unchanged = before == (project / filename).read_bytes()
    publication = owner / "results/published/run-1.json"
    return {"language": language, "owner": str(owner), "candidate": str(project),
            "steps": steps, "installer_steps": installer_steps, "candidate_unchanged": unchanged,
            "publication": json.loads(publication.read_text()) if publication.is_file() else None,
            "passed": len(steps) == 4 and all(row["exit"] == 0 for row in steps) and unchanged}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root")
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()
    root = Path(args.root or tempfile.mkdtemp(prefix="vibeos-native-release-")).resolve()
    root.mkdir(exist_ok=True)
    results = [run_one(root, language, args.install) for language in ["python", "javascript"]]
    payload = {"native_codex": True, "provider_calls": False, "root": str(root),
               "results": results, "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (root / "proof.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    return 0 if all(row["passed"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
