# Sky — Batch 04 swordless body motion study

**Status: REAL FRAME/ATLAS ARTIFACT · LOCAL SOURCE QA PASS · ART-STYLE QUALITY HOLD · EXACT BUILDER IMPORT NOT TESTED.**

This batch addresses a genuine absence after [Batch 03 drawn Sunblade](SUNBLADE-BATCH-03-RECEIPT.md): no complete swordless Sky character motion frames had been delivered. Nine independent body motions are now authored as **offline vector drawings**. Their style is simplified and **materially below the ornate, textured, user-approved character**; they are technical, not publishable game sprites.

The user wants substantial batched progress and no more general concepting. This motion study is a reusable **working manifest/frame fixture**, not a reason to start another poster/reference round.

## Artifact handoff, deliberately not published

The conversation archive `Sky-Animation-Production-Batch-04.zip` contains the complete source study, exact original SVG frame drawings and RGBA PNG exports, rebuilding/QA scripts, preview GIFs and the **independent** `sky-body-motion-study-v0.1.zip` import pack. The prior Sunblade 0.1 and FX 0.2 import ZIPs remain separate, unchanged. No binaries were added to this public repo or publication allowlist.

| Measured result | Actual |
|---|---:|
| Swordless full-body RGBA source frames | **92** |
| Animations / sequences | **9** |
| Standalone selectors | **2** (nine clip preview; normal/low HP idle preview) |
| Assets in manifest | **103** (92 regions + 9 sequences + 2 state selectors) |
| Atlases | **4**, maximum dimension 2048 |
| Source canvas | **480 × 512** |
| Playback | 16 authored FPS |
| Candidate import ZIP | **6,026,278 bytes** |
| Decoded packed RGBA | **49,991,680 bytes** |
| Naive untrimmed RGBA | **90,439,680 bytes** |
| Decoded memory saved | **44.7%** |
| Lossless source-frame reconstruction | **92/92 byte-exact PASS** |
| Actual Visual Atlas Builder browser import | **NOT TESTED** |
| High-detail character style / motion approval | **FAIL / HOLD** |
| Public asset release | **NO** |

**Nine clips:** `idle.relaxed` (12 loop), `idle.low` (12 loop), `walk.loop` (12 loop), `run.loop` (12 loop), `run.stop` (8 one-shot), `jump.rise` (8 one-shot), `jump.land` (8 one-shot), `martial.claw_01` (12 one-shot), and `defend.parry` (8 one-shot).

The `sky.body.idle.health_preview` state selector exposes **normal** and **low**. Host gameplay still owns the health boundary, normal **>36%** and low **<=36%**. This threshold was not added as a proprietary conditional interpreter in the Visual Atlas manifest.

## Actual observations / corrective qualification

1. **Source creation issue:** the image-generation path again produced a fake ornate **production delivery poster** with tables and tiny frames rather than isolated image-source frames. It is NOT part of the pack and NONE of its claimed numbers describe delivered assets. **Never treat a generated presentation board as source sprite data.**
2. **Alternative validated:** independently authored SVG poses have separate hip/arm/leg/tail geometry and clear nonidentical frames, then export to individual straight-alpha PNG files. These are not a simple global translation or image warp of the approved reference. **But** the simplified vector drawing style falls far below the canonical costume/feather/anatomy detail, and the tails appear too schematic. That is a **visual failure** relative to the requested premium painted-animation quality. No amount of numeric manifest validation overrides it.
3. **Manifest:** reuses `region` + `sequence` + `state_set`, with clip-specific one-shot vs loop semantics and shared pivot/logical-canvas trim. There is no second gameplay state machine, extra controller schema, sword baked into character frames, or physical scabbard.
4. **Lossless graphics:** 92 source-frame RGBA buffers reconstruct exactly from cropped atlas positions, including hidden RGB values. Four pages save 44.7% decoded RGBA memory vs untrimmed cells in this measured example. This is **not** a universal asset-size result. The actual ZIP still needs Visual Atlas Builder browser import.
5. **Role isolation:** the high-detail swordless reference drawing is included *only for art comparison*; it is not transformed into fake run cycles. The previous separately drawn sword pack and independent effects pack are included as unchanged companion ZIPs in the handoff, with no implicit cross-pack references. A review-only GIF demonstrates them together but is not a game-engine test.

## Production quality gates before promoting body sprites

- Use the detailed original hooded, veiled desert-wanderer artwork and approved low hip-rooted **three feathered tails** as the **identity standard**. Restore fabric texture, feline anatomy, patterned wraps and the subtle cosmic eyes. No wings, no physical sword attached to his back.
- Commission individual **high-detail, orthographic-ish three-quarter swordless key poses** for idle/run/contact/recovery, keeping the same camera and foot baseline. Do not try to salvage the vector proxy by upscaling or applying a filter.
- Draw true in-betweens frame-by-frame and inspect adjacent pairs, three tail roots, scarf/robe cloth and grounded foot contacts. Exact source-to-atlas byte QA continues to apply but is only the technical gate.
- Test all nine sequences and both preview selectors from the **exact ZIP** in a real browser using the Visual Atlas Builder, and record screenshots and failures before release.
- Continue to preserve the existing 315-clip backlog; 92 actual frames are **not** 92 finished approved character sprites. No public publication until quality and import gates both pass.

No existing published images are modified: image optimization is assigned to another agent.

**Recorded status:** motion pipeline qualification = PASS locally; art quality = HOLD; real Builder import = NOT TESTED; user approval = PENDING.
