# Sky Blue Eyes — dual-stick combat and interaction study

**Status: PROPOSED HOST GAMEPLAY CONTRACT, NOT IMPLEMENTED IN VISUAL ATLAS.** The authoritative machine-readable action IDs, defaults, analog behavior, and keyboard/controller parity are in [controls-proposal.json](controls-proposal.json). Do not copy an independent keybinding registry into another manifest or the art-production instructions.

## Character, sword, and controller responsibilities

Sky's body animation contains **no sword pixels**. The Shattered Sunblade is a persistent autonomous actor: an ornate cloth-wrapped relic whose visible fragments translate and rotate independently while energy tethers deform between them. Its normal rest is `back_hover`, beside Sky's back/right shoulder, **not sheathed**.

- **Floating mode:** Left stick moves Sky; he can punch, sweep, kick and launch with martial-arts attacks. Right stick directs the independent sword; right trigger sends strikes at long range, orbit control, anchors or a charged vortex. A sword-hop from an anchored blade is a future unlocked host mechanic, not a drawable platform baked into the sprite.
- **Held mode:** A deliberate grab/lock transition attaches the hilt to Sky's animated hand. Left stick continues locomotion, right stick selects attack direction/throw aim, and body attacks become committed, higher-damage held-sword combinations. Hilt is locked; shards continue to flex and lag under energy cohesion.
- **Away/anchored mode:** Sky continues martial movement while the blade remains in world space. Its aim/command controller persists until recall, release, or a valid attachment. Never teleport the sword to the back in response to an unrelated animation transition.

**Damage/reach identity:** martial arts is the agile combo glue, floating sword offers longer-range control at lower committed damage, held sword offers shorter-range higher-damage commitment. Gameplay balance numbers remain provisional.

## Dual-stick gamepad and keyboard/mouse parity

Use standard gamepad face controls for jump/light/heavy/dodge, left shoulder for guard/parry, right shoulder for attachment/release/recall, right trigger for autonomous sword commands or held throws, left trigger for precision focus, and directional controls for aspects/techniques. L3 supports deliberate world interaction; R3 anchors the blade. Start/Menu and Select/View open pause and map.

Left stick / keyboard WASD moves Sky. Right stick / mouse position aims or steers the blade. The **same semantic commands** work in either input modality. Individual assignments must be remappable; the JSON contract is a starting layout, not a required commercial game's default.

### Controller ergonomics and accessibility

Holding the right stick while pressing face buttons can require the same thumb to be in two places. Avoid mandatory simultaneous gestures:

- Remember the last valid aim direction briefly after right-stick release (proposed 400 ms); preview targeting and aim-assist are optional.
- `sword_vortex`: holding RT (or F) charges the effect. A stick-circle gesture may alter the shape/direction but must never be required to activate it. Resolve short RT release (cast) versus sustained hold (vortex) **exactly once**; do not cast and charge concurrently.
- Arrow/circle/charge and aspect effects should be feedback layers, not separate mandatory input gestures.
- Keep hand-grab prompts, combo windows, and precise parry feedback readable without vibration. Vibration is optional and can be disabled; don't use it as the only information channel.
- Support gamepad deadzones, aim sensitivity, input buffering, remapping, accessible aim retention, and reduced screen-shake.

## Example combo vocabulary

The JSON controller proposal covers semantic sequences, not sprite-specific button macros. Prototype:

1. **Claw → crosscut:** light martial strike, remote blade cast, heavy finisher. Body and sword operate on parallel tracks.
2. **Palm launcher → air follow-up:** rapid light/light/heavy, jump cancel when host authorizes, cast through the rising enemy.
3. **Blade-hop:** anchor sword in world space, then jump off a valid contact surface if the traversal skill is unlocked.
4. **Vortex:** hold command in floating mode to spin fragmented blade into a remote controllable vortex, with a button/hold activation alternative to circular-stick gestures.
5. **Grab → melee → throw → recall:** lock the hilt at `sword_grab_lock`; play committed sword attack; throw in last valid aim; request autonomous return. Preserve exact fragment IDs and no teleport on attach/detach.

## What an animation asset actually needs

At this phase, **do not extend the strict `smi-visual-pack/1` schema**. Continue using `region`, `sequence`, `state_set`, and `composition` for source art, clips and visual effects.

The game or future optional controller adapter can read semantic events:

`sword_grab_start` → `sword_grab_lock` → held slash → `sword_release_start` → `sword_release_end`.

A future implementation may sample attachment transforms from qualified character pose anchors and drive fragment-local motion and tether endpoint interpolation. That requires an isolated proof and tests. Atlas should preview these changes as external parameter/state inputs; it must not independently decide damage, hitboxes, invulnerability, jump physics, enemy reactions or puzzle unlocks.

## Reference quality: latest creator approval

The approved image for the **hero stance** is a *shallow right-facing three-quarter perspective*, showing believable torso depth rather than an absolutely flattened 90° side view. The creator explicitly requested that the upper two tails of the large isolated study be **lowered**. All three feathered tails must share lower-back/hip/pelvic roots, fan backward and slightly downward, and not appear to grow from the upper back or shoulder.

The user-provided cropped reference `image(20261102-135059).png` documents angle and root placement. It is **not a replacement for the full-resolution approved costume original** and not a certified alpha-sprite source. The eight-view construction check still includes a strict pure side for anatomy verification, but the displayed **hero master** should have more three-dimensional perspective. Record the correction and user approval without falsely marking an uncorrected generated image as production-qualified.

Consult [P0 review](P0-REVIEW.md) and the [reusable agent side-scroller guide](../../docs/ai/animations/SIDE-SCROLLER-PRODUCTION.md). **An AI-generated decorative reference board, however attractive, is not accepted as an individual frame, a consistent eight-view turnaround, or proof of animation.**
