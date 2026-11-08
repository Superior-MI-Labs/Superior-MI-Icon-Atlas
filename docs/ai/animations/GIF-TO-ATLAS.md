# GIF → Canonical Visual Atlas sequence

A GIF is a source animation, **not** a texture sheet or game-runtime format.

The import tool is intentionally two-stage:

1. Run \`python3 tools/import_gif.py my-clip.gif --out /tmp/clip-review\`.
   Review \`frames-review.png\` and \`qa-report.json\`. It inspects compositing,
   per-frame delays, transparency, duplicate frames and loop-seam change.
2. After actual human frame-by-frame approval, run
   \`python3 tools/import_gif.py my-clip.gif --out /tmp/clip-review --pack /tmp/clip.zip --id my.character.idle --license CC0-1.0 --approve-visual\`.

The ZIP uses the existing \`smi-visual-pack/1\` contract:
RGBA PNG atlases, exact pixel frame regions and one timed \`sequence\`. A 4-column
grid is used where possible; oversized frame sets split into multiple texture
sheets. Logical canvases and relative registration are preserved, with default
bottom-center pivots that creators should visually verify. No new asset kinds,
builders, combat logic or runtime API are introduced.

The tool blocks fully opaque frames and frames without actual motion. It reports,
but cannot automatically certify, frame continuity, anatomy, color fidelity,
foot contacts, or character consistency. Never claim that running or blocking
motion is correct from structural checks alone. These outputs are private
preview candidates; they are not automatically added to the public catalog.
