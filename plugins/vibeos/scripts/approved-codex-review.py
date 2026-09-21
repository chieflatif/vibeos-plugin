#!/usr/bin/env python3
"""Approved same-model Codex review transport.

This module validates a narrow operator record and a prior operational Claude
failure, then runs a new ephemeral ``codex exec`` review in an empty directory.
It provides integrity evidence for a same-user workflow; it does not authenticate
the approver or prove the provider-observed model or provider identity.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
APPROVAL_TYPE = "vibeos.approved-same-model-codex-review"
FAILURE_TYPE = "vibeos.claude-operational-failure"
BUNDLE_TYPE = "vibeos.approved-codex-review-evidence"
APPROVAL_AUTHENTICITY = "operator_record_not_cryptographically_verified"
MAX_EVENT_BYTES = 4_000_000

BINDING_KEYS = set(
    "work_order mode candidate_commit candidate_tree prompt_sha256 implementer_model_requested".split()
)
FAILURE_KEYS = set(
    "schema_version receipt_type failure_id created_at stage reason_code binding".split()
)
APPROVAL_KEYS = set(
    "schema_version receipt_type approval_id recorded_at recorded_approver source_ref authenticity decision binding claude_failure_id claude_failure_sha256".split()
)
ELIGIBLE_FAILURE_REASONS = set(
    "claude_cli_not_found claude_cli_not_file claude_auth_status_unavailable claude_not_authenticated claude_auth_provider_mismatch claude_version_unavailable claude_cli_version_too_old claude_help_unavailable claude_required_flags_missing claude_max_turns_probe_unavailable claude_max_turns_flag_unsupported claude_max_turns_probe_inconclusive claude_audit_timed_out claude_audit_unavailable claude_audit_failed".split()
)
ALLOWED_ITEM_TYPES = {"agent_message", "reasoning"}

class ReviewError(RuntimeError):
    """Approval, transport, or evidence is invalid."""

def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()

def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def _exact_keys(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ReviewError(f"{label}_keys_invalid")
    return value

def _validate_binding(value: Any) -> dict[str, str]:
    binding = _exact_keys(value, BINDING_KEYS, "binding")
    if binding["mode"] not in {"full", "verification"}:
        raise ReviewError("binding_mode_invalid")
    if not re.fullmatch(r"WO-[0-9]+", binding["work_order"]):
        raise ReviewError("binding_work_order_invalid")
    for key in ("candidate_commit", "candidate_tree"):
        if not isinstance(binding[key], str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", binding[key]):
            raise ReviewError(f"binding_{key}_invalid")
    if not isinstance(binding["prompt_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", binding["prompt_sha256"]):
        raise ReviewError("binding_prompt_sha256_invalid")
    model = binding["implementer_model_requested"]
    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", model):
        raise ReviewError("binding_implementer_model_invalid")
    return dict(binding)

def validate_approval(
    approval: dict[str, Any], failure: dict[str, Any], binding: dict[str, Any]
) -> dict[str, Any]:
    """Validate exact fallback scope; this does not authenticate the approver."""
    expected = _validate_binding(binding)
    stored_failure = _exact_keys(failure, FAILURE_KEYS, "failure")
    if stored_failure["schema_version"] != SCHEMA_VERSION or stored_failure["receipt_type"] != FAILURE_TYPE:
        raise ReviewError("failure_identity_invalid")
    if stored_failure["stage"] != "claude_operational" or stored_failure["reason_code"] not in ELIGIBLE_FAILURE_REASONS:
        raise ReviewError("failure_not_fallback_eligible")
    if not isinstance(stored_failure["failure_id"], str) or not stored_failure["failure_id"]:
        raise ReviewError("failure_id_invalid")
    if not isinstance(stored_failure["created_at"], str) or not stored_failure["created_at"]:
        raise ReviewError("failure_created_at_invalid")
    if _validate_binding(stored_failure["binding"]) != expected:
        raise ReviewError("failure_binding_mismatch")
    failure_sha = _sha256(_canonical(stored_failure))

    stored_approval = _exact_keys(approval, APPROVAL_KEYS, "approval")
    if stored_approval["schema_version"] != SCHEMA_VERSION or stored_approval["receipt_type"] != APPROVAL_TYPE:
        raise ReviewError("approval_identity_invalid")
    if stored_approval["decision"] != "approve_same_model_fallback":
        raise ReviewError("approval_decision_invalid")
    if stored_approval["recorded_approver"] != "Latif" or stored_approval["authenticity"] != APPROVAL_AUTHENTICITY:
        raise ReviewError("approval_record_invalid")
    for key in ("approval_id", "recorded_at", "source_ref"):
        if not isinstance(stored_approval[key], str) or not stored_approval[key]:
            raise ReviewError(f"approval_{key}_invalid")
    if _validate_binding(stored_approval["binding"]) != expected:
        raise ReviewError("approval_binding_mismatch")
    if stored_approval["claude_failure_id"] != stored_failure["failure_id"]:
        raise ReviewError("approval_failure_id_mismatch")
    if stored_approval["claude_failure_sha256"] != failure_sha:
        raise ReviewError("approval_failure_sha256_mismatch")
    return {
        "approval": json.loads(_canonical(stored_approval)),
        "failure": json.loads(_canonical(stored_failure)),
        "binding": json.loads(_canonical(expected)),
        "approval_sha256": _sha256(_canonical(stored_approval)),
        "failure_sha256": failure_sha,
    }

def _child_environment() -> dict[str, str]:
    allowed = {
        "HOME", "USER", "LOGNAME", "PATH", "TMPDIR", "LANG", "CODEX_HOME",
        "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy",
        "no_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS",
    }
    return {key: value for key, value in os.environ.items() if key in allowed or key.startswith("LC_")}

def _resolve_binary(value: str | None) -> Path:
    candidate = value or shutil.which("codex")
    if not candidate:
        raise ReviewError("codex_cli_not_found")
    path = Path(candidate).expanduser().resolve()
    if not path.is_file():
        raise ReviewError("codex_cli_not_file")
    return path

def _validate_events(raw: bytes, final_raw: bytes) -> tuple[dict[str, Any], str]:
    if not raw or len(raw) > MAX_EVENT_BYTES:
        raise ReviewError("codex_event_stream_size_invalid")
    events: list[dict[str, Any]] = []
    try:
        for line in raw.decode("utf-8").splitlines():
            if line.strip():
                event = json.loads(line)
                if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                    raise ReviewError("codex_event_invalid")
                events.append(event)
        final_text = final_raw.decode("utf-8").strip()
        result = json.loads(final_text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewError("codex_output_not_json") from exc
    if not isinstance(result, dict):
        raise ReviewError("codex_final_result_must_be_object")

    types = [event["type"] for event in events]
    if types.count("thread.started") != 1 or types.count("turn.started") != 1 or types.count("turn.completed") != 1:
        raise ReviewError("codex_lifecycle_count_invalid")
    if "turn.failed" in types or "error" in types:
        raise ReviewError("codex_lifecycle_failed")
    thread_index = types.index("thread.started")
    start_index = types.index("turn.started")
    complete_index = types.index("turn.completed")
    if not thread_index < start_index < complete_index or complete_index != len(events) - 1:
        raise ReviewError("codex_lifecycle_order_invalid")
    thread_id = events[thread_index].get("thread_id")
    if not isinstance(thread_id, str) or not thread_id:
        raise ReviewError("codex_thread_id_invalid")

    messages: list[str] = []
    for event in events:
        if event["type"].startswith("item."):
            item = event.get("item")
            if not isinstance(item, dict) or item.get("type") not in ALLOWED_ITEM_TYPES:
                raise ReviewError("codex_tool_or_unknown_item_observed")
            if item["type"] == "agent_message" and event["type"] == "item.completed":
                text = item.get("text")
                if not isinstance(text, str):
                    raise ReviewError("codex_agent_message_invalid")
                messages.append(text.strip())
        elif event["type"] not in {"thread.started", "turn.started", "turn.completed"}:
            raise ReviewError("codex_unknown_event_observed")
    if not messages or messages[-1] != final_text:
        raise ReviewError("codex_final_message_mismatch")
    return result, thread_id

def _transport_claims(binding: dict[str, str], thread_id: str) -> dict[str, Any]:
    return {
        "runtime": "codex-cli",
        "session_mode": "ephemeral_new_thread",
        "thread_id": thread_id,
        "empty_temporary_cwd": True,
        "user_config_ignored": True,
        "rules_ignored": False,
        "sandbox_requested": "read-only",
        "reasoning_effort_requested": "high",
        "requested_model": binding["implementer_model_requested"],
        "observed_model": None,
        "observed_provider": None,
        "model_provenance": "cli_argument_requested_not_provider_observed",
        "tool_isolation": "read_only_requested_and_tool_events_rejected_not_tool_free",
    }

def run_review(
    prompt: str,
    schema: dict[str, Any],
    authorization: dict[str, Any],
    *,
    binary: str | None = None,
    timeout: int = 900,
) -> dict[str, Any]:
    """Run one fresh native Codex review and return one persistable evidence bundle."""
    if not isinstance(prompt, str) or _sha256(prompt.encode()) != authorization["binding"]["prompt_sha256"]:
        raise ReviewError("prompt_binding_mismatch")
    if not isinstance(schema, dict):
        raise ReviewError("output_schema_must_be_object")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 30 <= timeout <= 3600:
        raise ReviewError("timeout_invalid")
    codex = _resolve_binary(binary)
    env = _child_environment()
    try:
        version_run = subprocess.run(
            [str(codex), "--version"], capture_output=True, env=env,
            timeout=min(timeout, 30), check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReviewError("codex_version_unavailable") from exc
    if version_run.returncode != 0 or not version_run.stdout.strip():
        raise ReviewError("codex_version_unavailable")
    version = version_run.stdout.decode("utf-8", errors="replace").strip()[:200]

    with tempfile.TemporaryDirectory(prefix="vibeos-approved-codex-review-") as temporary:
        temp = Path(temporary)
        review_cwd = temp / "review-cwd"
        review_cwd.mkdir()
        schema_path = temp / "result-schema.json"
        final_path = temp / "final-message.json"
        schema_path.write_bytes(_canonical(schema))
        command = [
            str(codex), "exec", "-", "--ephemeral", "--ignore-user-config",
            "--skip-git-repo-check", "--cd", str(review_cwd), "--sandbox", "read-only",
            "--model", authorization["binding"]["implementer_model_requested"],
            "--config", 'model_reasoning_effort="high"',
            "--output-schema", str(schema_path), "--json",
            "--output-last-message", str(final_path),
        ]
        try:
            completed = subprocess.run(
                command, input=prompt.encode(), capture_output=True, env=env,
                timeout=timeout, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            reason = "codex_review_timed_out" if isinstance(exc, subprocess.TimeoutExpired) else "codex_review_unavailable"
            raise ReviewError(reason) from exc
        if completed.returncode != 0 or not final_path.is_file():
            raise ReviewError("codex_review_failed")
        final_raw = final_path.read_bytes()
    result, thread_id = _validate_events(completed.stdout, final_raw)
    transport = _transport_claims(authorization["binding"], thread_id)
    transport.update(cli_path=str(codex), cli_sha256=_sha256(codex.read_bytes()), cli_version=version)
    return {
        "schema_version": SCHEMA_VERSION,
        "receipt_type": BUNDLE_TYPE,
        "authorization": {
            key: authorization[key]
            for key in ("approval", "approval_sha256", "failure", "failure_sha256")
        },
        "binding": authorization["binding"],
        "transport": transport,
        "raw_events": completed.stdout.decode("utf-8"),
        "raw_events_sha256": _sha256(completed.stdout),
        "final_message": final_raw.decode("utf-8"),
        "final_message_sha256": _sha256(final_raw),
        "result": result,
    }

def validate_evidence(bundle: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    """Revalidate a persisted bundle and return its structured review result."""
    if not isinstance(bundle, dict) or bundle.get("schema_version") != SCHEMA_VERSION or bundle.get("receipt_type") != BUNDLE_TYPE:
        raise ReviewError("evidence_identity_invalid")
    auth = bundle.get("authorization")
    if not isinstance(auth, dict) or set(auth) != {"approval", "approval_sha256", "failure", "failure_sha256"}:
        raise ReviewError("evidence_authorization_invalid")
    authorization = validate_approval(auth["approval"], auth["failure"], binding)
    if auth["approval_sha256"] != authorization["approval_sha256"] or auth["failure_sha256"] != authorization["failure_sha256"]:
        raise ReviewError("evidence_authorization_hash_mismatch")
    if bundle.get("binding") != authorization["binding"]:
        raise ReviewError("evidence_binding_mismatch")
    raw_events = bundle.get("raw_events")
    final_message = bundle.get("final_message")
    if not isinstance(raw_events, str) or not isinstance(final_message, str):
        raise ReviewError("evidence_raw_output_invalid")
    raw = raw_events.encode()
    final_raw = final_message.encode()
    if bundle.get("raw_events_sha256") != _sha256(raw) or bundle.get("final_message_sha256") != _sha256(final_raw):
        raise ReviewError("evidence_output_hash_mismatch")
    result, thread_id = _validate_events(raw, final_raw)
    transport = bundle.get("transport")
    required_transport = _transport_claims(authorization["binding"], thread_id)
    if not isinstance(transport, dict) or any(transport.get(key) != value for key, value in required_transport.items()):
        raise ReviewError("evidence_transport_invalid")
    if bundle.get("result") != result:
        raise ReviewError("evidence_result_mismatch")
    return result
