# Side-scrolling character production — reusable motion and reference gate

**Scope:** high-quality frame-based player/NPC characters, independently animated equipment and effects, and optional dialogue portraits. This is an extension of the [general animation recipe](README.md), not a replacement for the [creator preflight](../CREATOR-PREFLIGHT.md), [manifest contract](../FORMAT-API.md), or [release checklist](../RELEASE-CHECKLIST.md). Load this guide **only** for relevant side-scrolling character work.

**First candidate:** [Sky Blue Eyes motion-foundation plan](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/production/sky-blue-eyes/plan.json). It is a machine-checked preproduction plan, **not** renderable artwork, an approved model sheet, a runtime asset pack, or a working state-machine controller.

## What we learned and must preserve

The Visual Atlas pipeline has already taught us several lessons: image models can make excellent presentation art that is **not** production sprite geometry; texture grid coordinates must come from inspected pixels; a valid JSON manifest can still produce visually broken assembled output; and interactive previews must show actual user-controlled values rather than merely decorative dropdowns. Our later animation lessons add broken articulation from warped single-pose art, identity drift across generated views, false animation from optical-flow ghosts, clipped wings, misaligned pivots, and loop seams that pop. Keep the current production chain: **faithful brief → references → key poses → measured pixels → existing manifests → actual browser preview → acceptance → handoff**.

For each regression record **observation → root cause → correction → executable/visual gate → evidence**, in the relevant existing guide. Do not create another competing global checklist, registry, or animation engine.

## Gate P0 — canonical references before bulk animation

A reference image is not automatically a canonical, animation-ready pose. Assign each supplied image one **specific role**, record its source and rights status, and distinguish its approved design facts from incidental lighting, background, text, camera angle, or other characters. The Sky plan records four historical candidate references plus one **creator-approved wardrobe reference** (SHA-256 fingerprint in the plan): the hooded, veiled desert wanderer. The latest creator instructions supersede earlier anatomy concepts: **no wings, exactly three independent feathered tails, and celestial galaxy-like eyes**. Neither the original pixels nor isolated animation masters are yet committed to the repository. Their pixels are **not committed to the repository** and cannot be assumed available to a later agent without an attachment or licensed source transfer.

Produce a model-sheet package *as real, separately inspectable art*, not one image prompt asking for a giant collage:

1. **Character identity:** preserve the approved hood's solar sigil, covered muzzle/mouth, gold brooch, cream/saffron wraps, layered torn red cloth, spotted feline paws, black-hole-centered blue/teal galactic iris and **three separate feathered tails**. No wings in V1. The user-approved image locks the *design language*, not its inaccurate/occluded anatomy in every angle.
2. **Canonical poses:** produce a consistent 8-view orthographic turnaround: front 0°, front-right 45°, right 90°, back-right 135°, back 180°, back-left 225°, left 270°, front-left 315°, plus right combat stance. Each must be a **separate, full-size, clean source image** with common scale and ground line—not a collage of tiny poses. The initially playable 2D side-scroller still qualifies right/left motion before the other facings get full animation sets.
3. **Shape/palette lock:** clean silhouette on light, midtone and dark backdrops; no unreadable clumps from feathers, ornate wraps, or sword glow. Palette reference includes flat color samples with readable material boundaries. Effects are overlays; never substitute dramatic sunset lighting for a base color model.
4. **Camera and geometry:** orthographic side-scroller; right-facing is the initial animation master. Choose a single logical body canvas and world-space foot baseline. Sample target is 384–512 px tall source body and 240–320 px on-screen, both explicitly **provisional** until measured in a scene.
5. **Directionality:** mirror-testing may be used diagnostically, but both actual left/right canonical views must be reviewed. Annotate asymmetric hood folds, solar emblems, shoulder clasp, belt rings, wrap binding, weapon strap and cloth tear placements; verify that three tails share plausible roots and overlap naturally in side/front views. Never claim a flip automatically preserves asymmetrical detail.
6. **Licensing:** record creator/source rights before publishing any derivative. Do not infer that a reference image is authorized for unrestricted distribution.

**Approval rule:** P0 is complete only when the model sheet, palette, camera, body canvas, anchors, default Sunblade silhouette, and source-rights decision are approved and evidence recorded. Approval of a plan does not equal approval of artwork. When uncertainty would make bulk work expensive, produce the smallest reversible study instead.

### P0 failure mode: beautiful reference collage, unusable animation source

**Observed in Sky's first visual exploration:** AI generations made ornate presentation boards with multiple tiny figures, textual labels, sword thumbnails, and schematic action poses. These were useful for discussion but **failed canonical sprite qualification**. Do not crop a tiny pose from such a board, upscale it, and silently call it an animation frame.

**Correction:** use the original identity references for planning, then create **one isolated full-height right-facing, 90-degree side-profile character per art-generation pass**, on a simple uniform neutral ground with visible feet, a known camera and the full silhouette. Explicitly prohibit title text, multi-panel layout, diagrams, extra characters, motion smear, weapons overlapping the body, and dramatic background lighting. Do not draw wings. Request the sword as a separately authored object, not strapped to or baked over the character's silhouette. Generate alternate views and motion key poses in separate passes *after* one view passes identity and scale review.

**Gate:** inspect the single isolated pose at target on-screen height, compare masked eye/ear shape, galactic iris, body markings, garment seams, the three distinct tail roots and tail feather shapes to the approved source and creator updates, and verify one contiguous figure without clipping. Mark `NEEDS FIXES` if the output is a collage, inconsistent view, or scene painting even when aesthetically excellent. An image-generation response is not a qualified PNG sprite sheet, stable model sheet, or loop. See [Sky P0 review](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/production/sky-blue-eyes/P0-REVIEW.md) for concrete regression evidence.

### Sky-specific design-lock contract (2026-11-02)

The user explicitly approved the **original cream-and-saffron hooded, face-covered desert wanderer** reference. That approval is a style/identity lock, **not** permission to approve newly generated images without inspection. The approved reference image has SHA-256 `5f0aa77d1514c1f859a5143732d4a39a3295a2afbb3b0fc0731878c98d95c97f`, documented in the plan. Preserve:

- No wings. A consistent **trio** of feathered tails; from certain directions they may occlude each other, but three distinct roots/anatomical strands must be confirmed in the back and three-quarter views.
- Hood and scarf hide the mouth and most facial identity. Eye visibility is intentional; the galaxy-like iris has a dark black-hole pupil, swirling blue/teal dust and sparse stars. Distant read: blue eyes with a restrained glow; close-up read: cosmic depth and short optical trails.
- The shoulder sun clasp, solar hood embroidery, torso crossover wraps, tattered layered hem, belt medallions, leg bandages and exposed spotted feline paws keep their positions and scale across every facing. Reverse-side folds must be derived consistently, never invented.
- The dormant Sunblade is a **separate weapon asset** and separate track, wrapped in torn fabric with a few phoenix-feather ties and barely visible cohesion magic. Unlockable aspects use optional FX overlays and host puzzle abilities, not seven different core weapon motion definitions.
- **Unframed head assets**: front, three-quarter and side at readable portrait size, with neutral, listen, masked-talk, blink, focus and low-health possibilities. Each source must be a clean standalone image with no rectangular frame, dialogue box, title, annotations or second character. The hood/veil and three-tail body design are not negotiable.
- Health visuals use **normal >36%** versus **low <=36%** only; health 0/death remains a separate body state.

**QA anti-pattern:** several generated "canonical character design" infographics showed eight tiny angle studies but did not supply consistent, individually editable source files; dialogue heads were presented in boxes; some color-variant eyes were invented from health state; directions and tails could not be independently verified. Mark **CONCEPT ONLY / P0 NOT PASSED**. For future generation, use a **single-view or single-unframed-head** source task per iteration; only compose a presentation sheet *after* each source view is individually qualified. Source-art prompt engineering or attractive typography must never be mistaken for animation-ready geometry.

## Gate P1 — smallest useful *working* animation slice

Create these actual Visual Atlas assets first: relaxed side idle loop; run loop and an authored run-stop transition; three-tail idle secondary motion; and a separate dormant Sunblade orbit visualization. Build one **self-contained** ZIP using existing `smi-visual-pack/1` kinds and real measured PNG frames. Do not invent a controller property in this strict v1 schema.

The [plan](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/production/sky-blue-eyes/plan.json) defines clip IDs and evidence gates. Validate it with:

```bash
python3 tools/validate_animation_plan.py production/sky-blue-eyes/plan.json
python3 -m unittest tests/test_animation_plan.py -v
```

An approved P1 ZIP must additionally pass the existing ZIP validator, pixel qualification, request-specific acceptance, and Chromium rendered-state tests, including **run → stop → idle**, native-scale visible identity, actual animation, loop seam and adjacent-frame contacts, attach-point continuity, and round-trip import. The checks in the plan are *planned evidence*, not already-executed results.

Do not generate 200 actions, six complete sword variants, or every health/stance combination to qualify the underlying drawing method. If the first idle motion looks like a translated cardboard cutout, do not expand; redraw genuine key poses and fix the source.

## State machine architecture — proposal, not runtime support

Current `region`, `sequence`, `state_set`, and `composition` assets remain the single source of truth for pixels/frames/visual layers. The current `state_set` chooses named assets but is **not** a gameplay-conditional state machine. An optional future `smi-animation-controller/1` sidecar may reference existing asset IDs and declare typed parameters, hierarchical states, condition grammar, transition priorities, markers, deterministic idle scheduler and parallel track ownership. Before implementing it: write a schema, pure evaluator, negative tests, deterministic trace and a thin adapter for existing builder controls. Do not duplicate frame data, write executable scripts inside imported JSON, or turn Atlas into a physics/combat engine.

### Articulated autonomous relic weapons — Sunblade canonical animation contract

For weapons whose shape is held by **energy rather than physical joins**, the individual blade fragments are independent visible objects. Shattering cannot be faked with cracks painted on one rigid sword image. The canonical base consists of an isolated hilt/grip, solar guard/rings, stable-ID blade shards and tip, energy weave passing through *changing gaps*, plus cloth and phoenix-feather secondary motion. Keep the sword a **separate actor** from character body art: its default back/shoulder hover is not a scabbard or sheathing animation.

**Build-versus-reuse choice:** test a small multi-layer `composition` backed by current `region` art and existing timeline/keyframes before requesting a dedicated weapon renderer or a second animation-controller pipeline. We can animate individual shard translations/rotations through existing layers where expressible; fluid energy tethers whose endpoints continuously follow separately moving fragments may require a bounded extension to the existing renderer after a clear fixture demonstrates that current constructs cannot describe them. A static sword render with particle glow does **not** qualify the independent-shard requirement.

**Animation hierarchy:** the sword actor controls its root trajectory (back hover, orbit, cast, anchor, recall, hand-lock, held melee, release). Shards have **local, bounded** translation and rotation relative to that root, each with its own phase and slight lag/damped return. The grip/hilt is authoritative: when Sky grabs it, hand attachment is exact and stable; independently floating metal can continue to flex around the now hand-locked hilt. Distinct fragments must remain recognizable and their order stable across pose changes. Energy-tether endpoints follow moving pieces; strands pulse, coil and elongate as gaps open, never teleport, disconnect or turn into physical rods.

**Art-direction phases:** back hover has almost imperceptible asynchronous shard breathing; orbit adds delayed follow-through; cast separates shards and stretches cohesion strands; impact briefly compresses and rebounds; recall draws them toward a familiar silhouette; held melee tightens alignment for readability while keeping independent shard vibration; release relaxes into autonomous flight. No physically unrealistic random jitter or blade fragments drifting so far that its combat silhouette disappears.

**Unlockable forms:** dormant, radiant, frost, ember, gale, storm and spirit share the exact same fragment identity, key pivots, grip point and motion envelope. Variants may customize energy weave texture, hue, flow behavior, frost accretion, embers, wind streamers, lightning branches or spectral haze; they do not introduce duplicate base weapon animations. Dormant still has very subtle cohesion filaments—without them, the blade would visibly fall apart.

**Mandatory motion acceptance:** inspect a loop and combat keyposes with at least two shards rotating/translating independently, moving energy endpoints, readable silhouette, continuous first/last frame, correct overlapping cloth/feathers, and exact hand-hilt anchoring. Scrub aspect swaps at the same moment to check that fragment positions do not teleport. An attractive illustrated variant sheet is only a visual concept, not proof that this behavior animates.

**Track ownership:** body/root and foot contacts; sword movement and world/local-space choice; the three feathered tails/hood/scarf/cloth; transient FX; masked portrait/dialogue. The body has no wings and no flying/gliding V1 track. For example, the orbiting sword tracks the body root, but a cast sword remains world-positioned when Sky dashes. Host gameplay owns actual damage, collision, i-frames, combos, jump buffering, and attack outcomes; Atlas previews corresponding visual cues.

**Health-dependent idle:** Sky V1 uses exactly **two** non-death art tiers: normal when health >36%, low when health <=36%. No fatigued/middle tier, no changed thresholds, no inferred red-eye state. These are clip selectors, not giant pre-baked matrices. If a future host needs temporal debouncing, it must preserve the user's actual 36% boundary rather than silently inventing a hysteresis band. Rare idle one-shots need eligibility, dwell time, seeded weighted choice, cooldown, one-shot completion, and safe return markers. Their algorithm lives in one controller evaluator, not duplicated inside per-character artwork.

**Transition families:** immediate interrupt, completion, contact/attack marker, phase-preserving (walk/run), and authored bridge. Avoid visually ghosted whole-character crossfades; full-body directional/action changes should generally have real transition art. Validate priorities, interruption, unreachable states, rapid health changes, repeatable seeded idles and missing-optional-layer fallback.

## Timing, anchors and sheets

- **Art FPS:** 16 as a default, not a cap. Per-frame positive `duration_ms` may hold certain drawings longer. A game may simulate at 60 Hz and render at display refresh; do not convert a 4-tick attack into a guess based on 16 FPS image count.
- **Anatomy and motion:** plan key contact poses, foot planting, anticipation, follow-through and real in-betweens. Never synthesize a running gait by globally shifting one static image. Review every frame and every adjacent pair.
- **Logical root:** feet projected to ground. Track important per-pose anchors (hands, feet, each of the three tail roots, head/ears, orbit anchor), with names and coordinate-space conventions. Preserve origin through trimmed packing and facing flips.
- **Atlas output:** keep source poses individually accessible, then use deterministic measured packing. Default to 2048² texture pages; consider 4096² only after real size/residency tests. Record exact alpha bounds, logical canvas, trim offset and pivot. **Current Canvas renderer does not yet fully apply trim offsets/pivots**; qualify/fix that before approving tightly trimmed production animation.
- **Budget:** size the sheets from actual approved alpha bounds after one loop—not from an invented fixed number. Current importer caps ZIP compressed/expanded size at 120 MiB, each member at 24 MiB, and eagerly decodes images. Avoid a monolithic full-game ZIP; do not promise cross-ZIP dependency resolution until tested.
- **Effects:** dust, spark, parry, afterimage and sword trails are independent assets, not always baked into body art. Dialogue art uses **unframed transparent masked-head/bust assets**. Since the mouth remains covered, speech is conveyed by subtle scarf motion, eye focus, blink, ear tension, hood/head movement and gestures; do not create open-mouth frames, expose the muzzle or bake a decorative text-frame rectangle into each asset. A future UI may surround these assets independently.

## Work milestones and high-fidelity gates

| Milestone | Outputs | Gate |
|---|---|---|
| P0 | Canonical reference sheet, palette, pose/anchor/camera lock and rights provenance | Creator signs off the actual visual identity, not a text-only summary |
| P1 | Right-facing idle, run/stop, three-tail idle and dormant sword orbit in a self-contained ZIP | Real source frames, native-scale preview, frame/contact QA, ZIP roundtrip |
| P2 | Low-health (<=36%) / rare idle, prejump and jump/land with parameter-driven preview | Hysteresis, no input lag, phase/timing, artwork transitions |
| P3 | Combo slice, dodge/parry and independent sword cast/recall | Legal interrupt/cancel windows, cues exactly once, sword world-space stability |
| P4 | Effects, secondary motion and dialogue bust/expressions | Layer ownership, clean silhouettes, portrait timing, QA evidence |
| P5 | Expand by action family: climb, wall, slide, grab, throw, loot, open chest, NPC variants | Each new family reuses shared contracts and passes a full end-to-end gate |
| P6 | Validate one real game adapter, memory budget and optional compression | No second runtime truth, measured decode/residency and stable IDs |

The first milestone is **reference and pipeline qualification**, not bulk art generation. Each later batch should contain one coherent family and its tests: real artwork, measured manifest, reference closure, browser visuals, regression outcomes and release notes. Preserve the approved working pack while testing new candidates on a branch.

## Agent handoff and truthful completion

1. Reconstruct the current request using [creator preflight](../CREATOR-PREFLIGHT.md). Inspect only relevant images/files, the current master plan, authoritative schema and animation recipe.
2. State **confirmed / proposed / pending** reference decisions. For Sky, respect the approved masked-desert-wanderer **identity** but do not pretend it or the generated infographics provide a clean eight-direction turnaround. Review [Sky P0 art gate](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/production/sky-blue-eyes/P0-REVIEW.md).
3. Choose existing `smi-visual-pack/1` representations first. If a requirement cannot be expressed, record a capability gap and test two designs before modifying the runtime.
4. Generate/art-direct only the smallest qualification slice until proportions, facing, style and real motion are approved. Preserve pose images and failure notes.
5. Run plan validation, source/alpha/frame inspection, ZIP/acceptance QA and browser rendered-state tests. Save both passing and failing evidence. Do not claim visual PASS if only schemas were checked.
6. Record the exact observation, root cause, adjustment, regression test and evidence in this task guide or an existing relevant recipe. No duplicate checklist or schema.
7. Never publish reference imagery or asset packs without source rights/approval and verified CI. A passing planning-data test is **NOT** a playable demo.

See the [standard release checklist](../RELEASE-CHECKLIST.md) for the mandatory final ZIP receipt. 
