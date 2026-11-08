# Portable input profiles for animation previews

One authored `smi-visual-pack/1` may include multiple optional `preview_profiles`.
Each profile references an already-declared asset, not a copy of its animations.
The existing `region`, `sequence`, `state_set`, `composition`, and
`behavior.on` definitions remain authoritative.

Minimal platformer-style state audition:

```json
{
  "schema": "smi-preview-controls/1",
  "id": "example.robot.platformer",
  "name": "Platformer controls",
  "asset": "example.robot.states",
  "neutral": {"state": "idle"},
  "actions": {
    "move": {"mode": "hold", "target": {"state": "walk"}}
  },
  "bindings": [
    {"device": "keyboard", "code": "ArrowRight", "action": "move"},
    {"device": "gamepad_button", "button": 15, "action": "move"}
  ]
}
```

To make an isometric or fighting-game profile, add different **state keys**
or named behavior events and bind different logical actions to them. The
profile does not define movement vectors, physics, attacks, hitboxes or
combination rules. Those belong to the target game's runtime. Do not hardcode
genre labels or controls in the renderer.

For a composition that drives a state_set through `state_from_input`,
a profile action targets an existing `behavior.on` **event**, for example:

```json
"actions": {
  "guard": {"mode": "hold", "target": {"event": "enter_guard"}},
  "attack": {"mode": "tap", "target": {"event": "light_attack"}}
},
"neutral": {"event": "return_to_neutral"}
```

All referenced events must be declared in the composition's existing
`behavior.on`. A `tap` action does not automatically revert to idle: the
actual animation engine decides if/when to transition on completion.

While Test Drive is active, keyboard events are handled only on the focused
preview stage. The first available gamepad's declared digital buttons are
handled by the same pure input dispatcher. Mouse/touch direct manipulation
continues to use the existing `behavior` and `position_from_input` contracts.
No executable code is allowed in imported manifests.

Profiles are validated during import and export. Multi-pack collections retain
profiles alongside asset definitions; exporting an asset preserves profiles
that reference that asset. The Schema intentionally limits profiles, actions,
and bindings to bounded sizes. The Builder offers generic state cycling for
assets that have no authored profile, but never assumes their genre or controls.
