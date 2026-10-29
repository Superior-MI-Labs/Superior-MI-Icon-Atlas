#!/usr/bin/env python3
"""Portable, offline shared-resource installer (stdlib-only)."""
from __future__ import annotations
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import sys
import subprocess
import tempfile

SOURCE = Path(__file__).resolve().parents[1]
MARKER = 'smi-icon-atlas/1'
FILES = ['manifest.json', 'LICENSE', 'NOTICE.md', 'README.md', 'catalog.html', 'requirements-build.txt', 'atlasctl.py', 'RELEASE.json', 'CONTRIBUTING.md', '.gitignore', '.gitattributes', 'sheets', 'docs', 'tools', 'tests', 'web']

def default_destination() -> Path:
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA')
        if not base:
            raise RuntimeError('LOCALAPPDATA is not set; provide --dest')
        return Path(base) / 'SuperiorMILabs' / 'icon-atlas'
    base = Path(os.environ['XDG_DATA_HOME']).expanduser() if os.environ.get('XDG_DATA_HOME') else Path.home() / '.local' / 'share'
    return base / 'superior-mi' / 'icon-atlas'

def valid_install(path: Path) -> bool:
    try:
        return json.loads((path / 'manifest.json').read_text(encoding='utf-8')).get('schema') == MARKER
    except (ValueError, OSError):
        return False

def main() -> int:
    p = argparse.ArgumentParser(description='Install Superior MI Icon Atlas to the user data directory')
    p.add_argument('--dest', type=Path, default=None, help='Override destination directory')
    p.add_argument('--show-path', action='store_true')
    p.add_argument('--upgrade', action='store_true', help='Replace existing valid installation; retain timestamped backup')
    p.add_argument('--check', action='store_true', help='Check whether destination contains a valid Icon Atlas install')
    args = p.parse_args()
    destination = (args.dest or default_destination()).expanduser().absolute()
    if args.show_path:
        print(destination)
        return 0
    if args.check:
        print(('INSTALLED: ' if valid_install(destination) else 'NOT INSTALLED: ') + str(destination))
        return 0 if valid_install(destination) else 1
    if not valid_install(SOURCE):
        p.error('source manifest invalid; extract the full release first')
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not args.upgrade:
        p.error(f'destination already exists: {destination}; use --upgrade for a managed prior install')
    if destination.exists() and not valid_install(destination):
        p.error('destination is not a recognizable Icon Atlas install; refusing to overwrite it')
    with tempfile.TemporaryDirectory(prefix='.icon-atlas-install-', dir=destination.parent) as tmp:
        staged = Path(tmp) / 'icon-atlas'
        staged.mkdir()
        for item in FILES:
            original = SOURCE / item
            if original.is_dir():
                shutil.copytree(original, staged / item, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            elif original.is_file():
                shutil.copy2(original, staged / item)
            else:
                p.error(f'missing source file: {original}')
        if not valid_install(staged):
            p.error('staging verification failed')
        # Build from staged manifest; no external service and no checked-in duplicate site.
        subprocess.run([sys.executable, str(staged / 'tools' / 'build_site.py')], check=True, capture_output=True, text=True)
        if not (staged / 'site' / 'index.html').is_file():
            p.error('site build failed')
        backup = None
        if destination.exists():
            timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            backup = destination.with_name(destination.name + '.bak-' + timestamp)
            if backup.exists():
                p.error(f'backup destination already exists: {backup}')
            destination.rename(backup)
        try:
            staged.rename(destination)
        except Exception:
            if backup is not None and backup.exists() and not destination.exists():
                backup.rename(destination)
            raise
    print(f'INSTALLED: {destination}')
    if backup is not None:
        print(f'BACKUP: {backup}')
    print('MANIFEST:', destination / 'manifest.json')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
