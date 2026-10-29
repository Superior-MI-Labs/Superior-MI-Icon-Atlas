#!/usr/bin/env python3
"""Icon Atlas: canonical registry loader, search, export and raster operations."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def tokens(text):
    normalized = unicodedata.normalize('NFKD', str(text or '')).casefold()
    normalized = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.findall(r'[a-z0-9]+', normalized)


def expand_synonyms(synonyms):
    groups = {}
    for root, variants in synonyms.items():
        group = {root, *variants}
        words = set()
        for entry in group:
            words.update(tokens(entry))
        for word in words:
            groups.setdefault(word, set()).update(words)
    return groups


def _rect(cell, cell_px):
    x, y = cell
    return {'x': x * cell_px, 'y': y * cell_px, 'w': cell_px, 'h': cell_px}


def _box(values):
    return dict(zip(('x', 'y', 'w', 'h'), values))


def load(root=ROOT):
    """Assemble runtime view from authoritative root + per-sheet documents.

    No second editable manifest and no independently maintained search index.
    """
    root = Path(root)
    registry = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    if registry.get('schema') != 'smi-icon-atlas/3':
        raise ValueError('Unsupported schema (expected smi-icon-atlas/3)')
    sheets, icons, seen = [], [], set()
    for reference in registry['sheets']:
        path = Path(reference['manifest'])
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Unsafe sheet manifest path')
        manifest = json.loads((root / path).read_text(encoding='utf-8'))
        if manifest.get('schema') != 'smi-icon-atlas-sheet/1':
            raise ValueError('Unsupported sheet schema: ' + str(path))
        sheet = manifest['sheet']
        if (sheet['id'], sheet['domain'], sheet['style']) != (reference['id'], reference['domain'], reference['style']):
            raise ValueError('Sheet index mismatch: ' + str(path))
        if reference['count'] != len(manifest['icons']):
            raise ValueError('Sheet count mismatch: ' + str(path))
        sheets.append(sheet)
        for candidate in manifest['icons']:
            ident = candidate['id']
            if ident in seen:
                raise ValueError('Duplicate icon ID: ' + ident)
            seen.add(ident)
            review = candidate['review']
            cx, cy = candidate['cell']
            px = sheet['cell_px']
            name = review.get('name') or f'Unreviewed glyph · {cx:02d}:{cy:02d}'
            src = candidate['source']
            icons.append({
                'id': ident,
                'name': name,
                'concept_id': review.get('concept_id'),
                'aliases': review.get('aliases', []),
                'tags': review.get('tags', []),
                'subjects': review.get('subjects', []),
                'review_status': review['status'],
                'quality': review.get('art_status', 'candidate'),
                'domain': sheet['domain'],
                'variant': sheet['variant'],
                'style': sheet['style'],
                'sheet': sheet['path'],
                'cell': {'x': cx, 'y': cy},
                'rect_px': _rect(candidate['cell'], px),
                'uv': {'u0': cx / sheet['columns'], 'v0': cy / sheet['rows'], 'u1': (cx+1) / sheet['columns'], 'v1': (cy+1)/sheet['rows']},
                'source_file': src['file'],
                'source_bbox_px': _box(src['bbox']),
                'source_region_px': _box(src['region']),
                'provenance': {'source_path': 'source-images/' + src['file'], 'semantic_review': review['status']=='reviewed','licensing_review': candidate['license']['rights_reviewed']},
                'license': candidate['license']['id'],
                'crop_rgba_sha256': candidate['crop_rgba_sha256'],
            })
    return {**registry, 'icons': icons, 'sheets': sheets}


def search_icons(query, *, manifest=None, domain=None, style=None, status=None, subject=None):
    """Token AND search; exact identifiers and names outrank tags and generic category matches."""
    m = manifest or load()
    termlist = tokens(query)
    thesaurus = expand_synonyms(m.get('search', {}).get('synonyms', {}))
    ranked = []
    for icon in m['icons']:
        if domain and icon['domain'] != domain: continue
        if style and icon['style'] != style: continue
        if status and icon['review_status'] != status: continue
        if subject and subject not in icon['subjects']: continue
        primary = {x.casefold() for x in (icon['id'],icon['name'],*(icon['aliases'] or [])) if x}
        fields = {
            'id': set(tokens(icon['id'])),
            'name': set(tokens(icon['name'])),
            'alias': set(w for a in icon['aliases'] for w in tokens(a)),
            'tags': set(w for t in icon['tags'] for w in tokens(t)),
            'subject': set(w for s in icon['subjects'] for w in tokens(s)),
            'domain': set(tokens(icon['domain'])),
            'style': set(tokens(icon['style'])),
        }
        if not termlist:
            score = 1 if icon['review_status']=='reviewed' else 0
        else:
            score = 0
            for token in termlist:
                related = thesaurus.get(token, {token}) - {token}
                weights = [('id',50),('name',45),('alias',38),('tags',28),('subject',17),('domain',3),('style',1)]
                direct = max((weight for f,weight in weights if token in fields[f]),default=0)
                indirect = max((round(weight * .55) for f,weight in weights if related & fields[f]),default=0)
                weight = max(direct,indirect)
                if not weight:
                    score = 0
                    break
                score += weight
            if len(termlist)==1 and query.casefold().strip() in primary: score += 200
        if score or not termlist:
            ranked.append((score, icon['id'], icon))
    return [i for _,_,i in sorted(ranked,key=lambda x:(-x[0], x[1]))]


def validate(deep=False, root=ROOT):
    m = load(root)
    root = Path(root)
    errors, cells, bysheet = [], set(), {s['path']: [] for s in m['sheets']}
    for sheet in m['sheets']:
        path = root / sheet['path']
        if not path.is_file(): errors.append('Missing '+sheet['path']);continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != sheet['sha256']: errors.append('Sheet hash '+sheet['path'])
        head=path.read_bytes()[:26]
        w,h=struct.unpack('>II',head[16:24]) if len(head)>=26 else (0,0)
        if head[:8]!=b'\x89PNG\r\n\x1a\n' or (w,h)!=(sheet['width_px'],sheet['height_px']) or head[25]!=6:
            errors.append('PNG dimensions / alpha '+sheet['path'])
        for key in ('foreground_mask','black_outline'):
            if not (root/sheet[key]).is_file(): errors.append('Missing layer '+sheet[key])
    for icon in m['icons']:
        if icon['sheet'] not in bysheet:
            errors.append('Unknown sheet '+icon['id']);continue
        sh=next(s for s in m['sheets'] if s['path']==icon['sheet'])
        cx,cy=icon['cell']['x'], icon['cell']['y']
        key=(icon['sheet'],cx,cy)
        if key in cells:errors.append('Occupied cell collision '+icon['id'])
        cells.add(key)
        if not (0 <= cx < sh['columns'] and 0 <= cy < sh['rows']):errors.append('Bad cell '+icon['id'])
        if icon['rect_px'] != _rect([cx,cy],sh['cell_px']):errors.append('Bad crop '+icon['id'])
        if len(icon['tags'])!=len(set(t.casefold() for t in icon['tags'])):errors.append('Duplicate tags '+icon['id'])
        bysheet[icon['sheet']].append(icon)
    if deep:
        try:from PIL import Image
        except ImportError:raise RuntimeError('Install Pillow for deep validation')
        for sheet in m['sheets']:
            path=root/sheet['path']
            if not path.exists():continue
            image=Image.open(path).convert('RGBA')
            for icon in bysheet[sheet['path']]:
                r=icon['rect_px'];box=(r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])
                crop=image.crop(box)
                if not crop.getchannel('A').getbbox():errors.append('Empty icon '+icon['id'])
                if hashlib.sha256(crop.tobytes()).hexdigest()!=icon['crop_rgba_sha256']:errors.append('Crop mismatch '+icon['id'])
                alpha=crop.getchannel('A')
                margin=5;w=r['w'];h=r['h']
                if any(alpha.crop(rect).getbbox() for rect in ((0,0,w,margin),(0,h-margin,w,h),(0,0,margin,h),(w-margin,0,w,h))):
                    errors.append('Border bleed '+icon['id'])
    return errors


def main():
    p=argparse.ArgumentParser(description='Superior MI Icon Atlas')
    sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('validate').add_argument('--deep',action='store_true')
    q=sub.add_parser('search');q.add_argument('query');q.add_argument('--domain');q.add_argument('--style');q.add_argument('--status');q.add_argument('--subject');q.add_argument('--limit',type=int,default=30)
    inf=sub.add_parser('info');inf.add_argument('id')
    crop=sub.add_parser('crop');crop.add_argument('id');crop.add_argument('--out',required=True)
    tint=sub.add_parser('tint');tint.add_argument('id');tint.add_argument('--out',required=True);tint.add_argument('--color',required=True)
    args=p.parse_args()
    if args.cmd=='validate':
        errors=validate(args.deep)
        for e in errors:print('FAIL',e,file=sys.stderr)
        print(('PASS' if not errors else 'FAIL') + f': {len(load()["icons"])} icons')
        return bool(errors)
    m=load()
    if args.cmd=='search':
        results=search_icons(args.query,manifest=m,domain=args.domain,style=args.style,status=args.status,subject=args.subject)
        for icon in results[:args.limit]:print(icon['id'],'·',icon['name'])
        print(f'{len(results)} matches')
        return 0
    icon=next((i for i in m['icons'] if i['id']==args.id),None)
    if not icon:raise ValueError('Unknown icon: '+args.id)
    if args.cmd=='info':print(json.dumps(icon,indent=2));return 0
    from PIL import Image
    r=icon['rect_px'];s=next(s for s in m['sheets'] if s['path']==icon['sheet']);box=(r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])
    if args.cmd=='crop':im=Image.open(ROOT/s['path']).convert('RGBA').crop(box)
    else:
        if not re.fullmatch(r'#[0-9a-fA-F]{6}',args.color):raise ValueError('Expected #RRGGBB')
        outline=Image.open(ROOT/s['black_outline']).convert('RGBA').crop(box)
        fg=Image.open(ROOT/s['foreground_mask']).convert('RGBA').crop(box).getchannel('A')
        ink=Image.new('RGBA',(r['w'],r['h']),tuple(bytes.fromhex(args.color[1:]))+(0,));ink.putalpha(fg)
        im=Image.alpha_composite(outline,ink)
    dst=Path(args.out);dst.parent.mkdir(parents=True,exist_ok=True);im.save(dst);print(dst)
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,RuntimeError,FileNotFoundError) as e: print('Error:',e,file=sys.stderr);sys.exit(1)
