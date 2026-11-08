#!/usr/bin/env python3
"""Review animated image/video sources and export through the existing Atlas GIF packer.

Examples:
  python3 tools/import_animation.py clip.mp4 --out /tmp/sky-review --fps 16 --seconds 3
  python3 tools/import_animation.py clip.mp4 --out /tmp/sky-review --fps 16 --seconds 3 \
      --pack /tmp/sky.zip --id sky.walk --license UNSPECIFIED --approve-visual --allow-opaque

The source is never edited. --allow-opaque is for scenes/backgrounds, not a
substitute for alpha matting on character animations.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.import_gif import (MAX_FRAMES, MAX_FRAME_PIXELS, MAX_TOTAL_PIXELS,
                              inspect, preview, package)

ANIMATED = {'.gif', '.apng', '.webp', '.png'}
VIDEO = {'.mp4', '.webm', '.mov', '.mkv', '.m4v'}
MAX_SOURCE_BYTES = 120 * 1024 * 1024


def decode_animated(path: Path):
    frames, delays, warnings = [], [], []
    with Image.open(path) as source:
        if source.format not in ('GIF', 'PNG', 'WEBP') or not getattr(source, 'is_animated', False):
            raise ValueError('Expected animated GIF, APNG, or WebP (not a still image)')
        width, height = source.size
        first = 1 if source.format == 'PNG' and source.info.get('default_image') else 0
        count = source.n_frames - first
        check_limits(width, height, count)
        for i in range(first, source.n_frames):
            source.seek(i)
            frames.append(source.convert('RGBA').copy())
            duration = source.info.get('duration', 0)
            if not isinstance(duration, (int, float)) or duration <= 0:
                duration = 100
                warnings.append(f'Frame {i-first} had no duration; using 100 ms')
            delays.append(max(1, round(duration)))
    return frames, delays, warnings


def check_limits(width: int, height: int, count: int):
    if not (2 <= count <= MAX_FRAMES) or width < 1 or height < 1:
        raise ValueError('Animation must contain 2 to 240 frames')
    if width * height > MAX_FRAME_PIXELS or width * height * count > MAX_TOTAL_PIXELS:
        raise ValueError('Animation exceeds safe frame/pixel limits')


def decode_video(path: Path, fps: int, start: float, seconds: float):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        raise RuntimeError('Install FFmpeg first: sudo apt install ffmpeg')
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height', '-of', 'json', str(path)],
        capture_output=True, text=True, timeout=20, check=True)
    streams = json.loads(probe.stdout).get('streams', [])
    if not streams:
        raise ValueError('No decodable video stream')
    width, height = int(streams[0]['width']), int(streams[0]['height'])
    check_limits(width, height, max(2, round(seconds * fps)))
    warnings = ['Video was sampled at a fixed FPS; audio and original timestamps are not retained']
    with TemporaryDirectory(prefix='smi-video-import-') as temp:
        destination = str(Path(temp) / 'frame-%05d.png')
        command = ['ffmpeg', '-hide_banner', '-nostdin', '-loglevel', 'error', '-y',
                   '-ss', str(start), '-i', str(path), '-t', str(seconds),
                   '-vf', f'fps={fps}', '-frames:v', str(MAX_FRAMES),
                   '-pix_fmt', 'rgba', destination]
        subprocess.run(command, capture_output=True, text=True, timeout=180, check=True)
        paths = sorted(Path(temp).glob('frame-*.png'))
        check_limits(width, height, len(paths))
        frames = []
        for filename in paths:
            with Image.open(filename) as frame:
                if frame.size != (width, height):
                    raise ValueError('Decoded video has inconsistent dimensions')
                frames.append(frame.convert('RGBA').copy())
    # Distribute fractional milliseconds without shortening the total cycle.
    delays = [round((i + 1) * 1000 / fps) - round(i * 1000 / fps)
              for i in range(len(frames))]
    return frames, delays, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--fps', type=int, default=16, help='video sample rate, 1..30 FPS')
    parser.add_argument('--start', type=float, default=0)
    parser.add_argument('--seconds', type=float, default=4, help='video segment, up to 8 seconds')
    parser.add_argument('--pack', type=Path)
    parser.add_argument('--id', default='')
    parser.add_argument('--license', default='UNSPECIFIED')
    parser.add_argument('--playback', choices=('loop', 'once', 'pingpong'), default='loop')
    parser.add_argument('--approve-visual', action='store_true')
    parser.add_argument('--allow-opaque', action='store_true',
                        help='explicitly accept opaque video as scenery, never transparent character art')
    args = parser.parse_args(argv)
    if not args.source.is_file() or args.source.stat().st_size > MAX_SOURCE_BYTES:
        parser.error('Missing or oversized input (maximum 120 MB)')
    extension = args.source.suffix.lower()
    if extension not in ANIMATED | VIDEO:
        parser.error('Supported inputs: GIF, APNG, animated WebP, MP4, WebM, MOV, MKV, M4V')
    if not (1 <= args.fps <= 30) or not (0 <= args.start <= 3600) or not (0 < args.seconds <= 8):
        parser.error('Use FPS 1..30, start 0..3600, segment length 0..8 seconds')
    if args.pack and (not args.approve_visual or not args.id or
                     not all(c.isalnum() or c in '._-' for c in args.id)):
        parser.error('Packing needs --approve-visual and safe stable --id')
    if extension in VIDEO:
        frames, delays, warnings = decode_video(args.source, args.fps, args.start, args.seconds)
    else:
        frames, delays, warnings = decode_animated(args.source)
    report = inspect(frames, delays, warnings, allow_opaque=args.allow_opaque)
    report['source_sha256'] = hashlib.sha256(args.source.read_bytes()).hexdigest()
    report['source_format'] = extension.lstrip('.')
    report['review_disposition'] = 'NOT_APPROVED_BY_AUTOMATED_QA'
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'qa-report.json').write_text(json.dumps(report, indent=2) + '\n')
    preview(frames, args.out / 'frames-review.png')
    if args.pack:
        if report['errors']:
            raise ValueError('Structural QA failed: ' + '; '.join(report['errors']))
        args.pack.parent.mkdir(parents=True, exist_ok=True)
        package(frames, delays, args.id, args.license, args.playback, report, args.pack)
        print('PACKED', args.pack)
    else:
        print('INSPECTED', args.out / 'frames-review.png')
    print('Errors:', len(report['errors']), 'Warnings:', len(report['warnings']))
    return bool(report['errors'])


if __name__ == '__main__':
    raise SystemExit(main())
