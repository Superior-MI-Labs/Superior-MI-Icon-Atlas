#!/usr/bin/env python3
"""Derive static browser projection from canonical per-atlas manifests, stdlib only."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from atlasctl import load,validate


def build(dest:Path|None=None):
    dest=Path(dest or ROOT/'site').resolve()
    m=load(ROOT)
    problems=validate(root=ROOT)
    if problems:raise ValueError('Invalid manifest: '+ '; '.join(problems[:5]))
    if dest==ROOT or ROOT in dest.parents and 'sheets' in dest.parts:
        raise ValueError('Refusing to build over source')
    dest.mkdir(parents=True,exist_ok=True)
    for name in ('index.html','styles.css','app.js','builder.html','builder.css','timeline-core.js','collection-core.js','bag-store.js','interaction-core.js','slot-core.js','builder.js','ai-guide.html'):
        shutil.copy2(ROOT/'web'/name,dest/name)
    vendor=ROOT/'web'/'vendor'
    if not (vendor/'jszip.min.js').is_file() or not (vendor/'JSZip-LICENSE.md').is_file(): raise ValueError('Missing bundled offline ZIP library')
    (dest/'vendor').mkdir(exist_ok=True)
    shutil.copy2(vendor/'jszip.min.js',dest/'vendor'/'jszip.min.js')
    shutil.copy2(vendor/'JSZip-LICENSE.md',dest/'vendor'/'JSZip-LICENSE.md')
    (dest/'schemas').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'schemas'/'smi-visual-pack-v1.schema.json',dest/'schemas'/'smi-visual-pack-v1.schema.json')
    shutil.copy2(ROOT/'schemas'/'smi-visual-collection-v1.schema.json',dest/'schemas'/'smi-visual-collection-v1.schema.json')
    # One canonical AI handoff split into short, versioned references.
    (dest/'ai').mkdir(exist_ok=True)
    for guide in sorted((ROOT/'docs'/'ai').glob('*.md')):
        shutil.copy2(guide,dest/'ai'/guide.name)
    (dest/'templates').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'web'/'templates'/'authoring-grids.zip',dest/'templates'/'authoring-grids.zip')
    (dest/'demo').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'web'/'demo'/'starter-pack.zip',dest/'demo'/'starter-pack.zip')
    shutil.copy2(ROOT/'web'/'demo'/'potions-collection.zip',dest/'demo'/'potions-collection.zip')
    src_files=['manifest.json','LICENSE','NOTICE.md']
    registry=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    src_files.extend(ref['manifest'] for ref in registry['sheets'])
    assets=set()
    for sh in m['sheets']:
        assets.update(sh[k] for k in ('path','foreground_mask','black_outline'))
    for name in [*src_files,*sorted(assets)]:
        src=ROOT/name;target=dest/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,target)
    (dest/'.nojekyll').write_text('')
    # Read-only derived projection. No second manually editable icon registry.
    data={
        'version':m.get('version'), 'pack':m.get('pack'),
        'styles':m.get('styles',{}), 'synonyms':m.get('search',{}).get('synonyms',{}),
        'sheets':[{k:sh.get(k) for k in ('path','foreground_mask','black_outline','width_px','height_px','cell_px','style','domain')} for sh in m['sheets']],
        'icons':[{k:i.get(k) for k in ('id','name','concept_id','aliases','tags','subjects','review_status','quality','domain','style','variant','license','rect_px','sheet')} for i in m['icons']]
    }
    js=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    (dest/'catalog-data.js').write_text('"use strict";window.ICON_ATLAS_DATA='+js+';\n',encoding='utf-8')
    return len(m['icons'])

if __name__=='__main__':
    path=ROOT/'site' if len(sys.argv)<2 else Path(sys.argv[1]).expanduser().resolve()
    print(f'Built {build(path)} icons into {path}')
