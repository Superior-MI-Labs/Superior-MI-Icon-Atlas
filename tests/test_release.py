#!/usr/bin/env python3
"""Fast, deterministic artifact-level release tests; no external services."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import atlasctl

def run(*args):
    return subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,check=True,capture_output=True,text=True)

def main():
    m=atlasctl.read_manifest()
    assert len(m['icons'])==192
    assert len({x['concept_id'] for x in m['icons']})==64
    assert len({x['id'] for x in m['icons']})==192
    assert all(x['source']['third_party_glyph'] is False for x in m['icons'])
    assert all(x['source']['kind']=='independent-geometric-design' for x in m['icons'])
    assert all(x['license']=='Apache-2.0' for x in m['icons'])
    assert all(set(x['variant'] for x in m['icons'] if x['concept_id']==c)=={'symbol','badge','tile'} for c in {x['concept_id'] for x in m['icons']})
    assert not atlasctl.verify(m)
    for q,needle in [('bug','bug'),('defect','bug'),('integer','integer'),('i32','integer'),('picture','camera'),('ocean','fish'),('football','ball'),('family','family')]:
        candidates=sorted(((atlasctl.score(x,q),x) for x in m['icons']),reverse=True,key=lambda t:t[0])
        assert candidates[0][0]>0 and any(needle in x['id'] for s,x in candidates if s>0), (q,needle)
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        dest=tmp/'custom'/'icon-atlas'
        run(ROOT/'tools/install.py','--dest',dest)
        assert (dest/'manifest.json').exists()
        assert (dest/'catalog.html').exists()
        assert (dest/'site/index.html').exists()
        assert (dest/'site/catalog-data.js').exists()
        assert (dest/'sheets/original-00/atlas.png').exists()
        run(ROOT/'tools/install.py','--dest',dest,'--check')
        failed=subprocess.run([sys.executable,str(ROOT/'tools/install.py'),'--dest',str(dest)],capture_output=True,text=True)
        assert failed.returncode!=0, 'installer must not replace existing directory without --upgrade'
        run(ROOT/'tools/install.py','--dest',dest,'--upgrade')
        assert len(list(dest.parent.glob('icon-atlas.bak-*')))==1
        out=tmp/'bug.png'
        run(ROOT/'atlasctl.py','crop','icons.original.programming.bug.symbol','--out',out)
        from PIL import Image
        assert Image.open(out).size==(96,96)
        tinted=tmp/'tinted.png'
        run(ROOT/'atlasctl.py','tint','icons.original.science.atom.symbol','--color','#ff0000','--out',tinted)
        rgba=Image.open(tinted).convert('RGBA')
        opaque=[rgba.getpixel((x,y)) for y in range(96) for x in range(96) if rgba.getpixel((x,y))[3]>0]
        assert any((p[0],p[1],p[2])==(0,0,0) for p in opaque), 'outline lost fixed black color'
        assert any(p[0]>p[1]+40 for p in opaque), 'foreground did not tint'
    assert 'Material Design' not in m['sheet']['id']
    print('PASS: 192 assets, 64 concepts, geometry/alpha/hashes, provenance flags, search, crop, tint, install, upgrade')

if __name__=='__main__':main()
