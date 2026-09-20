# Local Engineering Intake and Triage

The `local-engineering-intake` profile module moves one narrow class of routine
engineering work off the frontier-model loop: turning CI, test, lint, build,
dependency, static-analysis, and release-receipt artifacts into a small,
machine-validated triage record.

It is disabled by default. It does not make a local model an implementer, test
author, planner, auditor, or acceptance authority.

## Where It Fits

Use this lane only after a deterministic parser has been considered. It is useful when
the input is repetitive but still needs semantic classification, for example grouping
several test failures around one root symptom or extracting the next inspection target
from a noisy build log.

The intended flow is:

```text
bounded artifact
  -> deterministic request validation
  -> loopback-only local model
  -> closed JSON and evidence validation
  -> advisory intake result
  -> parent runtime decides and acts
```

The local worker never receives tools. It cannot read project files from a request,
write source, run a command, use Git, deploy, approve work, or call a cloud fallback.

## Enable It

Add both the module and its explicit enable flag to the project profile used by the
profile installer:

```json
{
  "mode": "product-engineering",
  "enabled_modules": ["local-engineering-intake"],
  "local_engineering_intake": {
    "enabled": true,
    "base_url": "http://127.0.0.1:1234/v1",
    "model": "gpt-oss-120b",
    "timeout_seconds": 120,
    "max_input_chars": 60000,
    "max_output_tokens": 4096,
    "reasoning_effort": "low",
    "temperature": 1.0,
    "allowed_task_types": [
      "build-log-triage",
      "ci-log-triage",
      "dependency-finding-triage",
      "lint-finding-triage",
      "release-receipt-triage",
      "static-analysis-triage",
      "test-failure-triage"
    ]
  }
}
```

The installer fills the values shown above when the configuration contains only
`{"enabled": true}`. It rejects remote hosts, embedded credentials, unknown fields,
and a configuration whose module and enable flag do not agree. An API key, if a local
server requires one, may be supplied at runtime through
`VIBEOS_LOCAL_INTAKE_API_KEY`; it is never stored in the project profile.

Analyze, inspect, and apply the profile through the normal profile-driven installation
flow. Existing projects that do not opt in receive neither the CLI nor its skill.

## Operate It

First verify that the configured loopback endpoint is reachable and the exact model is
listed:

```bash
python3 .vibeos/scripts/local-engineering-intake.py probe --project-dir .
```

Inspect the closed result contract at any time:

```bash
python3 .vibeos/scripts/local-engineering-intake.py schema
```

`run` accepts one request on standard input. It deliberately does not accept a file
path, so the parent chooses and bounds the content before delegation:

```json
{
  "schema_version": 1,
  "task_type": "test-failure-triage",
  "objective": "Classify the failure and identify the next inspection step.",
  "artifact": "FAILED tests/test_math.py::test_add\nE assert 3 == 4",
  "context": {
    "command": "pytest",
    "exit_code": 1
  }
}
```

Pipe that JSON to:

```bash
python3 .vibeos/scripts/local-engineering-intake.py run --project-dir .
```

An accepted receipt contains the validated result, local-model identifier, attempt
count, duration, token counts when supplied by the server, and the fixed authority
label `advisory_intake_only`. Evidence and error quotes must occur verbatim in the
artifact. High-uncertainty output must request escalation.

The CLI makes at most two local attempts. An unavailable model, provider error,
truncated answer, invalid JSON, schema violation, ungrounded quote, or second failed
attempt returns exit code `3` and a `fallback_required` receipt. The current parent
runtime then decides whether to handle the task itself, use a cloud worker, or stop.
There is no hidden automatic cloud spend.

## Safety Boundaries

- Only loopback-resolving HTTP or HTTPS endpoints are allowed. Proxy use and redirects
  are disabled so a local endpoint cannot silently send the request elsewhere.
- The input is fenced as untrusted data. Common prompt-injection markers fail before a
  network call rather than being handed to the configured model.
- Requests are limited to the configured task types and size. Context is scalar and
  bounded; nested objects are rejected, and path-looking strings are never opened.
- Output is exact JSON with no extra fields. Claims without artifact-grounded quotes do
  not pass validation.
- The worker has no action tools. Accepted intake is evidence for the parent to review,
  not permission to modify the project or mark anything complete.
- Project privacy and client boundaries still apply. Local transport is not permission
  to delegate material the current task was not authorized to inspect.

## Research Basis

The design reuses LM Studio's documented OpenAI-compatible `GET /v1/models` and
`POST /v1/chat/completions` endpoints rather than adding a model server. OpenAI
documents gpt-oss-120b as its strongest open-weight model, with configurable reasoning
and structured-output support. Those capabilities justify testing it as a structured
worker; they do not justify giving it engineering authority.

- [OpenAI gpt-oss-120b model documentation](https://developers.openai.com/api/docs/models/gpt-oss-120b)
- [LM Studio OpenAI-compatible endpoints](https://lmstudio.ai/docs/developer/openai-compat)

Matched project testing found the frontier coding worker materially faster and more
reliable for code changes, while the local model was adequate for the closed triage
fixture after one permitted retry. That is why this module handles intake only and
returns all decisions and effects to the parent.
