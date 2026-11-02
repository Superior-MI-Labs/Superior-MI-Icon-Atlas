# Shattered Sunblade — A/B animation prototype, first measured outcome

**Stage:** P0→P1 technical experiment, **NOT** approved canonical production artwork or a public asset-pack release.

The first experimental import ZIPs are supplied separately in the conversation handoff `Sky-Sunblade-AB-Prototype-Handoff-v0.1.zip`. Their bytes are **not** committed to the public repo, and are not automatically available to subsequent agents. If the handoff ZIP is missing, ask for that artifact or rerun the included deterministic source generator; do **not** substitute concept-art collages or claim you tested it.

## What we actually built

A and B were generated from the **same original simplified nine-piece prototype sword art** (pommel, hilt, ornate guard, six blade shards), with a separate energy-strand image. Same 16 FPS motion source, 4 basic states: `hover`, `cast`, `recall`, `held`. The hero and sword are still independent actors; no sword is sheathed or baked into Sky's body artwork.

| Factor | Approach A — fragment composition | Approach B — precomposed frames |
|---|---|---|
| Existing manifest kinds | `region`, `composition`, `state_set` | `region`, `sequence`, `state_set` |
| Real source assets | Individual shard regions and one energy-strand region | Same fragments rasterized into 64 complete image frames |
| Motion implementation | Independent per-shard position/rotation keyframes, keyframed tether placement, using existing timeline and renderer layers | Whole-sword sequence at 16 authored FPS, per-frame drawn cohesion weave |
| Test coverage | Hover, cast, recall, held | Same states, same underlying poses |
| Package | `sunblade-a-v0.1.zip` | `sunblade-b-v0.1.zip` |
| Compressed ZIP, measured | **137,726 bytes** (~0.13 MiB) | **6,779,533 bytes** (~6.47 MiB) |
| Atlas pages | One 1024 × 512 page | Eight 1536 × 1280 pages |
| Live control after authoring | Good: each shard remains a separate asset | Low: shards flattened into each frame |
| Appearance of flowing energy | Keyframed strand sprites approximate connections; **not** genuinely endpoint-bound if a shard moves beyond the authored keys | Fully drawn, coherent at each authored frame; cannot react dynamically between frames |

The **50× package-size difference** for the small proof (rough ratio) is meaningful but not universally generalizable: visual quality, source resolution, trim packing, compression, level of effect detail, and number of states will change real numbers. Do not declare Approach A visually superior from file size alone.

## Structural qualification performed

**PASS (local Python checks):** 4 matching A/B states; 84 assets in combined pack; 64 complete authored B frames; six separately tracked animated blade shards and six animated tether layers per A state; unique IDs; every texture region valid and nontransparent; every input atlas dimension correct; monotonic keyframes; closed loop transforms; valid ZIP members and no oversized member.

**NOT COMPLETED:** the local environment blocked the Chromium navigation test even for a localhost viewer; the official Visual Atlas browser import and rendered-state QA have **not** been executed against this exact ZIP in CI. Do not claim a passing browser screenshot. A separate interactive HTML diagnostic viewer and animated GIFs are included in the handoff, as well as the reproducible builder and check scripts. The locally generated image preview is not equivalent to a real repository browser gate.

**NOT APPROVED:** ornate identity fidelity versus the user's six-concept Shattered Sunblade sheet. This test art is deliberately simplified and procedural, only to validate architecture and import contracts. The corrected wingless Sky hero master, exact hip-rooted triple tails and sword-hilt attachment art remain separate pending production gates. No public collection was added to `publications.json`.

## Critical observations → lessons → next gates

1. **Scope drift:** previous reference ZIPs contained images suggesting a sword worn/sheathed on Sky's back. **Correction:** never include such image in the **canonical body-only references**. Ship body-only, blade-only, fragment-only and interaction-overlay studies as separately labeled roles. The back hover is a separate sword transform.
2. **Art generation drift:** image models repeatedly delivered attractive multi-panel posters, not isolated original sprites. **Correction:** individual clean PNG source tasks; only generate reference boards from already-approved isolated views. Visual-art QA remains separate from manifest QA.
3. **Renderer capability:** current `composition.layers[].tracks` already supports independent x/y/rotation/scale and can animate energy strand sprites with the same sampled motion. **Do not build a second renderer**. A subtle caveat: the tethers are not **reactively bound** to moving shard anchors; use a pure resolver/attachment contract only if a real dynamic edit test proves this insufficient.
4. **Size tradeoff:** A packs significantly smaller, whereas B stores finished pixels and gives controlled artist-authored effects. Continue both through the *same* later visual acceptance; shared source data, two packaging outputs, no second registry or competing source art.
5. **Testing honesty:** geometry/ZIP QA PASS does not mean visual quality or runtime importing PASS. Capture actual side-by-side browser screenshots and import receipts **before approving any pack or uploading to publication allowlist**.
6. **Other agent optimizing repo images:** do not run bulk image-recompression or rewrite existing published sheets as part of this experiment. The new test uses separate PNGs and can later consume the shared image optimization pipeline.

## Next batch acceptance before proceeding to approved Sunblade art

- Import `sunblade-a-v0.1.zip` and `sunblade-b-v0.1.zip` independently into the real local-first builder and examine all 4 states using controls, scrub and actual canvas output.
- Validate the exact ZIPs using `python3 tools/validate_visual_pack.py ...`, then run rendered-state Chromium QA against these ZIPs, using [the existing animation recipe](../../docs/ai/animations/SIDE-SCROLLER-PRODUCTION.md).
- Confirm orientation around the grip, readable wide/small silhouette, more expressive shard motion in close-ups, and consistently positioned energy strands.
- Compare both approaches using the same approved **high-resolution ornate shard references** once P0 source art is qualified. Do not call one visually superior on the simplified 0.1 source.
- Test hand-attachment transitions and nonlinear fragment dynamics; if A's energy connectors separate between keys, extend the **existing** renderer contract narrowly, with deterministic tests, rather than starting another pipeline.
- Record `observation / root cause / correction / test / evidence` as an update to this document and the **existing** AI production guide. Preserve source artwork and stable IDs; PNG optimization is a separate concern.

**Recommended posture:** keep A as a likely runtime scalability candidate, B as the authored art-quality baseline. The winner/hybrid decision stays open until visual qualification, not a matter of preference alone.
