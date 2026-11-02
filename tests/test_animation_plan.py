"""Regression tests for the canonical-reference / motion preflight contract.

This is deliberately a production-planning gate; it does not assert that Sky
textures, a controller interpreter, or approved animation artwork exist.
"""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from tools.validate_animation_plan import check

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "production/sky-blue-eyes/plan.json"


class CharacterPlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(PLAN.read_text(encoding="utf-8"))

    def test_first_slice_is_traceable_and_planning_only(self):
        self.assertEqual(check(self.plan), [])
        self.assertEqual(self.plan["status"], "PREPRODUCTION")
        self.assertEqual(self.plan["runtime_support"], "NOT_IMPLEMENTED")
        self.assertFalse(self.plan["provenance"]["artwork_approved"])
        self.assertFalse(self.plan["provenance"]["original_image_bytes_in_repo"])
        self.assertEqual(self.plan["target"]["art_fps_default"], 16)
        self.assertEqual(self.plan["target"]["gameplay_simulation_hz"], 60)
        self.assertEqual(len(self.plan["reference_slots"]), 4)
        self.assertTrue(any(x["track"] == "sword" for x in self.plan["qualification_clips"]))
        self.assertTrue(any(x["track"] == "secondary" for x in self.plan["qualification_clips"]))

    def test_duplicate_clip_rejected(self):
        plan = copy.deepcopy(self.plan)
        plan["qualification_clips"].append(copy.deepcopy(plan["qualification_clips"][0]))
        self.assertTrue(any("duplicate clip" in x.lower() for x in check(plan)))

    def test_missing_clip_reference_and_stage_rejected(self):
        plan = copy.deepcopy(self.plan)
        plan["transition_checks"][0]["to"] = "sky.body.nonexistent"
        self.assertTrue(any("missing clip" in x for x in check(plan)))
        plan = copy.deepcopy(self.plan)
        plan["transition_checks"][0]["stage"] = "P0"
        self.assertTrue(any("before its clips" in x for x in check(plan)))

    def test_invalid_clip_stage_returns_validation_error(self):
        plan = copy.deepcopy(self.plan)
        plan["qualification_clips"][0]["stage"] = "NOT_A_STAGE"
        problems = check(plan)
        self.assertTrue(any("Unknown clip stage" in issue for issue in problems))

    def test_uncovered_first_slice_rejected(self):
        plan = copy.deepcopy(self.plan)
        for gate in plan["qa_gates"]:
            gate["covers"] = [c for c in gate["covers"] if c != "sky.secondary.wings.idle"]
        self.assertTrue(any("P1 clips missing explicit QA" in x for x in check(plan)))

    def test_false_approval_rejected(self):
        plan = copy.deepcopy(self.plan)
        plan["status"] = "PRODUCTION_APPROVED"
        self.assertTrue(any("approval requires" in x for x in check(plan)))
        plan = copy.deepcopy(self.plan)
        plan["provenance"]["pixel_visual_qa"] = "PASS"
        self.assertTrue(any("Cannot claim visual QA PASS" in x for x in check(plan)))

    def test_no_accidental_runtime_schema_expansion(self):
        runtime = json.loads((ROOT / "schemas/smi-visual-pack-v1.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(runtime["additionalProperties"])
        self.assertNotIn("controller", runtime["properties"])
        self.assertTrue((ROOT / "docs/ai/animations/SIDE-SCROLLER-PRODUCTION.md").is_file())


if __name__ == "__main__":
    unittest.main()
