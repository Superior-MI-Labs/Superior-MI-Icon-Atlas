# Side-scrolling character production — reusable motion and reference gate

**Scope:** high-quality frame-based player/NPC characters, independently animated equipment and effects, and optional dialogue portraits. This is an extension of the [general animation recipe](README.md), not a replacement for the [creator preflight](../CREATOR-PREFLIGHT.md), [manifest contract](../FORMAT-API.md), or [release checklist](../RELEASE-CHECKLIST.md). Load this guide **only** for relevant side-scrolling character work.

**First candidate:** [Sky Blue Eyes motion-foundation plan](../../../production/sky-blue-eyes/plan.json). It is a machine-checked preproduction plan, **not** renderable artwork, an approved model sheet, a runtime asset pack, or a working state-machine controller.

## What we learned and must preserve

The Visual Atlas pipeline has already taught us several lessons: image models can make excellent presentation art that is **not** production sprite geometry; texture grid coordinates must come from inspected pixels; a valid JSON manifest can still produce visually broken assembled output; and interactive previews must show actual user-controlled values rather than merely decorative dropdowns. Our later animation lessons add broken articulation from warped single-pose art, identity drift across generated views, false animation from optical-flow ghosts, clipped wings, misaligned pivots, and loop seams that pop. Keep the current production chain: **faithful brief → references → key poses → measured pixels → existing manifests → actual browser preview → acceptance → handoff**.

For each regression record **observation → root cause → correction → executable/visual gate → evidence**, in the relevant existing guide. Do not create another competing global checklist, registry, or animation engine.

## Gate P0 — canonical references before bulk animation

A reference image is not automatically a canonical, animation-ready pose. Assign each supplied image one **specific role**, record its source and rights status, and distinguish its approved design facts from incidental lighting, background, text, camera angle, or other characters. The Sky plan currently records four **conversation-only** reference candidates: anatomy/wings/tail; cream/saffron costume; six Shattered Sunblade designs; and Empty Body flame form. Their pixels are **not committed to the repository** and cannot be assumed available to a later agent without an attachment or licensed source transfer.

Produce a model-sheet package *as real, separately inspectable art*, not one image prompt asking for a giant collage:

1. **Character identity:** exact silhouette, feline proportions/markings, sky-blue eyes, outfit construction, wing feather groups, and bifurcated tail. Compare against the source reference at normal gameplay size, not only zoomed-in art.
2. **Canonical poses:** right-facing side neutral; right-facing combat guard; forward/back construction checks; folded and extended wings; grounded foot alignment; separate weapon at known scale. Every pose must depict the **same character**, not merely the same theme.
3. **Shape/palette lock:** clean silhouette on light, midtone and dark backdrops; no unreadable clumps from feathers, ornate wraps, or sword glow. Palette reference includes flat color samples with readable material boundaries. Effects are overlays; never substitute dramatic sunset lighting for a base color model.
4. **Camera and geometry:** orthographic side-scroller; right-facing is the initial animation master. Choose a single logical body canvas and world-space foot baseline. Sample target is 384–512 px tall source body and 240–320 px on-screen, both explicitly **provisional** until measured in a scene.
5. **Directionality:** test mirrored-left first; annotate asymmetric costume/weapon/hands and wing occlusion. Commission distinct left art only if mirror visibly breaks identity or gameplay readability.
6. **Licensing:** record creator/source rights before publishing any derivative. Do not infer that a reference image is authorized for unrestricted distribution.

**Approval rule:** P0 is complete only when the model sheet, palette, camera, body canvas, anchors, default Sunblade silhouette, and source-rights decision are approved and evidence recorded. Approval of a plan does not equal approval of artwork. When uncertainty would make bulk work expensive, produce the smallest reversible study instead.

## Gate P1 — smallest useful *working* animation slice

Create these actual Visual Atlas assets first: relaxed side idle loop; run loop and an authored run-stop transition; separate wing idle motion; and a Sunblade orbit visualization. Build one **self-contained** ZIP using existing `smi-visual-pack/1` kinds and real measured PNG frames. Do not invent a controller property in this strict v1 schema.

The [plan](../../../production/sky-blue-eyes/plan.json) defines clip IDs and evidence gates. Validate it with:

```bash
python3 tools/validate_animation_plan.py production/sky-blue-eyes/plan.json
python3 -m unittest tests/test_animation_plan.py -v
```

An approved P1 ZIP must additionally pass the existing ZIP validator, pixel qualification, request-specific acceptance, and Chromium rendered-state tests, including **run → stop → idle**, native-scale visible identity, actual animation, loop seam and adjacent-frame contacts, attach-point continuity, and round-trip import. The checks in the plan are *planned evidence*, not already-executed results.

Do not generate 200 actions, six complete sword variants, or every health/stance combination to qualify the underlying drawing method. If the first idle motion looks like a translated cardboard cutout, do not expand; redraw genuine key poses and fix the source.

## State machine architecture — proposal, not runtime support

Current `region`, `sequence`, `state_set`, and `composition` assets remain the single source of truth for pixels/frames/visual layers. The current `state_set` chooses named assets but is **not** a gameplay-conditional state machine. An optional future `smi-animation-controller/1` sidecar may reference existing asset IDs and declare typed parameters, hierarchical states, condition grammar, transition priorities, markers, deterministic idle scheduler and parallel track ownership. Before implementing it: write a schema, pure evaluator, negative tests, deterministic trace and a thin adapter for existing builder controls. Do not duplicate frame data, write executable scripts inside imported JSON, or turn Atlas into a physics/combat engine.

**Track ownership:** body/root and foot contacts; sword movement and world/local-space choice; wings/tail/cloth; transient FX; portrait/dialogue. For example, the orbiting sword tracks the body root, but a cast sword remains world-positioned when Sky dashes. Host gameplay owns actual damage, collision, i-frames, combos, jump buffering, and attack outcomes; Atlas previews corresponding visual cues.

**Health-dependent idle:** healthy/fatigued/injured are conditional clip selectors, not giant pre-baked matrices. Example threshold for experiments: injured enters at <=25% health and exits at >=32% (hysteresis). Rare idle one-shots need eligibility, dwell time, seeded weighted choice, cooldown, one-shot completion, and safe return markers. Their algorithm lives in one controller evaluator, not duplicated inside per-character artwork.

**Transition families:** immediate interrupt, completion, contact/attack marker, phase-preserving (walk/run), and authored bridge. Avoid visually ghosted whole-character crossfades; full-body directional/action changes should generally have real transition art. Validate priorities, interruption, unreachable states, rapid health changes, repeatable seeded idles and missing-optional-layer fallback.

## Timing, anchors and sheets

- **Art FPS:** 16 as a default, not a cap. Per-frame positive `duration_ms` may hold certain drawings longer. A game may simulate at 60 Hz and render at display refresh; do not convert a 4-tick attack into a guess based on 16 FPS image count.
- **Anatomy and motion:** plan key contact poses, foot planting, anticipation, follow-through and real in-betweens. Never synthesize a running gait by globally shifting one static image. Review every frame and every adjacent pair.
- **Logical root:** feet projected to ground. Track important per-pose anchors (hands, feet, wing roots, tail, orbit anchor), with names and coordinate-space conventions. Preserve origin through trimmed packing and facing flips.
- **Atlas output:** keep source poses individually accessible, then use deterministic measured packing. Default to 2048² texture pages; consider 4096² only after real size/residency tests. Record exact alpha bounds, logical canvas, trim offset and pivot. **Current Canvas renderer does not yet fully apply trim offsets/pivots**; qualify/fix that before approving tightly trimmed production animation.
- **Budget:** size the sheets from actual approved alpha bounds after one loop—not from an invented fixed number. Current importer caps ZIP compressed/expanded size at 120 MiB, each member at 24 MiB, and eagerly decodes images. Avoid a monolithic full-game ZIP; do not promise cross-ZIP dependency resolution until tested.
- **Effects:** dust, spark, parry, afterimage and sword trails are independent assets, not always baked into body art. Dialogue portraits are separate bust/eyes/mouth/expression components with their own presentation controller.

## Work milestones and high-fidelity gates

| Milestone | Outputs | Gate |
|---|---|---|
| P0 | Canonical reference sheet, palette, pose/anchor/camera lock and rights provenance | Creator signs off the actual visual identity, not a text-only summary |
| P1 | Right-facing idle, run/stop, wing idle and sword orbit in a self-contained ZIP | Real source frames, native-scale preview, frame/contact QA, ZIP roundtrip |
| P2 | Injured/rare idle, prejump and jump/land with parameter-driven preview | Hysteresis, no input lag, phase/timing, artwork transitions |
| P3 | Combo slice, dodge/parry and independent sword cast/recall | Legal interrupt/cancel windows, cues exactly once, sword world-space stability |
| P4 | Effects, secondary motion and dialogue bust/expressions | Layer ownership, clean silhouettes, portrait timing, QA evidence |
| P5 | Expand by action family: climb, wall, slide, grab, throw, loot, open chest, NPC variants | Each new family reuses shared contracts and passes a full end-to-end gate |
| P6 | Validate one real game adapter, memory budget and optional compression | No second runtime truth, measured decode/residency and stable IDs |

The first milestone is **reference and pipeline qualification**, not bulk art generation. Each later batch should contain one coherent family and its tests: real artwork, measured manifest, reference closure, browser visuals, regression outcomes and release notes. Preserve the approved working pack while testing new candidates on a branch.

## Agent handoff and truthful completion

1. Reconstruct the current request using [creator preflight](../CREATOR-PREFLIGHT.md). Inspect only relevant images/files, the current master plan, authoritative schema and animation recipe.
2. State **confirmed / proposed / pending** reference decisions. For Sky, do not pretend the four image candidates are a fully approved turnaround.
3. Choose existing `smi-visual-pack/1` representations first. If a requirement cannot be expressed, record a capability gap and test two designs before modifying the runtime.
4. Generate/art-direct only the smallest qualification slice until proportions, facing, style and real motion are approved. Preserve pose images and failure notes.
5. Run plan validation, source/alpha/frame inspection, ZIP/acceptance QA and browser rendered-state tests. Save both passing and failing evidence. Do not claim visual PASS if only schemas were checked.
6. Record the exact observation, root cause, adjustment, regression test and evidence in this task guide or an existing relevant recipe. No duplicate checklist or schema.
7. Never publish reference imagery or asset packs without source rights/approval and verified CI. A passing planning-data test is **NOT** a playable demo.

See the [standard release checklist](../RELEASE-CHECKLIST.md) for the mandatory final ZIP receipt. 
