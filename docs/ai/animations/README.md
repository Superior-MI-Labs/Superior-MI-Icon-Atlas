# Recipe: animated icons, characters, objects and effects

**Start from:** [three-frame pulse icon](../../demo/animated-icons.zip) or [robot idle/walk states](../../demo/character-animations.zip). For layered animation, see [glass/weather](../../demo/starter-pack.zip).

**Mandatory before art:** follow [creator preflight](../CREATOR-PREFLIGHT.md). Reconstruct intent from the current request, relevant accessible project history and game requirements; ask any architecture-changing questions and **secure production-blueprint approval**. Review [image-engine workflow](../IMAGE-ENGINE-WORKFLOW.md) for source-art prompting. Do not use the demo's visual style as a substitute for the creator's approved character.

## Shared manifest contract (unchanged)

1. Identify the requested animations and whether each **loops** or is a **one-shot transition**. Avoid inventing extra states.
2. Make complete original frames with matching logical dimensions, pivots and actual alpha. Inspect every crop rather than assuming an AI-generated grid is regular.
3. Each sprite is a `region`; ordered frames and timings form a `sequence`; named alternatives use `state_set`. Use a `composition` for real layer/track reuse, not a duplicated animation state machine. Host games own input and transitions.
4. Preview every state at real size/FPS and all loop seams, run official validations and the [common release checklist](../RELEASE-CHECKLIST.md).

## Character / directional specialization — gated stages

1. **Confirm integration first [HARD STOP].** Determine camera elevation and facing order, game tile scale, pixel resolution, animation names, action count, FPS, collision/foot pivot and required output. Inspect any character templates or host engine code. If the game needs changeable clothing/equipment, agree on **layer separation, attachment and occlusion rules before drawing**. Don't promise a layered character from flattened sprites.
2. **Approve visual identity.** Freeze a canonical character sheet from creator references; map identity details (face, hair, accessories, garment markings), palette, proportion and approved sprite scale. Explain the tradeoff between hand-drawn direction-specific art and a rig/skeleton route; neither is automatically superior for the approved look.
3. **Qualify one small action before multiplication [HARD STOP].** Draw or edit *one canonical facing + one complete action loop* as the proof. An image-engine prompt describes **one exact pose/angle and one allowed change**, not a 208-frame showcase. Keep final sprites isolated from labels, checkerboards and scene backdrops.
4. **Approve canonical facing set [HARD STOP].** Generate all required facing bases at fixed camera/light, same ground anchor and exact outfit identity. Inspect front, side, rear and diagonals for consistent depth/handedness; no mirrored logo or wrong-way stripes.
5. **Block meaningful key poses [HARD STOP].** For each state, storyboard intent, contact and recovery, with readable support leg and actual joint motion. Breathing can be subtle; foot taps need toe/ankle articulation, impatient behavior needs visibly changed head, shoulders, arms or weight. **Whole-sprite warps or color hashes do not prove an action.**
6. **Separate stable loops from changing posture.** A folded-arms impatient *loop* should remain in a coherent base posture. Enter/exit the posture using separate **one-shot** sequences with actual transition artwork if the game needs them. Never hide a hard hands-to-arms-crossed jump in a looping idle.
7. **In-between art.** Draw the intermediate poses or use a vetted pose/render pipeline with character identity preserved. Reject optical-flow blending that produces ghost arms/double heads, silhouette bleeding or shoe/ankle separation. Adjust frame count and per-frame hold timing to match the action; do not duplicate frames to reach an arbitrary count.
8. **Per-frame and adjacency QA.** Measure crop alpha, true baseline and foot pivot, plus separate body/garment anchor consistency when layered. Inspect *every* frame and every adjacent pair, **including final→first**. Check planted foot, shoulder/hip arcs, costume details, overlaid clothing registration and transparency fringes.
9. **Runtime motion QA [HARD STOP].** Play each directional loop at native game scale and 0.5×/1×/2× speeds. Test loop seams, changing states, direction switching and equipment/clothing variations **when required**. Use actual Canvas/host engine rendering, not only an atlas screenshot. Correct one action first before batch expansion.
10. **Pack vetted source art.** Only after visual acceptance, write measured RGBA atlases with stable IDs and the existing manifest contract. Correct pivots from actual game-ground anchors; the previous pilot contained a 2px declared-pivot discrepancy.
11. **Run executable release gates.** Run official manifest validation, strict crop QA when appropriate, request-specific `smi-ai-acceptance/1` checks and [rendered-state Chromium QA](../VISUAL-RENDER-QA.md) against the **final** ZIP. Import in the builder, exercise all states, then export/reimport.
12. **Independent final review.** Preserve QA samples, source/evidence provenance, failures and fixes. Label `NEEDS FIXES` if any required source, visual, technical or rights gate is unverified. Do not ship a production ZIP and call the required repairs “future polish.”

## Production-learning rule

Log **defect → root cause → corrective technique → repeatable test**. Previous character attempts demonstrated that one promotional image does not contain trustworthy evenly spaced sprites; simple rigid segmentation fails at ankles; a consistent 3D rig alone loses hand-painted identity; and optical-flow between unrelated poses produces ghosting. Use these as **negative regression cases** rather than repeating the same attempts.

After the first approved character, test **one genuinely new character** with the procedure and reference prompt strategy frozen. Record first-pass success, retries and interventions before tuning. This is the meaningful one-shot benchmark.

Contract source: [`examples/character-animations/manifest.json`](https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas/blob/main/examples/character-animations/manifest.json).
