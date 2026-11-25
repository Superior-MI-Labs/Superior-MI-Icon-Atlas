# Side-scrolling character production — reusable motion and reference gate

**Scope:** frame-based characters, independently animated equipment/effects, and dialogue portraits. Use only for relevant character work, alongside [Creator preflight](../CREATOR-PREFLIGHT.md), [animation recipe](README.md), [format/API](../FORMAT-API.md) and [release checklist](../RELEASE-CHECKLIST.md).

## P0 — lock actual production artwork before motion

- Assign each reference a role, provenance and rights status. Distinguish approved identity, silhouette, anatomy, garment/equipment geometry and palette from incidental lighting, camera and background. Recover missing source images rather than pretending a historical description substitutes for their pixels.
- Select only the directions, angles, layers and actions required by the actual game. Keep camera, logical size, root/ground baseline, named anchors, handedness, palette and scale consistent. A collage is a concept reference, not a measured model sheet.
- Produce one actual native-resolution master for each independently owned visual track needed by the first slice. Compare side-by-side with approved references at native gameplay and source-art resolution. Obtain explicit approval of the actual production master. Stop on mismatch; do not expand flawed art or replace painterly sprites with procedural approximations.
- Keep source drawings separately inspectable. Preserve approved masters and version candidate revisions independently; do not overwrite a working pack to experiment.

## P1 — qualify the smallest complete working slice

Select the smallest useful action family (for example, a facing, idle/walk loop and one stop transition) and any essential equipment/secondary-motion layer. The creator's requested actions and engine contract determine scope; do not assume all characters need eight directions or independent weapons.

Author real poses with planted contacts, anticipation, follow-through and in-betweens. Never call a translated static silhouette or ghosted interpolation a professional animation. Inspect every frame and adjacent pair, loop seam, native-scale silhouette, contact/anchor continuity and equipment alignment. If the technique fails, fix the source before scaling.

Package measured regions, real sequences, named state sets and reusable compositions in one ZIP using existing schemas. Use explicit per-frame timing where needed. For trimmed frames, declare logical canvas, measured trim offset and normalized pivot as described in the [current format contract](../FORMAT-API.md); do not assume legacy logical-size fields restore trim. Use the shared renderer and actual host anchor convention. Keep image bounds, decode size and memory within documented runtime limits.

Execute the official acceptance command, applicable browser scenarios and manual native-scale inspection. Verify first/middle/last frames, loop and transitions, each declared layer and state, and round-trip import/export. A motion-plan validation PASS is not art or playback approval. A creator can approve a technical preview separately from final artwork; rejected visual masters cannot qualify as finished.

## P2 onward — expand coherent action families

Expand only after the approved slice works. Reuse frame and asset IDs, state families and layer contracts. Add traversal, combat, expression and effect families only when requested. Track ownership of body/root, equipment, secondary motion, portraits and effects; keep world/local-space choices explicit. Validate contacts, grip alignment, phase changes, authored transitions, interruption and fallback behavior with the real host if applicable. Record actual failures and corrections.

The existing `state_set` selects visuals; it is not a conditional gameplay state machine. [Preview input profiles](PREVIEW-CONTROLS.md) offer visual audition, not collision, hitboxes, damage or game simulation. A richer controller sidecar is a proposal, not supported manifest functionality. Do not invent fields or duplicate frame data. If a real capability gap exists, compare solutions and design/test the shared contract before implementing anything.

## Qualification and handoff

Follow the [release checklist](../RELEASE-CHECKLIST.md) for evidence and publication authorization. Include real source references, exact ZIP hash, approved masters, named state/clip inventory, contact sheets, native-size playback/transition evidence and remaining gaps. A test fixture, plan, draft and approved release are distinct.

## Project-specific case study — Sky

Only for Sky work, load the [Sky production history](SKY-PRODUCTION-HISTORY.md) and the [current project plan](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/production/sky-blue-eyes/plan.json). The [creator's art rejection audit](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/production/sky-blue-eyes/ART-FIDELITY-AUDIT-2026-11-02.md) remains binding for the rejected assets: do not reuse the rejected procedural masters or extend their clip counts. Requalify real artwork against the approved identity before bulk motion. The historical document retains all project decisions, rejected candidates and planned gates; it must not override current runtime contracts. For that project run `python3 tools/validate_animation_plan.py production/sky-blue-eyes/plan.json` as an additional plan check.
