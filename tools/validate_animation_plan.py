#!/usr/bin/env python3
"""Validate preproduction character motion plans; NOT a runtime manifest parser."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ID = re.compile(r"^[a-z][a-z0-9_.-]*$")
STAGE = re.compile(r"^P[0-9]+$")
ALLOWED_KINDS = {"region", "sequence", "composition", "state_set"}
EXPECTED = "smi-character-production-plan/1"


def check(plan: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(plan, dict):
        return ["Plan must be an object"]
    if plan.get("schema") != EXPECTED:
        errors.append("Unknown character production plan schema")
    if plan.get("runtime_support") != "NOT_IMPLEMENTED":
        errors.append("Planning sidecar must not claim runtime support")
    if plan.get("status") not in {"PREPRODUCTION", "PRODUCTION_APPROVED"}:
        errors.append("Unknown production status")
    target = plan.get("target") or {}
    if not isinstance(target, dict):
        return errors + ["target must be an object"]
    if target.get("art_fps_default", 0) not in range(1, 121):
        errors.append("Invalid authored animation FPS")
    if target.get("gameplay_simulation_hz", 0) not in range(1, 241):
        errors.append("Invalid gameplay simulation Hz")
    refs = plan.get("reference_slots") or []
    ref_ids: set[str] = set()
    if not isinstance(refs, list) or not refs:
        errors.append("At least one canonical reference role is required")
        refs = []
    for item in refs:
        if not isinstance(item, dict):
            errors.append("Invalid reference record")
            continue
        ref = item.get("id")
        if not isinstance(ref, str) or not ID.fullmatch(ref) or ref in ref_ids:
            errors.append(f"Invalid or duplicate reference ID: {ref}")
        else:
            ref_ids.add(ref)
        if not item.get("role") or not item.get("source"):
            errors.append(f"Reference lacks role/source: {ref}")
        if item.get("approval") not in {"PENDING", "APPROVED", "REJECTED"}:
            errors.append(f"Reference has no review status: {ref}")
    lock = plan.get("canonical_lock") or {}
    if not isinstance(lock, dict) or not lock.get("required_views") or not lock.get("anchors"):
        errors.append("Reference lock must specify canonical views and anchors")
    if not isinstance(lock, dict) or lock.get("status") not in {"PENDING", "APPROVED"}:
        errors.append("Reference lock must state approval status")
    milestones = plan.get("milestones") or []
    stages = [m.get("id") for m in milestones if isinstance(m, dict)]
    if not stages or stages != [f"P{i}" for i in range(len(stages))]:
        errors.append("Milestones must be contiguous P0..Pn with no duplicates")
    if not milestones or milestones[0].get("release_scope") != "planning_only":
        errors.append("P0 must be planning-only, not published artwork")
    tracks = plan.get("track_owners") or []
    owners = [t.get("id") for t in tracks if isinstance(t, dict)]
    if not owners or len(set(owners)) != len(owners):
        errors.append("Animation track owners must be nonempty and unique")
    clips = plan.get("qualification_clips") or []
    ids: set[str] = set()
    clip_stages = {}
    for item in clips:
        if not isinstance(item, dict):
            errors.append("Invalid clip record")
            continue
        ident = item.get("id")
        if not isinstance(ident, str) or not ID.fullmatch(ident) or ident in ids:
            errors.append(f"Invalid or duplicate clip ID: {ident}")
            continue
        ids.add(ident)
        clip_stages[ident] = item.get("stage")
        if item.get("stage") not in stages:
            errors.append(f"Unknown clip stage: {ident}")
        if item.get("track") not in owners:
            errors.append(f"Unknown clip track: {ident}")
        if item.get("kind") not in ALLOWED_KINDS:
            errors.append(f"Unknown existing visual asset kind: {ident}")
        if item.get("playback") not in {"loop", "once", "pingpong"}:
            errors.append(f"Unsupported playback: {ident}")
    if not clips:
        errors.append("No qualification clips declared")
    checks = plan.get("qa_gates") or []
    covered: set[str] = set()
    gates = set()
    for item in checks:
        if not isinstance(item, dict):
            errors.append("Invalid QA gate")
            continue
        ident, stage = item.get("id"), item.get("stage")
        if ident in gates or not isinstance(ident, str) or not ID.fullmatch(ident):
            errors.append(f"Duplicate or invalid QA gate: {ident}")
        gates.add(ident)
        if stage not in stages or not item.get("evidence"):
            errors.append(f"QA gate lacks stage/evidence: {ident}")
        for clip in item.get("covers") or []:
            if clip not in ids:
                errors.append(f"QA references absent clip {clip}")
            elif stage == "P1":
                covered.add(clip)
    p1 = {c["id"] for c in clips if isinstance(c, dict) and c.get("stage") == "P1" and isinstance(c.get("id"), str)}
    if p1 - covered:
        errors.append("P1 clips missing explicit QA: " + ", ".join(sorted(p1 - covered)))
    for m in milestones:
        if isinstance(m, dict) and m.get("gate") not in gates:
            errors.append(f"Milestone {m.get('id')} references missing QA gate")
    for rule in plan.get("transition_checks") or []:
        src, dst, stage = rule.get("from"), rule.get("to"), rule.get("stage")
        if src not in ids or dst not in ids:
            errors.append(f"Transition {rule.get('id')} references missing clip")
        if stage not in stages:
            errors.append(f"Transition {rule.get('id')} has unknown stage")
        if not rule.get("policy"):
            errors.append(f"Transition {rule.get('id')} needs an explicit policy")
        if stage in stages and src in clip_stages and dst in clip_stages:
            if stages.index(stage) < max(stages.index(clip_stages[src]), stages.index(clip_stages[dst])):
                errors.append(f"Transition {rule.get('id')} occurs before its clips")
    provenance = plan.get("provenance") or {}
    if plan.get("status") == "PRODUCTION_APPROVED":
        if lock.get("status") != "APPROVED" or target.get("licensing") != "VERIFIED" or not provenance.get("rights_verified"):
            errors.append("Production approval requires locked art and verified rights")
        if not all(r.get("approval") == "APPROVED" for r in refs):
            errors.append("Production approval requires reference decisions")
    if not provenance.get("artwork_approved") and provenance.get("pixel_visual_qa") == "PASS":
        errors.append("Cannot claim visual QA PASS before artwork approval")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.plan.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"FAIL: Cannot read plan: {exc}", file=sys.stderr)
        return 1
    issues = check(data)
    for issue in issues:
        print("FAIL: " + issue, file=sys.stderr)
    if issues:
        return 1
    print(f"PASS: {data['project_id']} | {len(data['qualification_clips'])} declared clips | {len(data['qa_gates'])} evidence gates | PREPRODUCTION DATA ONLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
