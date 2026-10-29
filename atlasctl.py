#!/usr/bin/env python3
"""One-manifest icon atlas lookup, extraction and verification."""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent

def read_manifest():
    p = ROOT / 'manifest.json'
    m = json.loads(p.read_text(encoding='utf-8'))
    if m.get('schema') != 'smi-icon-atlas/1':
        raise ValueError('unsupported icon atlas manifest schema')
    return m

def lookup(icons, key):
    for entry in icons:
        if entry['id'] == key:
            return entry
    raise KeyError(key)

def normalized(s):
    return ' '.join(re.findall(r'[\w]+', s.lower().replace('_', ' ')))

def score(entry, query):
    q = normalized(query)
    ident = normalized(entry['id'])
    name = normalized(entry['name'])
    tags = [normalized(t) for t in entry['tags']]
    if not q:
        return 0
    if q == normalized(entry['id']): return 100
    if q == normalized(entry['concept_id']): return 95
    if q == name: return 80
    if q in tags: return 70
    if name.startswith(q): return 50
    if any(t.startswith(q) for t in tags): return 40
    if q in ident: return 30
    if any(q in t for t in tags): return 20
    return 0

def verify(m, deep=True):
    from PIL import Image
    sh=m['sheet']; icons=m['icons']; errors=[]
    c,r,s=sh['columns'],sh['rows'],sh['cell_px']
    p=ROOT / sh['path']
    if (c,r,s)!=(24,8,96): errors.append('unexpected sheet geometry')
    if len(icons)>c*r: errors.append('overfilled sheet')
    if len({i['id'] for i in icons})!=len(icons):errors.append('duplicate icon ID')
    if not p.is_file():errors.append(f'missing {p}')
    if errors:return errors
    img=Image.open(p)
    if img.size!=(c*s,r*s) or img.mode!='RGBA':errors.append(f'bad RGBA image {img.mode} {img.size}')
    if hashlib.sha256(p.read_bytes()).hexdigest()!=sh['sha256']:
        errors.append('sheet checksum differs from manifest')
    for layer in ('foreground_mask','black_outline'):
        f=ROOT/sh[layer]
        if not f.exists():errors.append(f'missing {layer}')
        else:
            layer_img=Image.open(f)
            if layer_img.mode!='RGBA' or layer_img.size!=img.size:errors.append(f'invalid {layer} image')
    if errors:return errors
    occupied=set()
    for e in icons:
        x,y=e['cell']['x'],e['cell']['y']; rect=e['rect_px']
        if x<0 or x>=c or y<0 or y>=r:errors.append(f'out of bounds: {e["id"]}');continue
        if (x,y) in occupied:errors.append(f'cell collision: {e["id"]}')
        occupied.add((x,y))
        if rect != dict(x=x*s,y=y*s,w=s,h=s):errors.append(f'bad rect: {e["id"]}')
        actual=(x/c,y/r,(x+1)/c,(y+1)/r)
        uv=e['uv']
        if any(abs(z-t)>1e-8 for z,t in zip((uv['u0'],uv['v0'],uv['u1'],uv['v1']),actual)):
            errors.append(f'bad UV: {e["id"]}')
        if deep:
            crop=img.crop((x*s,y*s,(x+1)*s,(y+1)*s))
            if not crop.getchannel('A').getbbox():errors.append(f'blank occupied cell: {e["id"]}')
            if hashlib.sha256(crop.tobytes()).hexdigest()!=e['crop_rgba_sha256']:
                errors.append(f'crop hash mismatch: {e["id"]}')
    if deep:
        for y in range(r):
            for x in range(c):
                if (x,y) not in occupied:
                    if img.crop((x*s,y*s,(x+1)*s,(y+1)*s)).getchannel('A').getbbox():
                        errors.append(f'paint in unused cell {(x,y)}')
        for xy in ((0,0),(img.width-1,0),(0,img.height-1),(img.width-1,img.height-1)):
            if img.getpixel(xy)[3] != 0:errors.append('nontransparent sheet corner')
    return errors

def make_tint(e, color):
    from PIL import Image
    if not re.fullmatch(r'#[0-9a-fA-F]{6}',color):raise ValueError('use #RRGGBB color')
    x,y,w,h=e['rect_px'].values()
    m=read_manifest()
    outline=Image.open(ROOT/m['sheet']['black_outline']).convert('RGBA').crop((x,y,x+w,y+h))
    mask=Image.open(ROOT/m['sheet']['foreground_mask']).convert('RGBA').crop((x,y,x+w,y+h)).getchannel('A')
    foreground=Image.new('RGBA',(w,h),tuple(bytes.fromhex(color[1:]))+(0,))
    foreground.putalpha(mask)
    return Image.alpha_composite(outline,foreground)

def main():
    p=argparse.ArgumentParser(description='Superior MI Icon Atlas control tool')
    sub=p.add_subparsers(dest='action',required=True)
    search=sub.add_parser('search');search.add_argument('query');search.add_argument('--limit',type=int,default=20)
    info=sub.add_parser('info');info.add_argument('id')
    variants=sub.add_parser('variants');variants.add_argument('concept_id')
    sub.add_parser('browse')
    sub.add_parser('validate').add_argument('--quick',action='store_true')
    crop=sub.add_parser('crop');crop.add_argument('id');crop.add_argument('--out',required=True)
    tint=sub.add_parser('tint');tint.add_argument('id');tint.add_argument('--color',required=True);tint.add_argument('--out',required=True)
    a=p.parse_args();m=read_manifest();icons=m['icons']
    if a.action=='search':
        ranked=sorted(((score(e,a.query),e) for e in icons),key=lambda q:(-q[0],q[1]['id']))
        for value,e in ranked[:max(0,a.limit)]:
            if value:print(f'{value:3d}  {e["id"]}    {e["name"]}')
    elif a.action=='info':print(json.dumps(lookup(icons,a.id),indent=2))
    elif a.action=='variants':
        found=[e for e in icons if e['concept_id']==a.concept_id]
        if not found:raise KeyError(a.concept_id)
        for e in found:print(e['id'])
    elif a.action=='browse':
        domains=defaultdict(set)
        for e in icons:domains[e['domain']].add(e['concept_id'])
        for domain,concepts in sorted(domains.items()):print(f'{domain:<16} {len(concepts):3d} concepts')
    elif a.action=='validate':
        errors=verify(m,deep=not a.quick)
        if errors:
            for e in errors: print('FAIL',e,file=sys.stderr)
            return 1
        print(f'PASS: {len(icons)} icons, {m["sheet"]["columns"]}x{m["sheet"]["rows"]} sheet, checksums and coordinates valid')
    elif a.action in ('crop','tint'):
        from PIL import Image
        e=lookup(icons,a.id); rect=e['rect_px'];x,y,w,h=rect.values()
        if a.action=='crop':
            result=Image.open(ROOT/m['sheet']['path']).convert('RGBA').crop((x,y,x+w,y+h))
        else:result=make_tint(e,a.color)
        target=Path(a.out).expanduser()
        target.parent.mkdir(parents=True,exist_ok=True)
        result.save(target)
        print('SAVED:',target)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (KeyError,ValueError) as e:
        print(f'ERROR: {e}',file=sys.stderr)
        raise SystemExit(1)
