# Sky Blue Eyes — Batch 04: swordless body motion (candidate)

**Status: real source PNG/manifest pack, local exact-pixel QA PASS; visual style unapproved and live Builder import NOT TESTED.** This is a **simplified vector-drawn motion study**, not the approved detailed painterly look. It is neither a final character sprite set nor a game controller.

## Handoff files (conversation, not public GitHub)

- `Sky-Animation-Production-Batch-04.zip` — 36,170,784-byte self-contained source handoff with **92 individual 640×512 SVG and transparent RGBA PNG pose drawings**, offline frame scrubber, 9 GIFs and two independent-character/weapon scene studies, alpha-exact packer, validator, and receipts.
- `sky-body-grounded-v0.1.zip` — 7,025,327-byte **standalone** Visual Atlas v1 import: **92 regions, 9 sequences, 2 state selectors, 4 atlas pages** (103 addressable assets).
- Included **unchanged**: `sky-sunblade-drawn-v0.1.zip` (seven complete-sword sequences) and `sky-fx-foundation-v0.2.zip` (20 FX sequences). Each ZIP imports independently; there are no hidden cross-pack references.
- The public repository and `publications.json` are **not** changed to include these candidate images, and no previously published PNG is recompressed. Another agent owns existing-repository image optimization.

The binary files live in the current conversation handoff, **not in the repo**. Future agents must obtain the full archive before evaluating frame pixels; passing repo planning tests never means actual ZIP/browser QA passed.

## Nine real body clips, all mapped to the existing 315-clip inventory

| Animation | Frames | Playback | Exact inventory ID |
|---|---:|---|---|
| Normal relaxed idle | 12 | loop | `sky.body.idle.relaxed` |
| Low-health idle | 12 | loop | `sky.body.low_health.idle.loop` |
| Walk | 12 | loop | `sky.body.walk_run.walk.loop` |
| Run | 12 | loop | `sky.body.walk_run.run.loop` |
| Run stop | 8 | once | `sky.body.walk_run.run.stop` |
| Jump rise | 8 | once | `sky.body.jump.jump.rise` |
| Soft landing | 8 | once | `sky.body.jump.jump.land.soft` |
| Martial claw | 12 | once | `sky.body.martial_ground.claw.light_01` |
| Martial parry | 8 | once | `sky.body.defense.parry.start` |

**Art FPS:** 16. The visual-pack `state_set` allows manual selection, but the **game host** must implement normal health >36%, low health <=36%, death separately. Walking velocity, actual airborne motion, sword hilt sockets, collision, combat timing, legal transitions, buffered inputs and right-stick control are **not implemented** by these PNG animations.

## Exact local verification record

- 92/92 frames have unique nonblank content and are **unclipped**, with positive padding to all logical-canvas boundaries.
- **92/92 exact RGBA source reconstructions**, including all invisible RGB bytes, using `rect_px` + `trim_offset_px` on a 640×512 logical canvas.
- ZIP CRC/member/size integrity, 9 sequences, 2 selector references, 103 stable unique asset IDs, 4 declared texture dimensions, and no unlisted asset kinds PASS.
- Numeric seam diagnostics pass for relaxed idle, low-health idle, walk and run (visual frame quality remains unapproved).
- Atlas page dimensions: **2016×2048, 2040×2040, 2008×2032, 312×408**. **49,991,680 bytes** of decoded RGBA instead of **120,586,240 bytes** in untrimmed 92×640×512 storage: **58.5% measured memory reduction**.
- The exact new pack was **NOT run through the real Visual Atlas Builder browser import**, and there is **NO artist/customer approval** or commercial game-engine test.

## New root-cause lessons passed to production agents

1. **Canvas bounds matter before packing.** An earlier 384×512 study cut tail, claw and parry silhouettes at the left/right source boundary. Moving the full character drawing to a **640×512 stable logical canvas** and offsetting all shapes by a consistent 130 px preserved entire strokes. All 92 alpha bounds must remain strictly *inside* the canvas; blindly trimming already-clipped pixels would conceal the bug.
2. **Use one authoritative animation inventory** for stable clip IDs. Nine clips are a partial implementation of 315 planned IDs, **not 315 shipped assets**. Each body clip is swordless, no wings; original approved clothing/eye/tail silhouette is reference intent. Do not restart full concepting.
3. **Three hip-rooted tails remain attached in the body drawing**, but the illustration is still simplified and spiky compared with the approved feathered references. This is a **visual FAIL/HOLD**, even though the RGBA checks passed. Refine the art before multiplying this style across hundreds of actions.
4. **Independent actor integration:** the two review-only GIFs composite complete PNG sequences from separate body and sword ZIPs. They show an art-direction relationship, not verified world-space follow, hilt hand-lock, combat legality, or cross-pack import resolution. Do not bake sword pixels into character frames to simulate an attachment.
5. **Keep compiled PNG atlases derived** and retain SVG+PNG source. Alpha-trim with direct paste, exact source reconstruction, unique IDs, deterministic packaging; keep a **real browser-import gate** and creator style review before publication.

## Next source-art priority

Before producing dozens more body actions, bring the **actual 9-clip body source** closer to the approved painterly 3/4 reference: detailed hood/veil, orbital blue/teal pupil, visible three **feathered** low hip tails, richer wraps and cloth depth, no sword. Check head/foot anchors, contact phases, planted foot slipping, and run-stop handoff. Only after visual qualification, extend with `run.start`, `jump.prepare`, `jump.fall`, dodge/roll, held attack overlays, sword grab and combo sync.

**Outcome:** meaningful validated asset production; not production-final art.
