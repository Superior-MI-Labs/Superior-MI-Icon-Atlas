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
        self.assertEqual(len(self.plan["reference_slots"]), 6)
        self.assertEqual(len(self.plan["target"]["directions"]["required"]), 8)
        self.assertEqual(self.plan["target"]["health_variants"]["low_health_when"], "health_percent <= 36")
        self.assertEqual(self.plan["target"]["health_variants"]["normal_when"], "health_percent > 36")
        self.assertTrue(self.plan["provenance"]["reference_identity_approved"])
        self.assertFalse(self.plan["provenance"]["canonical_views_qualified"])
        self.assertTrue(any(ref["id"] == "ref.wardrobe_approved" and ref["approval"] == "APPROVED" for ref in self.plan["reference_slots"]))
        self.assertTrue(any("no wings" in rule for rule in self.plan["canonical_lock"]["visual_invariants"]))
        self.assertTrue(any("three separate feathered" in rule for rule in self.plan["canonical_lock"]["visual_invariants"]))
        self.assertTrue(any("galactic irises" in rule for rule in self.plan["canonical_lock"]["visual_invariants"]))
        self.assertTrue(any(x["track"] == "sword" for x in self.plan["qualification_clips"]))
        self.assertTrue(any(x["track"] == "secondary" for x in self.plan["qualification_clips"]))

    def test_sunblade_has_real_separate_fragment_contract(self):
        sword = self.plan["target"]["weapon"]
        articulation = sword["articulation"]
        self.assertTrue(articulation["separate_actor"])
        self.assertEqual(articulation["default_space"], "root_relative_back_hover_not_sheathed")
        self.assertEqual(articulation["status"], "CREATOR_DESIGN_LOCKED_RUNTIME_NOT_IMPLEMENTED")
        self.assertEqual(
            [element["id"] for element in articulation["canonical_elements"]],
            ["hilt", "guard", "blade_fragments", "cohesion_weave", "cloth_and_feathers"]
        )
        self.assertIn("held_melee", articulation["motion_phases"])
        self.assertIn("release", articulation["motion_phases"])
        self.assertIn("hand_lock", articulation["motion_phases"])
        self.assertIn("independent translation", next(e["allowed_motion"] for e in articulation["canonical_elements"] if e["id"] == "blade_fragments"))
        self.assertTrue(any("endpoints" in item for item in articulation["invariant_rules"]))
        self.assertFalse(self.plan["provenance"]["weapon_articulation_qualified"])
        self.assertTrue(any(gate["id"] == "weapon_articulation" and gate["stage"] == "P3" for gate in self.plan["qa_gates"]))

    def test_hero_angle_and_tail_roots_are_explicit_not_falsely_qualified(self):
        pose = self.plan["target"]["hero_master_perspective"]
        self.assertEqual(pose["status"], "USER_APPROVED_WITH_POSITIONAL_ADJUSTMENT")
        self.assertIn("three-quarter", pose["view"])
        self.assertIn("lower back/hip/pelvic", pose["tail_attachment"])
        self.assertIn("upper two tails", pose["tail_attachment"].lower())
        self.assertTrue(self.plan["provenance"]["pose_direction_approved"])
        self.assertFalse(self.plan["provenance"]["corrected_hero_master_qualified"])
        self.assertFalse(self.plan["provenance"]["generated_reference_candidate_reviewed"])
        self.assertTrue(any(r["role"] == "creator_approved_shallow_three_quarter_view_and_lower_triple_tail_roots" for r in self.plan["reference_slots"]))
        self.assertEqual(self.plan["target"]["input_design"]["action_manifest_path"], "production/sky-blue-eyes/controls-proposal.json")
        self.assertNotIn("actions", self.plan["target"]["input_design"], "input bindings must have a single source")

    def test_complete_keyboard_mouse_gamepad_parity(self):
        control = json.loads((ROOT / "production/sky-blue-eyes/controls-proposal.json").read_text(encoding="utf-8"))
        self.assertEqual(control["status"], "DESIGN_PROPOSAL_NOT_IMPLEMENTED")
        bindings = control["bindings"]
        keys = [binding["id"] for binding in bindings]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertGreaterEqual(len(keys), 18)
        self.assertTrue(all(x.get("gamepad") and x.get("keyboard_mouse") and x.get("remappable") for x in bindings))
        for required in ["move", "aim_sword", "jump", "light_attack", "heavy_attack", "evade", "block_parry", "attach_release_recall", "sword_command", "precision_focus", "anchor", "interact", "pause", "map_objectives"]:
            self.assertIn(required, keys)
        vortex = next(g for g in control["gestures"] if g["id"] == "sword_vortex")
        self.assertIn("Hold RT", vortex["gamepad"])
        self.assertIn("Hold F", vortex["keyboard_mouse"])
        self.assertTrue(control["analog_policy"]["no_right_thumb_chord_requirement"])
        self.assertEqual(self.plan["target"]["weapon"]["articulation"]["canonical_elements"][0]["id"], "hilt")
        self.assertTrue((ROOT / "production/sky-blue-eyes/CONTROL-AND-COMBO-PROPOSAL.md").is_file())

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

    def test_approved_identity_does_not_approve_animation_art(self):
        self.assertEqual(self.plan["canonical_lock"]["status"], "PENDING")
        self.assertEqual(self.plan["target"]["face_reveal_policy"].startswith("hide muzzle"), True)
        self.assertTrue(any(x["id"] == "sky.head.talk.masked" for x in self.plan["qualification_clips"]))
        self.assertFalse(any("wing" in x["id"] for x in self.plan["qualification_clips"]))
        self.assertFalse(any("wing" in clip for gate in self.plan["qa_gates"] for clip in gate.get("covers", [])))
        self.assertEqual(self.plan["target"]["weapon"]["aspects"][0], "dormant")

    def test_invalid_clip_stage_returns_validation_error(self):
        plan = copy.deepcopy(self.plan)
        plan["qualification_clips"][0]["stage"] = "NOT_A_STAGE"
        problems = check(plan)
        self.assertTrue(any("Unknown clip stage" in issue for issue in problems))

    def test_uncovered_first_slice_rejected(self):
        plan = copy.deepcopy(self.plan)
        for gate in plan["qa_gates"]:
            gate["covers"] = [c for c in gate["covers"] if c != "sky.secondary.tails.idle"]
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
