# Sky — Animation Transition Test Pack v0.2

This is a **prototype**, not a production-approved Sky animation release. It uses original generated frames from the earlier Sky GIF explorations. The artwork is right-facing and predominantly transparent, but inconsistent source poses and alpha-color fringing are still visible.

## Open the interactive test

Unzip the full package and open `preview.html` in a browser. If your browser restricts local file access, open a terminal in this folder and run `python3 -m http.server 8000`, then visit `http://localhost:8000/preview.html`.

Use **A/D** or the arrow keys to move, **Shift** to run, **Space** to jump, **J** for a fully linked three-stage charge/slash/orb combo, **K** to hold combat guard, **H** to test the health meter, **P** to pause, and **I** for the inventory overlay. Touch buttons are present for simple mobile use.

Jump is controlled by a small illustrative physics runner, not by assuming a full jump is a single GIF. State transitions are:

`idle → jump_takeoff → jump_rise → jump_apex → jump_fall → jump_land → idle`

Attack-chain transitions are:

`idle → attack_charge → attack_slash → attack_orb → idle`

The **run/walk/idle/guard** clips are loops; other clips are one-shots. The preview owns height, velocity and collision detection while animations supply visuals. Jump/fall thresholds and action order are defined in `scenario.json`. The playable page embeds a generated snapshot of both JSON definitions so it works offline. Do not edit the HTML as a separate authoritative source.

## Import into Visual Atlas

Upload the separately provided `Sky_Animation_States_Builder_Import_v1.zip` directly into the [Visual Atlas Builder](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/builder.html). It contains the canonical `smi-visual-pack/1` manifest, source PNG atlas sheets, named sequences and a state-set asset. In the Builder, select **Sky prototype animation states** and use the Preview Profile to audition individual states.

This imported state-set does **not** include the prototype world physics/combo implementation. `scenario.json` is intentionally a separate experimental companion contract. We have not changed the canonical Atlas schema to include world simulation rules.

## Source frames, animation clips and QA

- `gifs/` contains the split looping and one-shot clips, plus full jump and attack showcases.
- `textures/` contains 13 RGBA sheets. Frame regions all refer back to these canonical textures; the individual GIFs are derived previews, not extra editable sources of truth.
- `manifest.json` is the authoritative animation asset graph.
- `scenario.json` describes the experimental transitions and miniature world configuration.
- `review/clip_endpoints.jpg` shows the first and last frame of each animation. `review/playground_static_reference.png` illustrates the intended world composition.
- `qa-report.json` documents quantitative clip discontinuities and source problems.
- `validate_pack.py` checks asset references, texture dimensions, hashes, GIF transparency and playback flags.

**Important limitations:** The fall and landing clips now have extra interpolated intermediate poses and aligned endpoints. These are prototype compositing solutions, not independent hand-authored animation. Some inbetween frames ghost and still need replacement for production. The attack clips also have seam changes and character appearance drift. We deliberately excluded a newly generated golden-arc GIF because its background was entirely opaque. The remaining source frames can have red/yellow alpha-edge artifacts. Dedicated fall and landing animation art and artistic review are needed before game production use.

The owner authorized public release explicitly labeled as **Experimental / Prototyping**. A site listing is separate from this portable ZIP; local QA does not establish production readiness.
## Public experimental release

Publicly discoverable as **Prototype / Experimental — visual QA pending**. Source license: prototype evaluation only, not CC0; no commercial use rights are granted. The atlas textures are original-resolution authored sources. The deployed showcase is derived from this manifest plus scenario.json and the generated ZIP.

[Play prototype](https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/sky-prototype.html)
