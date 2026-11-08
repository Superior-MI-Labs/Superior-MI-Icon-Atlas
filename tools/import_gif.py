#!/usr/bin/env python3
"""Inspect GIF frame quality before exporting a canonical Visual Atlas sequence.

Usage:
  python3 tools/import_gif.py input.gif --out /tmp/sky-qa
  python3 tools/import_gif.py input.gif --out /tmp/sky-qa --pack /tmp/sky.zip \
      --id smi.sky.idle --license CC0-1.0 --approve-visual
Artwork review is human, not automated. This tool never publishes to the site.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
from statistics import median
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
from PIL import Image, ImageChops, ImageDraw

MAX_FRAMES = 240
MAX_FRAME_PIXELS = 4_194_304
MAX_TOTAL_PIXELS = 65_000_000
MAX_SHEET = 8192

def decode(path: Path):
    if path.stat().st_size > 48 * 1024 * 1024:
        raise ValueError("GIF exceeds 48 MB import limit")
    frames, delays, warnings = [], [], []
    with Image.open(path) as source:
        if source.format != "GIF" or not getattr(source, "is_animated", False):
            raise ValueError("Expected an animated GIF")
        width, height = source.size
        count = source.n_frames
        if not (2 <= count <= MAX_FRAMES) or width * height > MAX_FRAME_PIXELS or width * height * count > MAX_TOTAL_PIXELS:
            raise ValueError("Animation exceeds safe frame/pixel limits")
        for i in range(count):
            source.seek(i)
            # Pillow resolves GIF disposal while seeking; use full logical canvases.
            frame = source.convert("RGBA").copy()
            if frame.size != (width, height):
                raise ValueError("Inconsistent source frame dimensions")
            frames.append(frame)
            delay = source.info.get("duration", 0)
            if not isinstance(delay, (int, float)) or delay <= 0:
                warnings.append(f"Frame {i} has no delay; replaced with 100 ms")
                delay = 100
            delays.append(max(10, round(delay / 10) * 10))
    return frames, delays, warnings

def inspect(frames, delays, warnings=(), allow_opaque=False):
    errors = []
    warnings = list(warnings)
    opaque = [i for i, frame in enumerate(frames) if frame.getchannel("A").getextrema()[0] == 255]
    if opaque:
        (warnings if allow_opaque else errors).append("Frames with fully opaque backgrounds: " + str(opaque[:20]))
    hashes = [hashlib.sha256(frame.tobytes()).hexdigest() for frame in frames]
    if len(set(hashes)) < 2:
        errors.append("All frames are identical")
    duplicates = [i for i in range(1, len(hashes)) if hashes[i] == hashes[i - 1]]
    if duplicates:
        warnings.append("Adjacent duplicate frames: " + str(duplicates[:30]))
    def distance(a, b):
        a = a.resize((64, 64))
        b = b.resize((64, 64))
        return sum(sum(v * i for i, v in enumerate(c.histogram()))
                   for c in ImageChops.difference(a, b).convert("RGB").split()) / (3 * 64 * 64)
    adjacent = [distance(a, b) for a, b in zip(frames, frames[1:])]
    typical = median([x for x in adjacent if x > 0]) if any(x > 0 for x in adjacent) else 0
    seam = distance(frames[-1], frames[0])
    if typical and seam > 2.5 * typical:
        warnings.append("Last-to-first loop seam is unusually large; inspect visually")
    if len(set(delays)) > 1:
        warnings.append("Variable GIF frame delays retained")
    return {
        "schema": "smi-gif-qa/1",
        "frame_count": len(frames),
        "logical_size_px": list(frames[0].size),
        "frame_durations_ms": delays,
        "total_duration_ms": sum(delays),
        "unique_frame_count": len(set(hashes)),
        "fully_opaque_frames": opaque,
        "adjacent_duplicate_indices": duplicates,
        "typical_frame_change": round(typical, 3),
        "loop_seam_change": round(seam, 3),
        "errors": errors, "warnings": warnings,
        "visual_review": "REQUIRED: contact, silhouette, anatomy, pose continuity, color consistency"
    }

def preview(frames, target: Path):
    count = len(frames)
    columns = min(4, count)
    width, height = frames[0].size
    tw = 240
    th = max(32, round(height * tw / width))
    if th > 420:
        th, tw = 420, max(30, round(width * 420 / height))
    cw, ch = tw + 16, th + 30
    sheet = Image.new("RGB", (cw * columns, ch * math.ceil(count / columns)), (34, 40, 48))
    draw = ImageDraw.Draw(sheet)
    for i, frame in enumerate(frames):
        x = (i % columns) * cw + 8
        y = (i // columns) * ch + 6
        back = Image.new("RGBA", (tw, th), (220, 220, 220, 255))
        grid = ImageDraw.Draw(back)
        for gy in range(0, th, 16):
            for gx in range(0, tw, 16):
                if (gx // 16 + gy // 16) % 2:
                    grid.rectangle((gx, gy, gx + 15, gy + 15), fill=(175, 180, 184, 255))
        back.alpha_composite(frame.resize((tw, th), Image.Resampling.LANCZOS))
        sheet.paste(back.convert("RGB"), (x, y))
        draw.text((x, y + th + 3), f"Frame {i:03}", fill="white")
    sheet.save(target, optimize=True)

def package(frames, delays, ident, license_id, playback, report, target):
    width, height = frames[0].size
    columns = min(4, MAX_SHEET // width)
    rows = MAX_SHEET // height
    if not columns or not rows:
        raise ValueError("Source frames exceed maximum atlas sheet size")
    capacity = columns * rows
    textures, regions, sequence_frames, images = {}, [], [], {}
    for start in range(0, len(frames), capacity):
        chunk = frames[start:start + capacity]
        index = start // capacity
        cols = min(columns, len(chunk))
        canvas = Image.new("RGBA", (cols * width, math.ceil(len(chunk) / cols) * height))
        key = f"sheet{index:03d}"
        filename = f"textures/{key}.png"
        textures[key] = {"path": filename, "width_px": canvas.width, "height_px": canvas.height, "alpha": "straight"}
        for j, frame in enumerate(chunk):
            i = start + j
            x, y = (j % cols) * width, (j // cols) * height
            canvas.alpha_composite(frame, (x, y))
            fid = f"{ident}.frame.{i:03d}"
            regions.append({"id": fid, "kind": "region", "name": f"Frame {i:03d}",
                            "texture": key, "rect_px": [x, y, width, height],
                            "logical_size_px": [width, height], "pivot": [0.5, 1.0]})
            sequence_frames.append({"asset": fid, "duration_ms": delays[i]})
        buffer = io.BytesIO()
        canvas.save(buffer, format="PNG", optimize=True)
        images[filename] = buffer.getvalue()
    sequence = {"id": ident, "kind": "sequence", "name": ident.split(".")[-1].title(),
                "default_fps": round(1000 * len(delays) / sum(delays), 5),
                "playback": playback, "frames": sequence_frames}
    manifest = {"schema": "smi-visual-pack/1", "pack_id": ident + ".pack",
                "version": "1.0.0", "license": license_id,
                "description": "Reviewed animation source conversion; see qa-report.json",
                "textures": textures, "assets": regions + [sequence]}
    def write(archive, name, payload):
        info = ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, payload, compress_type=ZIP_DEFLATED, compresslevel=6)
    with ZipFile(target, "w") as archive:
        write(archive, "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())
        for name, payload in sorted(images.items()):
            write(archive, name, payload)
        write(archive, "qa-report.json", (json.dumps(report, indent=2) + "\n").encode())
        write(archive, "README.txt", b"Visual approval is user-attested, not certified by machine QA.\n")
    return manifest

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pack", type=Path)
    parser.add_argument("--approve-visual", action="store_true")
    parser.add_argument("--id", default="")
    parser.add_argument("--license", default="UNSPECIFIED")
    parser.add_argument("--playback", choices=("loop", "once", "pingpong"), default="loop")
    args = parser.parse_args(argv)
    frames, delays, warnings = decode(args.source)
    report = inspect(frames, delays, warnings)
    report["source_sha256"] = hashlib.sha256(args.source.read_bytes()).hexdigest()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "qa-report.json").write_text(json.dumps(report, indent=2) + "\n")
    preview(frames, args.out / "frames-review.png")
    if args.pack:
        if not args.approve_visual:
            raise ValueError("Inspect every frame before passing --approve-visual")
        if report["errors"]:
            raise ValueError("Structural QA failed: " + "; ".join(report["errors"]))
        if not args.id or not all(c.isalnum() or c in "._-" for c in args.id):
            raise ValueError("Specify a safe stable --id")
        args.pack.parent.mkdir(parents=True, exist_ok=True)
        package(frames, delays, args.id, args.license, args.playback, report, args.pack)
        print("PACKED", args.pack)
    else:
        print("INSPECTED", args.out / "frames-review.png")
    print("Errors:", len(report["errors"]), "Warnings:", len(report["warnings"]))
    return bool(report["errors"])

if __name__ == "__main__":
    raise SystemExit(main())
