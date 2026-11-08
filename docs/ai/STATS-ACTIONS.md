# Stat and action experiments

The optional `stat_profiles` field in `smi-visual-pack/1` references a
composition. `smi-stat-profile/1` is the authoritative set of base stats,
derived calculations, timed modifiers and actions. No scripts or arbitrary
expressions execute from imported manifests.

## Canonical profile

```json
{
  "schema": "smi-stat-profile/1",
  "id": "demo.actor.stamina",
  "asset": "demo.actor",
  "stats": {
    "stamina": {"min": 0, "max": 100, "initial": 60},
    "speed": {"min": 0, "max": 10, "initial": 4}
  },
  "derived": {
    "mobility": {
      "min": 0, "max": 40, "offset": 0,
      "terms": [{"stat": "speed", "coefficient": 2},
                {"stat": "stamina", "coefficient": 0.05}]
    }
  },
  "effects": {
    "haste": {
      "duration_ms": 3000,
      "modifiers": [{"stat": "speed", "multiply": 1.5}]
    }
  },
  "actions": {
    "dash": {"costs": {"stamina": 20}, "emit": "dash"},
    "haste": {"costs": {"stamina": 10}, "activate": "haste"},
    "dispel": {"remove": "haste"}
  },
  "bindings": [
    {"stat": "stamina", "input": "stamina"},
    {"stat": "mobility", "input": "mobility"}
  ]
}
```

## One source of truth

- **Base** stats are bounded values. Only these can be edited directly or
  changed by action costs/deltas.
- **Effective** stats are computed from base values and active effects.
  Modifiers always combine as `(base + sum(add)) × product(multiply)`, then
  clamp to base bounds. Their order is deterministic.
- **Derived** stats are read-only bounded linear formulas over effective base
  stats: `clamp(offset + sum(coefficient × effective stat), min, max)`.
  The formula cannot reference another derived stat, so there are no cycles.
- **Bindings** project effective or derived values to existing numeric
  composition inputs. Computed input controls are read-only in the Builder.
  Editing a base-bound preview control sets the base stat; effects apply
  afterwards. The renderer never owns stat state.
- **Actions** atomically check all costs before mutating base values. On
  rejection they change nothing, activate no effect and emit no visual event.
  Successful actions can activate (or refresh) one effect, remove one effect,
  and/or send an existing `behavior.on` event for animation-state changes.
- **Time** moves only when explicitly advanced via `advance(ms)` or the
  Builder's simulation-step control. Each step is a bounded integer
  0–60,000 ms. Reapplication restarts an effect's duration and does not stack
  duplicate copies. Expiration removes modifiers, preserving base values.
  Animation preview playback and stat simulation time are separate.
- **Reset/export** returns to authored defaults. Export carries definitions,
  not live experimental values or active timers.

## Test cases

`examples/interactive-hud` demonstrates resource costs, damage,
recovery, derived readiness and a temporary energy modifier.
`examples/character-animations` demonstrates stamina, derived mobility,
a temporary speed multiplier and animation transitions on existing robot
states. Both are private fixtures—not automatically published to the gallery.

Validation runs through JSON Schema, semantic cross-reference checks, pure
Node tests and real-browser render/input/ZIP round-trip tests.

## Boundaries

This is a bounded preview evaluator, not gameplay physics, a scripting engine,
a combat simulator or a persistent save system. The next multi-asset/scene
workbench should consume the same stat contract; it must not reimplement it.
