#!/usr/bin/env bash
# VibeOS Plugin — Dependency Version Validation Gate
# Checks app-oriented dependency pinning, lockfile policy, and latest-version awareness.
#
# Usage:
#   bash scripts/validate-dependency-versions.sh
#
# Environment:
#   LANGUAGE           — python|typescript|javascript|go|rust|java (default: auto-detect)
#   PROJECT_ROOT       — target project root (default: script parent)
#   PACKAGE_FILE       — path to package manifest (default: auto-detect)
#   PROJECT_ROLE       — application|library (default: application)
#   PACKAGE_MANAGER    — npm|pnpm|yarn|bun|pip|poetry|pdm|uv (default: auto-detect where supported)
#   ONLINE_LOOKUP      — true|false (default: true)
#   MAX_LATEST_LOOKUPS — max packages to query for latest versions (default: 5)
#
# Exit codes:
#   0 = Dependency policy passed (or checks not available)
#   1 = Dependency policy violations found
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.1.0"
GATE_NAME="validate-dependency-versions"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-dependency-versions.sh

Environment:
  LANGUAGE           python|typescript|javascript|go|rust|java (default: auto-detect)
  PROJECT_ROOT       Target project root (default: script parent)
  PACKAGE_FILE       Path to package manifest (default: auto-detect)
  PROJECT_ROLE       application|library (default: application)
  PACKAGE_MANAGER    npm|pnpm|yarn|bun|pip|poetry|pdm|uv (default: auto-detect where supported)
  ONLINE_LOOKUP      true|false (default: true)
  MAX_LATEST_LOOKUPS Max packages to query for latest versions (default: 5)

Checks:
  - App-oriented pinning policy (floating versions fail by default)
  - Lockfile expectations for supported ecosystems
  - Latest stable version awareness (best-effort, non-blocking)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Dependency Version Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

repo_root="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# Auto-detect language
detect_language() {
  if [[ -f "$repo_root/pyproject.toml" ]] || [[ -f "$repo_root/setup.py" ]] || [[ -f "$repo_root/requirements.txt" ]]; then
    echo "python"
  elif [[ -f "$repo_root/tsconfig.json" ]]; then
    echo "typescript"
  elif [[ -f "$repo_root/package.json" ]]; then
    echo "javascript"
  elif [[ -f "$repo_root/go.mod" ]]; then
    echo "go"
  elif [[ -f "$repo_root/Cargo.toml" ]]; then
    echo "rust"
  elif [[ -f "$repo_root/pom.xml" ]] || [[ -f "$repo_root/build.gradle" ]]; then
    echo "java"
  else
    echo "unknown"
  fi
}

LANGUAGE="${LANGUAGE:-$(detect_language)}"
PROJECT_ROLE="${PROJECT_ROLE:-application}"
PACKAGE_MANAGER="${PACKAGE_MANAGER:-}"
ONLINE_LOOKUP="${ONLINE_LOOKUP:-true}"
MAX_LATEST_LOOKUPS="${MAX_LATEST_LOOKUPS:-5}"
echo "Language: $LANGUAGE"
echo "Project role: $PROJECT_ROLE"

if [[ "$PROJECT_ROLE" != "application" && "$PROJECT_ROLE" != "library" ]]; then
  echo "[$GATE_NAME] FAIL: PROJECT_ROLE must be 'application' or 'library'"
  exit 2
fi

if ! [[ "$MAX_LATEST_LOOKUPS" =~ ^[0-9]+$ ]]; then
  echo "[$GATE_NAME] FAIL: MAX_LATEST_LOOKUPS must be an integer"
  exit 2
fi

case "$LANGUAGE" in
  python)
    if [[ -z "${PACKAGE_FILE:-}" ]]; then
      if [[ -f "$repo_root/requirements.txt" ]]; then
        PACKAGE_FILE="$repo_root/requirements.txt"
      elif [[ -f "$repo_root/pyproject.toml" ]]; then
        PACKAGE_FILE="$repo_root/pyproject.toml"
      else
        PACKAGE_FILE=""
      fi
    fi
    ;;
  typescript|javascript)
    PACKAGE_FILE="${PACKAGE_FILE:-$repo_root/package.json}"
    ;;
esac

analysis_output="$(python3 - "$LANGUAGE" "$repo_root" "${PACKAGE_FILE:-}" "$PROJECT_ROLE" "$PACKAGE_MANAGER" "$ONLINE_LOOKUP" "$MAX_LATEST_LOOKUPS" <<'PYEOF'
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

language, repo_root, package_file, project_role, package_manager, online_lookup_raw, max_latest_lookup_raw = sys.argv[1:]
repo_root = Path(repo_root)
package_path = Path(package_file) if package_file else None
if package_path and not package_path.is_absolute():
    package_path = repo_root / package_path

online_lookup = online_lookup_raw.lower() != "false"
max_latest_lookups = int(max_latest_lookup_raw)
messages: list[tuple[str, str]] = []


def emit(level: str, message: str) -> None:
    messages.append((level, message))


def normalize_name(name: str) -> str:
    return name.split("[", 1)[0].strip()


def normalize_version(version: str) -> str:
    return version.strip().lstrip("v")


def js_is_exact(spec: str) -> bool:
    return bool(re.fullmatch(r"v?\d+\.\d+\.\d+(?:[-+][A-Za-z0-9._-]+)?", spec.strip()))


def js_is_floating(spec: str) -> bool:
    spec = spec.strip()
    if not spec:
        return True
    if spec in {"*", "latest", "next"}:
        return True
    if spec.startswith(("^", "~", ">", "<", "=", "workspace:", "file:", "link:", "github:", "git+", "git:", "http:", "https:", "npm:")):
        return True
    if "||" in spec:
        return True
    if re.search(r"(^|[.\s])(?:x|X|\*)(?:$|[.\s])", spec):
        return True
    return not js_is_exact(spec)


def py_requirement_is_exact(spec: str) -> bool:
    spec = spec.strip()
    return bool(re.fullmatch(r"===?[^,;]+", spec))


def py_is_floating(spec: str) -> bool:
    spec = spec.strip()
    if not spec:
        return True
    if spec.startswith("@"):
        return True
    if py_requirement_is_exact(spec):
        return False
    if any(op in spec for op in ("~=", ">=", "<=", "!=", ">", "<")):
        return True
    return True


def detect_js_package_manager(package_json: dict) -> str:
    if package_manager:
        return package_manager
    pm_field = package_json.get("packageManager", "")
    if isinstance(pm_field, str) and "@" in pm_field:
        return pm_field.split("@", 1)[0]
    if (repo_root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (repo_root / "yarn.lock").exists():
        return "yarn"
    if (repo_root / "bun.lockb").exists() or (repo_root / "bun.lock").exists():
        return "bun"
    return "npm"


def python_lockfile_status(manifest_path: Path) -> tuple[bool, str]:
    if package_manager in {"poetry", "pdm", "uv"}:
        expected = {"poetry": "poetry.lock", "pdm": "pdm.lock", "uv": "uv.lock"}[package_manager]
        return ((repo_root / expected).exists(), expected)

    if manifest_path.name == "requirements.txt":
        return True, "requirements.txt"

    if manifest_path.name == "pyproject.toml":
        for candidate in ("poetry.lock", "pdm.lock", "uv.lock", "requirements.txt", "requirements.lock", "pylock.toml"):
            if (repo_root / candidate).exists():
                return True, candidate
        return False, "poetry.lock, pdm.lock, uv.lock, requirements.txt, requirements.lock, or pylock.toml"

    return False, "known Python lockfile"


def fetch_json(url: str):
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


def fetch_latest_js(name: str):
    encoded = urllib.parse.quote(name, safe="@/")
    payload = fetch_json(f"https://registry.npmjs.org/{encoded}/latest")
    if isinstance(payload, dict):
        return payload.get("version")
    return None


def fetch_latest_python(name: str):
    encoded = urllib.parse.quote(name.replace("_", "-"))
    payload = fetch_json(f"https://pypi.org/pypi/{encoded}/json")
    if isinstance(payload, dict):
        info = payload.get("info", {})
        if isinstance(info, dict):
            return info.get("version")
    return None


if language in {"typescript", "javascript"}:
    if not package_path or not package_path.exists():
        emit("WARN", "package.json not found")
        emit("SKIP", "Set PACKAGE_FILE to enable JS/TS dependency version checks")
    else:
        with package_path.open() as handle:
            package_json = json.load(handle)

        detected_pm = detect_js_package_manager(package_json)
        emit("INFO", f"Using package manager policy: {detected_pm}")

        lockfile_map = {
            "npm": "package-lock.json",
            "pnpm": "pnpm-lock.yaml",
            "yarn": "yarn.lock",
            "bun": "bun.lockb|bun.lock",
        }
        lockfile_ok = False
        lockfile_desc = lockfile_map.get(detected_pm, "package-lock.json|pnpm-lock.yaml|yarn.lock|bun.lockb|bun.lock")
        if detected_pm == "bun":
            lockfile_ok = (repo_root / "bun.lockb").exists() or (repo_root / "bun.lock").exists()
        else:
            lockfile_ok = (repo_root / lockfile_map.get(detected_pm, "package-lock.json")).exists()

        if lockfile_ok:
            emit("PASS", f"Lockfile present for {detected_pm}")
        else:
            level = "ERROR" if project_role == "application" else "WARN"
            emit(level, f"Expected lockfile for {detected_pm} app policy: {lockfile_desc}")

        exact_deps = []
        floating_count = 0
        total_deps = 0
        for section in ("dependencies", "devDependencies"):
            deps = package_json.get(section, {})
            if not isinstance(deps, dict):
                continue
            for name, spec in deps.items():
                total_deps += 1
                if not isinstance(spec, str):
                    continue
                if js_is_floating(spec):
                    level = "ERROR" if project_role == "application" else "WARN"
                    emit(level, f"{section}:{name} uses floating specifier '{spec}'")
                    floating_count += 1
                else:
                    exact_deps.append((name, normalize_version(spec), section))

        if total_deps == 0:
            emit("WARN", "No dependencies found in package.json")
        elif floating_count == 0:
            emit("PASS", "JS/TS dependency declarations are pinned under the current policy")

        latest_hits = 0
        latest_misses = 0
        if online_lookup and exact_deps:
            for name, current, section in exact_deps[:max_latest_lookups]:
                latest = fetch_latest_js(name)
                if latest:
                    latest_hits += 1
                    latest = normalize_version(latest)
                    if current != latest:
                        emit("WARN", f"{section}:{name} pinned to {current}; latest stable is {latest}")
                else:
                    latest_misses += 1
        elif not online_lookup:
            emit("INFO", "Latest-version lookup disabled (ONLINE_LOOKUP=false)")

        if online_lookup and exact_deps and latest_hits == 0:
            emit("INFO", "Latest-version lookup unavailable for JS/TS dependencies; pinning and lockfile policy still checked")

elif language == "python":
    if not package_path or not package_path.exists():
        emit("WARN", "No Python dependency manifest found")
        emit("SKIP", "Set PACKAGE_FILE to requirements.txt or pyproject.toml to enable Python dependency version checks")
    else:
        emit("INFO", f"Using Python manifest: {package_path.name}")

        lockfile_ok, lockfile_desc = python_lockfile_status(package_path)
        if lockfile_ok:
            emit("PASS", f"Python lockfile/pin source present: {lockfile_desc}")
        else:
            level = "ERROR" if project_role == "application" else "WARN"
            emit(level, f"Expected Python lockfile or pinned export for app policy: {lockfile_desc}")

        exact_deps = []
        counters = {"floating": 0, "total": 0}

        def check_dep(name: str, spec: str, source: str):
            counters["total"] += 1
            clean_name = normalize_name(name)
            if py_is_floating(spec):
                level = "ERROR" if project_role == "application" else "WARN"
                emit(level, f"{source}:{clean_name} uses floating specifier '{spec or '(none)'}'")
                counters["floating"] += 1
            else:
                version = spec.split("=", 1)[-1].strip()
                exact_deps.append((clean_name, normalize_version(version), source))

        if package_path.name == "requirements.txt":
            for raw_line in package_path.read_text().splitlines():
                line = raw_line.split("#", 1)[0].strip()
                if not line or line.startswith(("-", "--")):
                    continue
                if line.startswith(("-e ", ".")):
                    level = "ERROR" if project_role == "application" else "WARN"
                    emit(level, f"requirements.txt entry uses editable/local reference '{line}'")
                    counters["floating"] += 1
                    counters["total"] += 1
                    continue
                if "@" in line and "://" in line:
                    name = line.split("@", 1)[0].strip()
                    check_dep(name, "@", "requirements.txt")
                    continue
                match = re.match(r"^\s*([A-Za-z0-9_.-]+(?:\[[^]]+\])?)\s*(.*)$", line)
                if not match:
                    continue
                name, spec = match.groups()
                check_dep(name, spec.strip(), "requirements.txt")
        else:
            pyproject_text = package_path.read_text()
            data = {}
            try:
                import tomllib  # type: ignore[attr-defined]
                data = tomllib.loads(pyproject_text)
            except ModuleNotFoundError:
                data = {}

            if data:
                project = data.get("project", {})
                for dep in project.get("dependencies", []) or []:
                    match = re.match(r"^\s*([A-Za-z0-9_.-]+(?:\[[^]]+\])?)\s*(.*)$", dep)
                    if match:
                        name, spec = match.groups()
                        check_dep(name, spec.strip(), "project.dependencies")

                poetry_deps = (((data.get("tool") or {}).get("poetry") or {}).get("dependencies") or {})
                if isinstance(poetry_deps, dict):
                    for name, spec in poetry_deps.items():
                        if name == "python":
                            continue
                        if isinstance(spec, str):
                            check_dep(name, spec.strip(), "tool.poetry.dependencies")
                        elif isinstance(spec, dict):
                            version = str(spec.get("version", "")).strip()
                            if version:
                                check_dep(name, version, "tool.poetry.dependencies")
            else:
                dep_lines = re.findall(r'^\s*"([^"]+)"\s*,?\s*$', pyproject_text, flags=re.MULTILINE)
                for dep in dep_lines:
                    match = re.match(r"^\s*([A-Za-z0-9_.-]+(?:\[[^]]+\])?)\s*(.*)$", dep)
                    if match:
                        name, spec = match.groups()
                        check_dep(name, spec.strip(), "pyproject.toml")

        if counters["total"] == 0:
            emit("WARN", f"No dependencies found in {package_path.name}")
        elif counters["floating"] == 0:
            emit("PASS", "Python dependency declarations are pinned under the current policy")

        latest_hits = 0
        if online_lookup and exact_deps:
            for name, current, source in exact_deps[:max_latest_lookups]:
                latest = fetch_latest_python(name)
                if latest:
                    latest_hits += 1
                    latest = normalize_version(latest)
                    if current != latest:
                        emit("WARN", f"{source}:{name} pinned to {current}; latest stable is {latest}")
        elif not online_lookup:
            emit("INFO", "Latest-version lookup disabled (ONLINE_LOOKUP=false)")

        if online_lookup and exact_deps and latest_hits == 0:
            emit("INFO", "Latest-version lookup unavailable for Python dependencies; pinning and lockfile policy still checked")

else:
    emit("WARN", f"Version checking MVP is not implemented for language '{language}'")
    emit("SKIP", "Supported in MVP: javascript, typescript, python")

for level, message in messages:
    print(f"{level}:{message}")
PYEOF
)"

printf '%s\n' "$analysis_output"

error_count=$(printf '%s\n' "$analysis_output" | awk -F: '/^ERROR:/{c++} END{print c+0}')
warning_count=$(printf '%s\n' "$analysis_output" | awk -F: '/^WARN:/{c++} END{print c+0}')

echo ""
if [[ "$error_count" -gt 0 ]]; then
  echo "[$GATE_NAME] FAIL: $error_count policy violation(s), $warning_count warning(s)"
  exit 1
elif [[ "$warning_count" -gt 0 ]]; then
  echo "[$GATE_NAME] PASS (with $warning_count warning(s))"
  exit 0
else
  echo "[$GATE_NAME] PASS: Dependency version validation complete"
  exit 0
fi
