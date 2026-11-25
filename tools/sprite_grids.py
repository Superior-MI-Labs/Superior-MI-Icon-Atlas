"""Build exact transparent sprite-sheet layout references (stdlib only)."""
from pathlib import Path
import struct
import zlib
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

# Columns, rows, square cell pitch in pixels. This is the single layout source.
LAYOUTS = (
    (2, 2, 512), (3, 2, 512), (4, 2, 512),
    (4, 4, 256), (6, 4, 256), (8, 4, 256),
    (5, 5, 256), (5, 3, 320), (3, 5, 320),
    (6, 6, 256), (12, 4, 192),
)
LINE = bytes((128, 128, 128, 255))
CLEAR = bytes(4)


def _chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))


def _line_at(position, extent, pitch):
    # Two pixels at every division, including both outer edges.
    return position < 2 or position >= extent - 2 or position % pitch in (0, pitch - 1)


def grid_png(columns, rows, pitch):
    width, height = columns * pitch, rows * pitch
    horizontal = b"\x00" + LINE * width
    vertical = b"\x00" + b"".join(
        LINE if _line_at(x, width, pitch) else CLEAR for x in range(width)
    )
    pixels = b"".join(horizontal if _line_at(y, height, pitch) else vertical
                      for y in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", header)
            + _chunk(b"IDAT", zlib.compress(pixels, 9)) + _chunk(b"IEND", b""))


def build_sprite_grids(templates):
    """Publish references and a deterministic ZIP beside existing authoring grids."""
    folder = Path(templates) / "sprite-grids"
    folder.mkdir(parents=True, exist_ok=True)
    table = []
    with ZipFile(Path(templates) / "sprite-grid-references.zip", "w") as archive:
        for columns, rows, pitch in LAYOUTS:
            name = f"grid-{columns}x{rows}-{pitch}px.png"
            data = grid_png(columns, rows, pitch)
            (folder / name).write_bytes(data)
            entry = ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, data)
            table.append(
                f'<tr><td>{columns} × {rows}</td><td>{columns * rows}</td>'
                f'<td>{columns * pitch} × {rows * pitch}</td><td>{pitch} × {pitch}</td>'
                f'<td><a href="{name}">PNG</a></td></tr>'
            )
    page = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sprite sheet reference grids | Visual Atlas</title>
<link rel="stylesheet" href="../../styles.css">
<style>main{max-width:850px;margin:auto;padding:24px}table{width:100%;border-collapse:collapse}th,td{padding:10px;text-align:left;border-bottom:1px solid var(--border)}a{color:inherit}</style>
</head><body><main><p><a href="../../ai-guide.html">AI Creation Guide</a></p>
<h1>Sprite sheet reference grids</h1>
<p>Transparent PNG layout references with exact square cell pitch and thin gray guides. Columns × rows. Choose a grid based on subject detail and the image engine's actual output size. Use one as a layout reference; final source artwork must have clean transparent spacing. Measure returned pixels independently.</p>
<p><a href="../sprite-grid-references.zip" download>Download all PNG grids (ZIP)</a> · <a href="../../ai/IMAGE-ENGINE-WORKFLOW.md">Source artwork workflow</a></p>
<table><thead><tr><th>Layout</th><th>Cells</th><th>Canvas (px)</th><th>Cell (px)</th><th>Reference</th></tr></thead><tbody>
""" + "\n".join(table) + "</tbody></table></main></body></html>\n"
    (folder / "index.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("templates", type=Path)
    build_sprite_grids(parser.parse_args().templates)
