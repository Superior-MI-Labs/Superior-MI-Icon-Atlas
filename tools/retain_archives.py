#!/usr/bin/env python3
"""Preserve exact approved ZIP bytes; no re-encoding, deletion or catalog inference."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import urllib.request

LIVE = 'https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/'
# GitHub rejects individual Git blobs over 100 MiB. Pages has a 1 GB site
# limit; fail closed before approaching it, rather than evicting old saves.
MAX_ZIP = 95 * 1024 * 1024
MAX_SITE = 900_000_000
MAX_CATALOG = 24 * 1024 * 1024
MAX_ARCHIVES = 4096
HEX = re.compile(r'[a-f0-9]{64}')
DEMO = re.compile(r'demo/[a-zA-Z0-9_-]+\.zip')


def archive_path(digest):
    if not isinstance(digest, str) or not HEX.fullmatch(digest):
        raise ValueError('Invalid archive digest')
    return 'archives/sha256/' + digest + '.zip'


def digest_file(path):
    if not path.is_file() or path.is_symlink() or not 0 < path.stat().st_size <= MAX_ZIP:
        raise ValueError('Missing, unsafe or oversized retained ZIP: ' + str(path))
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def approved_packs(catalog):
    if catalog.get('schema') != 'smi-public-catalog/1' or not isinstance(catalog.get('packs'), list):
        raise ValueError('Invalid public catalog')
    seen = set()
    for pack in catalog['packs']:
        if pack.get('archived') or pack.get('zip') is None:
            continue
        alias = pack['zip']
        if not isinstance(alias, str) or not DEMO.fullmatch(alias) or alias in seen:
            raise ValueError('Invalid or duplicate published ZIP alias')
        seen.add(alias)
        pinned = archive_path(pack.get('archive_sha256'))
        if 'immutable_zip' in pack and pack['immutable_zip'] != pinned:
            raise ValueError('Immutable locator disagrees with digest')
        yield pack, pinned


def preserve(source, target, digest):
    if digest_file(source) != digest:
        raise ValueError('Archive digest mismatch: ' + str(source))
    if target.exists():
        if digest_file(target) != digest:
            raise ValueError('Retained archive corruption: ' + str(target))
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def stage_current(site, catalog):
    """Build-time projection from the exact current approved generated ZIPs."""
    directory = site / 'archives/sha256'
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    packs = list(approved_packs(catalog))
    if not packs:
        raise ValueError('No approved archives')
    for pack, pinned in packs:
        preserve(site / pack['zip'], site / pinned, pack['archive_sha256'])
        pack['immutable_zip'] = pinned


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Unexpected redirect while seeding archive history')


def fetch_live(relative, limit):
    # Only the fixed official Pages origin and validated paths are requested.
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(LIVE + relative, timeout=60) as response:
        data = response.read(limit + 1)
    if not 0 < len(data) <= limit:
        raise ValueError('Empty or oversized live archive response')
    return data


def seed(store, fetch=fetch_live):
    """Bootstrap only the immediately preceding published site, not invented history."""
    catalog = json.loads(fetch('public-catalog.json', MAX_CATALOG))
    packs = list(approved_packs(catalog))
    if not packs:
        raise ValueError('Cannot bootstrap without a prior published catalog')
    if any('immutable_zip' in p for p, _ in packs):
        raise ValueError('Published retention already exists but retention branch is missing; recover branch')
    for pack, _ in packs:
        digest = pack['archive_sha256']
        target = store / (digest + '.zip')
        if target.exists():
            if digest_file(target) != digest:
                raise ValueError('Corrupt bootstrap archive')
            continue
        data = fetch(pack['zip'], MAX_ZIP)
        if len(data) > MAX_ZIP or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Prior live ZIP digest mismatch: ' + pack['zip'])
        target.write_bytes(data)


def retained_files(store):
    entries = sorted(store.iterdir())
    if len(entries) > MAX_ARCHIVES:
        raise ValueError('Retention archive count limit exceeded')
    for path in entries:
        if path.suffix != '.zip' or not HEX.fullmatch(path.stem):
            raise ValueError('Unexpected retention member: ' + path.name)
        if digest_file(path) != path.stem:
            raise ValueError('Retained archive corruption: ' + path.name)
    return entries


def publish_retained(site, store, *, bootstrap=False, fetch=fetch_live):
    """Append current pins, materialize historical bytes into the qualified site."""
    catalog = json.loads((site / 'public-catalog.json').read_text())
    packs = list(approved_packs(catalog))
    if not packs or any(p.get('immutable_zip') != loc for p, loc in packs):
        raise ValueError('Site missing qualified immutable locators')
    store.mkdir(parents=True, exist_ok=True)
    previous = retained_files(store)
    if bootstrap:
        if previous:
            raise ValueError('Bootstrap requires an empty store')
        seed(store, fetch)
    elif not previous:
        raise ValueError('Retention history missing; refuse to silently initialize')
    for p, loc in packs:
        preserve(site / p['zip'], store / (p['archive_sha256'] + '.zip'), p['archive_sha256'])
        if digest_file(site / loc) != p['archive_sha256']:
            raise ValueError('Current immutable site bytes mismatch')
    entries = retained_files(store)
    # Count actual deployed bytes including current mutable compatibility aliases.
    outside = sum(p.stat().st_size for p in site.rglob('*')
                  if p.is_file() and 'archives/sha256/' not in p.relative_to(site).as_posix())
    if outside + sum(p.stat().st_size for p in entries) > MAX_SITE:
        raise ValueError('Pages retention budget exceeded; migrate storage without deleting history')
    for p in entries:
        preserve(p, site / archive_path(p.stem), p.stem)
    return len(entries)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('site', type=Path)
    parser.add_argument('store', type=Path)
    parser.add_argument('--bootstrap', action='store_true')
    args = parser.parse_args()
    print('Retained exact ZIPs:', publish_retained(args.site, args.store, bootstrap=args.bootstrap))
