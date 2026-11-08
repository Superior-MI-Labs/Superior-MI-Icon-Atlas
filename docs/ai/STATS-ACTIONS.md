# Stat and action experiments

A `smi-visual-pack/1` may include optional `stat_profiles`; each references
one existing composition asset. Statistics are authored once and projected to
existing numeric composition inputs. The renderer is unchanged. This is a
small deterministic preview runtime, not a full game engine.

```json
{
  "stat_profiles": [{
    "schema": "smi-stat-profile/1",
    "id": "demo.actor.stamina",
    "name": "Stamina laboratory",
    "asset": "demo.actor",
    "stats": {"stamina": {"min": 0, "max": 100, "initial": 60}},
    "actions": {
      "dash": {"costs": {"stamina": 20}, "emit": "dash"},
      "recover": {"deltas": {"stamina": 25}, "emit": "recover"}
    },
    "bindings": [{"stat": "stamina", "input": "stamina"}]
  }]
}
```

`demo.actor` must be a composition declaring numeric `inputs.stamina` with
a range covering the stat range. Optional `emit` names must exist in that
composition's `behavior.on`. Those events can already change an animation
enum through a `state_from_input` layer; nothing duplicates animation frames.

**Rules:** All resource costs are checked first. If any cost would take a stat
below its minimum, the complete action is rejected, no values change and no
events fire. On success, costs subtract, deltas add, all results clamp to bounds,
and optional visual events dispatch through the existing interaction core.
Direct edits in the stat inspector or bound HUD slider update the same active
simulation state. Defaults/definitions are never mutated by preview activity.

**Examples:** `examples/interactive-hud/manifest.json` demonstrates a stamina-
like energy meter, while `examples/character-animations/manifest.json` uses
stamina costs to trigger existing robot animation events. The derived demo ZIPs
are private fixtures; importing them never publishes them to the public catalog.

**Not implemented:** Formula-based derived statistics, timed effects, modifiers,
inventory, multi-actor interactions, world physics or combat resolution. Those
will need separate versioned capabilities and scenario qualification, not
genre-specific code in the core.
