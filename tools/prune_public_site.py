#!/usr/bin/env python3
"""Remove internal, unapproved and historical assets *after* CI qualification.

The authored sources stay available for regression/migration; only the Pages
artifact is pruned. No second source-of-truth asset catalog is introduced.
"""
import json
import re
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def prune(site:Path):
    site=Path(site).resolve()
    if site==ROOT or not (site/'public-catalog.json').is_file():
        raise ValueError('Refusing to prune a source tree or unqualified site')
    catalog=json.loads((site/'public-catalog.json').read_text())
    allowed={Path(p['zip']).name for p in catalog['packs']}
    if not allowed:raise ValueError('No approved public ZIPs')
    for rel in ('catalog-data.js','featured-packs.json','featured.js','manifest.json'):
        (site/rel).unlink(missing_ok=True)
    for rel in ('manifests','sheets','showcase'):
        shutil.rmtree(site/rel,ignore_errors=True)
    demo=site/'demo'
    for f in demo.glob('*.zip'):
        if f.name not in allowed:f.unlink()
    (demo/'starter-pack.zip').unlink(missing_ok=True)
    # Hosted authoring docs link to GitHub fixtures, not removed public demo ZIPs.
    repo='https://github.com/Superior-MI-Labs/Superior-MI-Icon-Atlas'
    examples={'icons','animated-icons','character-animations','interactive-hud'}
    for doc in (site/'ai').rglob('*.md'):
        source=doc.read_text(encoding='utf-8')
        def link(match):
            name=match.group(1)
            url=(repo+'/tree/main/examples/'+name if name in examples
                else repo+'/blob/main/web/demo/'+name+'.zip')
            return ']('+url+')'
        updated=re.sub(r'\]\((?:\.\./)+demo/([a-z0-9-]+)\.zip\)',link,source)
        if updated!=source:doc.write_text(updated,encoding='utf-8')
    for p in catalog['packs']:
        if not (site/p['zip']).is_file():raise ValueError('Required approved pack was removed')
    for forbidden in ('catalog-data.js','featured-packs.json','manifest.json','demo/starter-pack.zip'):
        if (site/forbidden).exists():raise ValueError('Unapproved public file: '+forbidden)
    return len(allowed)

if __name__=='__main__':
    import sys
    path=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'site'
    print('Public site pruned. Approved collections:',prune(path))