# Recipe: animated icons, characters, objects and effects

**Start from:** [three-frame pulse icon](../../demo/animated-icons.zip) or [robot idle/walk states](../../demo/character-animations.zip). For layered animation, see [glass/weather](../../demo/starter-pack.zip).

This recipe adds animation-specific quality gates to the maintained [release checklist](../RELEASE-CHECKLIST.md). It uses the existing `smi-visual-pack/1` `region` → `sequence` → `state_set` contract. Do not create a second animation registry, playback system, or source of truth.

## Mandatory production passes, in order

1. **Visual brief.** Extract the requested subject, reference identity, animation states, viewpoints, projection, visual style, logical frame size, color palette, pivot, target frame rate, platform and rights. Define what action must be readable in each named animation. Frame counts may vary.
2. **Canonical direction pass [HARD STOP].** Produce and *inspect* a stable independent base pose for every camera direction. Lock proportions, camera elevation, costume, silhouette, light direction, pixels-per-unit, transparency and planted-foot reference. Fix wrong facings before animating.
3. **Key-pose blocking [HARD STOP].** Storyboard anticipation → action/contact → recovery. Author actual meaningful action-specific key poses, not a whole-sprite translation/warp just to produce unique hashes. Foot taps need ankle/toe movement and a planted support leg; impatient animation needs legible changes in head/arms/weight; breathing idle may remain subtle. If still key poses do not communicate the action, correct them.
4. **In-between construction.** Create necessary transitions and set frame durations by the action rather than filler counts. Inspect **each frame** at native game scale and nearest-neighbor enlargement, on dark and light backgrounds. Fix hair/face/wardrobe drift, joints, heel contact, pixel crawl, fringe pixels and partial cuts.
5. **Motion inspection [HARD STOP].** Compare **every adjacent pair and last→first**, not just first/middle/last. Watch **every sequence in every direction** at 0.5×, 1× and 2× speed. Assess ground anchors, occlusion, motion arcs, acceleration, seamless looping and transitions between states. Reject static-looking, rubbery or jittery movement; re-enter the appropriate art production pass *before release*.
6. **Pack vetted art.** Measure actual crop bounds; pack cleaned transparent RGBA frames into exact rectangles with sufficient gutters. Concepts, guide grids, labels and promotional backdrops are not production textures. Preserve stable asset IDs and authoritative manifest ownership. Use `region` for cells, `sequence` for ordered frames and per-frame `duration_ms`, `state_set` for named modes and facings, and `composition` only if layering adds real value. Encode holds with durations instead of duplicate frames.
7. **Execute technical gates on the final ZIP.** Run `python3 tools/validate_visual_pack.py FINAL.zip`, `python3 tools/qualify_asset_zip.py FINAL.zip --strict --out qa/final` (when isolated padded sprites), and `python3 tools/ai_acceptance.py FINAL.zip --acceptance TEST.json --out qa/acceptance`. Verify required facings, states, timing, frame uniqueness and source references. Inspect all generated contact sheets and loops. Automated PASS is not artistic PASS.
8. **Real browser import and round-trip [HARD STOP].** Import the final bytes into the actual Visual Atlas Builder, play all states/directions, verify default preview, then export/reimport. If unavailable, say NOT RUN and do not claim finished integration.
9. **Independent release audit [HARD STOP].** Record the number of frames actually inspected, every transition and sequence reviewed, test evidence, remaining art defects, and rights for intended distribution. If anything mandatory fails or was not run, label **NEEDS FIXES** and return to the failed stage. **Never hand over a production ZIP with deferred post-release polish.**

## Required animation release receipt

```text
ANIMATION RELEASE GATE
Canonical directions inspected: <count>/<expected>
Action key poses visually approved: PASS | FAIL | NOT RUN
Individual frames inspected: <count>/<expected>
Adjacent and closing loop pairs inspected: <count>/<expected>
Every-direction animation loops reviewed: <count>/<expected>
All state transitions & speed variants: PASS | FAIL | NOT RUN
Official manifest validator: PASS | FAIL | NOT RUN
Official pixel/crop QA: PASS | WARN | FAIL | NOT RUN
Creator-specific executable acceptance: PASS | FAIL | NOT RUN
Actual builder import & export/reimport: PASS | FAIL | NOT RUN
Source rights for intended release: PASS | FAIL | NOT RUN
Remaining defects: <facts>
Status: RELEASE APPROVED | NEEDS FIXES
```

**Honesty rule:** A valid manifest, unique frame hash, or loop-difference metric does **not** prove visual semantics or good animation. An actual animation review is mandatory. Unexecuted checks are NOT RUN.

Contract source: [`examples/character-animations/manifest.json`](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/character-animations/manifest.json).
