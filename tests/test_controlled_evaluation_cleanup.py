import os
import signal
import subprocess
import sys
import time

from tests.controlled_evaluation_fixtures import ENTRYPOINT, ControlledEvaluationCase

sys.path.insert(0, str(ENTRYPOINT.parent / "controlled_evaluation"))
import checks as controlled_checks  # noqa: E402 - test loads the shipped package


BLOCKING_ADAPTER = r'''import json
import os
from pathlib import Path
import subprocess
import signal
import sys
import time


result = Path(sys.argv[2])
evidence = result / "project-evidence"
evidence.mkdir(parents=True, exist_ok=True)
signal.signal(signal.SIGTERM, signal.SIG_IGN)
child = subprocess.Popen([
    sys.executable,
    "-c",
    "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)",
])
(evidence / "adapter.pid").write_text(str(os.getpid()), encoding="utf-8")
(evidence / "grandchild.pid").write_text(str(child.pid), encoding="utf-8")
time.sleep(60)
(result / "project.json").write_text(json.dumps({
    "schema": "vibeos.project-checks.v1",
    "cases": [],
    "held": [],
    "project_qualified": False,
    "runtime_qualified": False
}), encoding="utf-8")
'''

SPAWN_IGNORING_CHILD = r'''import signal
import subprocess
import sys
import time


child = subprocess.Popen(
    [sys.executable, "-c", "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)"],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
open(sys.argv[1], "w", encoding="utf-8").write(str(child.pid))
if sys.argv[2] == "wait":
    time.sleep(60)
'''


class ControlledEvaluationCleanupTests(ControlledEvaluationCase):
    def install_blocking_adapter(self, timeout=2, slow_owner=False):
        self.adapter.write_text(BLOCKING_ADAPTER, encoding="utf-8")
        if slow_owner:
            self.owner_test.write_text(
                "import time\n\ndef test_candidate_file():\n    time.sleep(0.7)\n\n"
                "def test_candidate_identity():\n    assert True\n",
                encoding="utf-8",
            )
        spec = self.spec_value()
        spec["timeout_seconds"] = timeout
        self.write_spec(spec)
        self.assert_ok(self.prepare())

    def pid_path(self, name):
        return self.owner / "results/checks/run-1/project-evidence" / name

    def wait_for_pid(self, name, timeout=5):
        path = self.pid_path(name)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if path.is_file():
                return int(path.read_text(encoding="utf-8"))
            time.sleep(0.02)
        self.fail(f"process PID was not recorded: {path}")

    def alive(self, pid):
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False

    def assert_terminated(self, *pids):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and any(self.alive(pid) for pid in pids):
            time.sleep(0.02)
        survivors = [pid for pid in pids if self.alive(pid)]
        for pid in survivors:
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.assertEqual(survivors, [], f"evaluation descendants survived: {survivors}")

    def test_total_deadline_terminates_adapter_and_grandchild(self):
        self.install_blocking_adapter(slow_owner=True)

        result = self.evaluate(timeout=10)
        adapter = self.wait_for_pid("adapter.pid")
        grandchild = self.wait_for_pid("grandchild.pid")

        self.assert_failed(result)
        self.assert_terminated(adapter, grandchild)
        self.assertFalse((self.owner / "results/runs/run-1/admitted.json").exists())

    def test_inner_phases_share_one_deadline(self):
        config = {"owner_root": str(self.root)}
        environment = dict(os.environ)
        command = [sys.executable, "-c", "import time; time.sleep(0.65)"]
        deadline = time.monotonic() + 1

        first = controlled_checks.execute(command, config, environment, deadline)
        second = controlled_checks.execute(command, config, environment, deadline)

        self.assertFalse(first["timed_out"])
        self.assertTrue(second["timed_out"])
        self.assertLess(time.monotonic() - deadline, 0.5)

    def execute_child_launcher(self, mode, budget):
        pid_file = self.inputs / f"{mode}-grandchild.pid"
        command = [sys.executable, "-c", SPAWN_IGNORING_CHILD, str(pid_file), mode]
        result = controlled_checks.execute(
            command,
            {"owner_root": str(self.root)},
            dict(os.environ),
            time.monotonic() + budget,
        )
        return result, int(pid_file.read_text(encoding="utf-8"))

    def test_normal_completion_cleans_pipe_closing_grandchild(self):
        result, grandchild = self.execute_child_launcher("exit", 3)

        self.assertEqual(result["exit"], 0)
        self.assertFalse(result["timed_out"])
        self.assert_terminated(grandchild)

    def test_timeout_cleans_grandchild_after_leader_exits_on_term(self):
        result, grandchild = self.execute_child_launcher("wait", 0.5)

        self.assertTrue(result["timed_out"])
        self.assert_terminated(grandchild)

    def test_sigterm_terminates_adapter_and_grandchild(self):
        self.install_blocking_adapter(timeout=10)
        process = subprocess.Popen(
            [
                sys.executable,
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
        adapter = self.wait_for_pid("adapter.pid")
        grandchild = self.wait_for_pid("grandchild.pid")

        process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=10)

        self.assertNotEqual(process.returncode, 0, stdout + stderr)
        self.assert_terminated(adapter, grandchild)
        self.assertFalse((self.owner / "results/runs/run-1/admitted.json").exists())
