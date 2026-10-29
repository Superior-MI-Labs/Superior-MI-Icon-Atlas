#!/usr/bin/env python3
"""Build one static/offline catalog from the authoritative manifest (stdlib only).

No second editable icon registry. Browser data is a derived projection.
"""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]


def sheets_for(manifest):
    if 'sheets' in manifest:
        sheets = manifest['sheets']
        if isinstance(sheets, dict):
            return list(sheets.values())
        return sheets
    return [manifest['sheet']]


def build(dest: Path | None = None):
    dest = dest or ROOT / 'site'
    m = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    if not isinstance(m.get('icons'), list):
        raise ValueError('manifest.icons must be a list')
    sheets = sheets_for(m)
    sheet_by_path = {sh['path']: sh for sh in sheets}
    if len(sheet_by_path) != len(sheets):
        raise ValueError('duplicate atlas paths')
    if len({i['id'] for i in m['icons']}) != len(m['icons']):
        raise ValueError('duplicate icon ID')
    for sh in sheets:
        for prop in ('path', 'foreground_mask', 'black_outline'):
            name = sh[prop]
            rel = Path(name)
            if rel.is_absolute() or '..' in rel.parts or not (ROOT / rel).is_file():
                raise ValueError(f'unsafe or missing sprite asset: {name}')
    for icon in m['icons']:
        sheet_path = icon['sheet']
        if sheet_path not in sheet_by_path:
            raise ValueError(f'icon references missing sheet: {icon["id"]}')
        sh = sheet_by_path[sheet_path]
        r = icon['rect_px']
        if min(r['x'], r['y']) < 0 or min(r['w'], r['h']) <= 0 or r['x'] + r['w'] > sh['width_px'] or r['y'] + r['h'] > sh['height_px']:
            raise ValueError(f'icon rectangle invalid: {icon["id"]}')
        if any(x in icon['id'] for x in ('/', '\\')):
            raise ValueError('icon ID may not contain path separators')

    dest.mkdir(parents=True, exist_ok=True)
    for name in ('index.html', 'styles.css', 'app.js'):
        shutil.copy2(ROOT / 'web' / name, dest / name)
    for sh in sheets:
        for prop in ('path', 'foreground_mask', 'black_outline'):
            rel = Path(sh[prop])
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, target)
    shutil.copy2(ROOT / 'manifest.json', dest / 'manifest.json')
    shutil.copy2(ROOT / 'LICENSE', dest / 'LICENSE')
    shutil.copy2(ROOT / 'NOTICE.md', dest / 'NOTICE.md')
    (dest / '.nojekyll').write_text('', encoding='utf-8')

    # Browser needs only a small immutable projection. Also works as file:/// offline.
    data = {
        'pack': m.get('pack'),
        'version': m.get('version'),
        'sheets': [{k: sh[k] for k in ('path','foreground_mask','black_outline','width_px','height_px','cell_px')} for sh in sheets],
        'icons': [{k: i.get(k) for k in ('id','concept_id','name','domain','variant','tags','quality','license','rect_px','sheet')} for i in m['icons']],
    }
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029','\\u2029')
    (dest / 'catalog-data.js').write_text('"use strict";window.ICON_ATLAS_DATA=' + js + ';\n', encoding='utf-8')
    return len(m['icons'])

if __name__ == '__main__':
    target = ROOT / 'site' if len(sys.argv) == 1 else Path(sys.argv[1]).expanduser().resolve()
    print(f'Built {build(target)} icons into {target}')
