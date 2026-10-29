#!/usr/bin/env python3
"""Single-manifest lookup, exact crop, and validation for Icon Atlas v0.3."""
import argparse, hashlib, json, sys, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def load():
 m=json.loads((ROOT/'manifest.json').read_text())
 if m.get('schema')!='smi-icon-atlas/2':raise ValueError('Unsupported manifest schema')
 return m

def validate(deep=False):
 m=load();errors=[];index={s['path']:s for s in m['sheets']};seen=set();positions=set()
 for sheet in m['sheets']:
  name=sheet['path'];p=ROOT/name
  if not p.is_file():errors.append('Missing '+name);continue
  if hashlib.sha256(p.read_bytes()).hexdigest()!=sheet['sha256']:errors.append('Checksum '+name)
  with p.open('rb') as f: head=f.read(26)
  if head[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack('>II',head[16:24])!=(2304,768) or head[25]!=6:errors.append('PNG geometry or alpha '+name)
  for key in ('foreground_mask','black_outline'):
   if not (ROOT/sheet[key]).is_file():errors.append('Missing '+sheet[key])
 for icon in m['icons']:
  ident=icon['id'];s=icon['sheet'];r=icon['rect_px'];c=icon['cell']
  if ident in seen:errors.append('duplicate ID '+ident)
  seen.add(ident)
  if s not in index:errors.append('unknown sheet '+s);continue
  if c['x'] not in range(24) or c['y'] not in range(8):errors.append('invalid cell '+ident)
  if (s,c['x'],c['y']) in positions:errors.append('collision '+ident)
  positions.add((s,c['x'],c['y']))
  if r!={'x':c['x']*96,'y':c['y']*96,'w':96,'h':96}:errors.append('invalid crop '+ident)
 if deep:
  try:from PIL import Image
  except ImportError:raise RuntimeError('Install Pillow to run deep validation')
  for sheet in m['sheets']:
   im=Image.open(ROOT/sheet['path']).convert('RGBA')
   if im.getpixel((0,0))[3]!=0:errors.append('nontransparent corner '+sheet['path'])
   for ic in (i for i in m['icons'] if i['sheet']==sheet['path']):
    r=ic['rect_px'];crop=im.crop((r['x'],r['y'],r['x']+96,r['y']+96))
    if not crop.getchannel('A').getbbox():errors.append('empty '+ic['id'])
    # source candidate manifest hashes PNG crop bytes (not pixels). semantic geometries only are checked here.
 return errors

def main():
 parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='cmd',required=True)
 sub.add_parser('validate').add_argument('--deep',action='store_true')
 search=sub.add_parser('search');search.add_argument('query')
 info=sub.add_parser('info');info.add_argument('id')
 crop=sub.add_parser('crop');crop.add_argument('id');crop.add_argument('--out',required=True)
 tint=sub.add_parser('tint');tint.add_argument('id');tint.add_argument('--color',required=True);tint.add_argument('--out',required=True)
 args=parser.parse_args();m=load()
 if args.cmd=='validate':
  errors=validate(args.deep)
  for e in errors:print('FAIL',e,file=sys.stderr)
  print(f'{len(m["icons"])} icons, {len(m["sheets"])} sheets:', 'PASS' if not errors else 'FAIL')
  return bool(errors)
 if args.cmd=='search':
  q=args.query.casefold();found=[i for i in m['icons'] if q in (i['id']+' '+i['name']+' '+' '.join(i['tags'])).casefold()]
  for i in found[:30]:print(i['id'],'·',i['name'])
  return 0
 icon=next((i for i in m['icons'] if i['id']==args.id),None)
 if icon is None:raise ValueError('Unknown icon ID: '+args.id)
 if args.cmd=='info':print(json.dumps(icon,indent=2));return 0
 from PIL import Image
 r=icon['rect_px']; sheet=next(s for s in m['sheets'] if s['path']==icon['sheet']);box=(r['x'],r['y'],r['x']+96,r['y']+96)
 if args.cmd=='crop':im=Image.open(ROOT/sheet['path']).convert('RGBA').crop(box)
 else:
  import re
  if not re.fullmatch(r'#[0-9A-Fa-f]{6}',args.color):raise ValueError('Use #RRGGBB')
  outline=Image.open(ROOT/sheet['black_outline']).convert('RGBA').crop(box)
  mask=Image.open(ROOT/sheet['foreground_mask']).convert('RGBA').crop(box).getchannel('A')
  fg=Image.new('RGBA',(96,96),tuple(bytes.fromhex(args.color[1:]))+(0,));fg.putalpha(mask)
  im=Image.alpha_composite(outline,fg)
 dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True);im.save(dest);print(dest)
 return 0
if __name__=='__main__':
 try:sys.exit(main())
 except (ValueError,RuntimeError) as e:print(e,file=sys.stderr);sys.exit(1)
