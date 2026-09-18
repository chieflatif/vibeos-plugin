#!/usr/bin/env python3
"""Run one gate command with a portable process-group timeout."""

import math
import os
import signal
import subprocess
import sys


TIMEOUT_EXIT = 124
TERM_GRACE_SECONDS = 2
FRAMEWORK_VERSION = "2.3.2"
TIMEOUT_MARKER = "__VIBEOS_GATE_TIMEOUT__"


def usage() -> None:
    sys.stderr.write("usage: gate_timeout.py SECONDS -- COMMAND [ARG ...]\n")


def send_group_signal(process: subprocess.Popen, signum: int) -> None:
    try:
        os.killpg(process.pid, signum)
    except ProcessLookupError:
        return


def emit_output(output: bytes) -> None:
    if output:
        sys.stdout.buffer.write(output)
        sys.stdout.buffer.flush()


def main(argv):
    if len(argv) < 4 or argv[2] != "--":
        usage()
        return 2
    try:
        timeout = float(argv[1])
    except ValueError:
        sys.stderr.write("gate_timeout.py: seconds must be a positive number\n")
        return 2
    if not math.isfinite(timeout) or timeout <= 0:
        sys.stderr.write("gate_timeout.py: seconds must be a positive number\n")
        return 2

    try:
        process = subprocess.Popen(
            argv[3:],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    except OSError as exc:
        sys.stderr.write(f"gate_timeout.py: cannot start command: {exc}\n")
        return 2

    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        send_group_signal(process, signal.SIGTERM)
        try:
            output, _ = process.communicate(timeout=TERM_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            send_group_signal(process, signal.SIGKILL)
            output, _ = process.communicate()
        emit_output(output)
        sys.stderr.write(f"{TIMEOUT_MARKER}\n")
        return TIMEOUT_EXIT

    emit_output(output)
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
