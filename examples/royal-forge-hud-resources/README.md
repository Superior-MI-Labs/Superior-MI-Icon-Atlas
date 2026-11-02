# Royal Forge — HUD Resource Systems (Candidate)
Original illustrated fantasy RPG UI with transparent sprite textures and portable manifests.

## Use
Import this ZIP into the Superior MI Visual Atlas Builder. Open Royal Health Bar by default.
All numeric horizontal bars, vertical vials and globe contents use 0–100 inputs and the existing
Canvas 2D `clip` contract. See `value` in each widget input and `set_value` behavior event.

## Important host semantics
Adaptive quarter hearts accept value in quarter units, max hearts (1..20), and columns (1..20);
the renderer wraps rows and measures the output dynamically. Fixed four-heart historic states remain.
Adaptive pip systems accept charge value, max pip count, and columns (1..20).
Quarter-heart counters encode values 0..16 as explicit compositions and `hp_00`..`hp_16` states.
Segmented pips encode `charge_0`..`charge_6`. Circular meters encode `pct_000`..`pct_100` in
increments of 10. Host applications must select the appropriate state; these are intentionally
not misrepresented as continuously bound numeric radial gauges.

Preview effects are independent 4-frame sequences. Animation does not auto-bind to arbitrary events.
Game input / runtime hit-testing remains the application's responsibility.
