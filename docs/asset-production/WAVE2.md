# Fantasy RPG HUD Wave 2 — Production specification

**Status:** plan / work in progress, not a public art release. Requires the approved Wave 1 design language and pixel-accurate geometry.

## Guiding architecture

Wave 2 is an additive `smi-visual-pack/1` collection. Use exactly four existing asset kinds (`region`, `sequence`, `composition`, `state_set`), and the existing typed `behavior` contract, `slots` and `presets` only when useful. No second behavior interpreter, private registry, extra asset kind, custom script inside JSON, or duplicated runtime/authoring manifests.

The browser currently provides generated controls for declared values/events. **Direct on-canvas pointer hit-testing, keyboard navigation and gamepad input remain a host-adapter capability**, not something these images or the existing manifest magically implement. Define these capabilities in the manifest; implement one shared host adapter separately after writing role-independent interaction tests.

## First production families

| Family | Source parts | Testable assembled examples |
| --- | ---: | --- |
| Ornate primary/secondary/icon buttons | 12 | Default, hover, pressed, disabled state sets |
| Toggles, checkboxes, radio controls | 10 | On/off and selected states |
| Tab headers and navigation arrows | 8 | Selected/hover/disabled |
| Inventory slots and equipment sockets | 10 | Empty/hover/selected/locked, rarity accents |
| Ability / hotbar sockets | 8 | Ready, cooldown, activated |
| Status indicators, counters and pips | 8 | Spent, ready, danger, warning |
| Panel and tooltip trim parts | 10 | Resize/nine-slice without corner distortion |
| Small notification / quest badges | 8 | Default, attention, disabled |
| **Planned** | **74** | Interactive state-family sample collection |

Do not generate or advertise the full 74 as complete until they have real isolated images, accurate region rectangles, manifest references and QA.

## Required interaction contract

- `inputs`: typed native values with authoritative min/max/default and optional step
- `behavior`: supported roles/events/outputs; no arbitrary script or evaluation
- `state_set`: visual appearance variants; hover/pressed/disabled not merged into one PNG
- `composition`: ordered layers; no decorative occlusion of values or icons
- `nine_slice_px`: authored only with physically valid corner/edge margins
- `interfaces/implements/slots/presets`: versioned compatibility, explicitly approved replacement options, no tag-based guessing

## Mandatory visual and semantic QA

1. Creator brief → choose the task-specific recipe and preserve intent.
2. Generate each reusable part independently and inspect it **before** exact deterministic atlas packing.
3. Confirm alpha, source dimensions, original drawing, bounds, no overlapping neighbor pixels, and exact rectangles.
4. Test every declared state at actual preview scale; hover, pressed, selected and disabled must visibly differ as intended.
5. Test value-controlled components at 0/1/5/10/25/50/75/90/99/100; make the visual proportion truthful.
6. Test button/toggle event outputs and manifest state transitions separately from render appearance.
7. Verify compatible slot alternatives without assuming matching labels imply matching dimensions.
8. Run official ZIP validation, strict crop QA, request-specific acceptance and Chromium render-state scenarios with negative assertions.
9. Export/reimport the **final** ZIP, verify pixel equivalence for the same state/time/input and record the evidence.
10. Publish only if art direction, tests, source provenance and license are approved; otherwise tag as candidate.

Keep raw art/source scripts outside the runtime `examples/` pack; source is under `production/`. Use the existing site builder to generate public ZIP and featured listing.
