import copy
import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "plugins/vibeos/reference/lane-packet.schema.json"
SCHEMA_DOC = REPO_ROOT / "docs/planning/WO-SCHEMA.md"

ACCEPT_PACKET = {
    "wo_number": "WO-114",
    "lane_status": "ACCEPT",
    "gate_results": [
        {
            "phase": "wo_exit",
            "status": "PASS",
            "passed": 8,
            "failed": 0,
            "skipped": 2,
            "command": "bash plugins/vibeos/scripts/gate-runner.sh wo_exit",
        }
    ],
    "defects": [],
    "evidence_bundle_path": "docs/evidence/WO-114/lane-packet.json",
    "lane_branch": "feat/wo-114-lane-packet",
}

DEFER_PACKET = {
    "wo_number": "WO-115",
    "lane_status": "DEFER",
    "gate_results": [
        {
            "phase": "wo_exit",
            "status": "FAIL",
            "passed": 7,
            "failed": 1,
            "skipped": 2,
            "summary_path": "docs/evidence/WO-115/gate-summary.json",
        }
    ],
    "defects": [
        {
            "severity": "high",
            "source": "scope-diff",
            "message": "Lane changed a file outside the WO write_scope.",
            "path": "src/out-of-scope.py",
        }
    ],
    "evidence_bundle_path": "docs/evidence/WO-115/lane-packet.json",
}


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_packet(packet, schema):
    errors = []
    for field in schema["required"]:
        if field not in packet:
            errors.append(f"missing:{field}")

    if "wo_number" in packet and not re.match(schema["properties"]["wo_number"]["pattern"], packet["wo_number"]):
        errors.append("invalid:wo_number")
    if packet.get("lane_status") not in schema["properties"]["lane_status"]["enum"]:
        errors.append("invalid:lane_status")

    gate_results = packet.get("gate_results")
    if not isinstance(gate_results, list) or not gate_results:
        errors.append("invalid:gate_results")
    else:
        gate_schema = schema["properties"]["gate_results"]["items"]
        for index, gate in enumerate(gate_results):
            for field in gate_schema["required"]:
                if field not in gate:
                    errors.append(f"missing:gate_results[{index}].{field}")
            if gate.get("status") not in gate_schema["properties"]["status"]["enum"]:
                errors.append(f"invalid:gate_results[{index}].status")
            for field in ["passed", "failed", "skipped"]:
                value = gate.get(field)
                if not isinstance(value, int) or value < 0:
                    errors.append(f"invalid:gate_results[{index}].{field}")

    defects = packet.get("defects")
    if not isinstance(defects, list):
        errors.append("invalid:defects")
    else:
        defect_schema = schema["properties"]["defects"]["items"]
        for index, defect in enumerate(defects):
            for field in defect_schema["required"]:
                if field not in defect:
                    errors.append(f"missing:defects[{index}].{field}")
            if defect.get("severity") not in defect_schema["properties"]["severity"]["enum"]:
                errors.append(f"invalid:defects[{index}].severity")

    evidence_path = packet.get("evidence_bundle_path")
    if not isinstance(evidence_path, str) or not evidence_path or re.search(r"(^|/)\\.\\.(?:/|$)", evidence_path):
        errors.append("invalid:evidence_bundle_path")

    return errors


class LanePacketSchemaTests(unittest.TestCase):
    def test_schema_is_parseable_and_requires_joan_u2_fields(self):
        schema = load_schema()

        self.assertEqual(schema["title"], "VibeOS Lane Return Packet")
        for field in ["wo_number", "lane_status", "gate_results", "defects", "evidence_bundle_path"]:
            self.assertIn(field, schema["required"])
            self.assertIn(field, schema["properties"])

    def test_accept_and_defer_fixtures_validate(self):
        schema = load_schema()

        self.assertEqual(validate_packet(ACCEPT_PACKET, schema), [])
        self.assertEqual(validate_packet(DEFER_PACKET, schema), [])

    def test_known_bad_packets_fail_validation(self):
        schema = load_schema()

        missing_evidence = copy.deepcopy(ACCEPT_PACKET)
        missing_evidence.pop("evidence_bundle_path")
        self.assertIn("missing:evidence_bundle_path", validate_packet(missing_evidence, schema))

        invalid_status = copy.deepcopy(ACCEPT_PACKET)
        invalid_status["lane_status"] = "MERGE"
        self.assertIn("invalid:lane_status", validate_packet(invalid_status, schema))

        invalid_gate = copy.deepcopy(ACCEPT_PACKET)
        invalid_gate["gate_results"][0]["failed"] = -1
        self.assertIn("invalid:gate_results[0].failed", validate_packet(invalid_gate, schema))

    def test_defer_packet_requires_defect_shape(self):
        schema = load_schema()
        packet = copy.deepcopy(DEFER_PACKET)
        packet["defects"][0].pop("message")
        packet["defects"][0]["severity"] = "blocker"

        errors = validate_packet(packet, schema)
        self.assertIn("missing:defects[0].message", errors)
        self.assertIn("invalid:defects[0].severity", errors)

    def test_schema_doc_mentions_lane_packet_handoff(self):
        text = SCHEMA_DOC.read_text(encoding="utf-8")

        self.assertIn("Lane Return Packet", text)
        self.assertIn("lane-packet.schema.json", text)
        self.assertIn("gate_results", text)
        self.assertIn("WO-115 consumes this schema", text)


if __name__ == "__main__":
    unittest.main()
