#!/usr/bin/env python3
"""Structural + actual-pixel QA for a Visual Atlas ZIP. Does not claim semantic art review."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import sys
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFont
from tools.validate_visual_pack import check

MAX_REGIONS = 10000
CONTACT_COLS = 8
THUMB = (156, 170)

def scan(archive: Path, report_dir: Path, strict: bool = False) -> dict:
    errors = list(check(archive))
    result = {'archive': archive.name, 'validation': 'FAIL' if errors else 'PASS', 'errors': errors,
              'warnings': [], 'regions': [], 'sequences': 0, 'compositions': 0,
              'state_sets': 0, 'packs': 0, 'contact_sheets': [],
              'visual_review': 'NOT VERIFIED BY AUTOMATION'}
    report_dir.mkdir(parents=True, exist_ok=True)
    if errors:
        save_report(result, report_dir)
        return result
    with zipfile.ZipFile(archive) as z:
        names = set(z.namelist())
        manifests = []
        for name in sorted(names):
            if not name.endswith('.json'):
                continue
            # Existing structural validator has already verified member safety and size.
            try: pack = json.loads(z.read(name))
            except (ValueError, UnicodeDecodeError): continue
            if pack.get('schema') == 'smi-visual-pack/1': manifests.append((name, pack))
        result['packs'] = len(manifests)
        all_regions = []
        images = {}
        for manifest_name, pack in manifests:
            prefix = manifest_name.rpartition('/')[0]
            for asset in pack['assets']:
                kind=asset['kind']
                if kind=='sequence':result['sequences']+=1
                elif kind=='composition':result['compositions']+=1
                elif kind=='state_set':result['state_sets']+=1
                if kind != 'region': continue
                texture = pack['textures'][asset['texture']]
                full = (prefix+'/' if prefix else '')+texture['path']
                if full not in images:
                    im = Image.open(io.BytesIO(z.read(full)))
                    im.load()
                    images[full] = im.convert('RGBA')
                im=images[full]
                x,y,w,h=asset['rect_px']
                crop=im.crop((x,y,x+w,y+h))
                a=crop.getchannel('A')
                occupied=a.getbbox()
                if not occupied:
                    result['errors'].append(f"{asset['id']}: empty or fully transparent crop")
                    state='FAIL';cover=0.0;touch=False
                else:
                    # Distinguish full-bleed photos/backgrounds from isolated sprites.
                    cover=sum(a.histogram()[1:])/(w*h)
                    touch=(occupied[0]==0 or occupied[1]==0 or occupied[2]==w or occupied[3]==h)
                    state='REVIEW' if touch else 'PASS'
                    if touch:result['warnings'].append(f"{asset['id']}: visible pixels reach crop boundary (may be intentional full-bleed)")
                    if cover < 0.001:
                        state='REVIEW'
                        result['warnings'].append(f"{asset['id']}: very low visible pixel coverage")
                entry={'id':asset['id'],'manifest':manifest_name,'texture':full,
                       'rect_px':[x,y,w,h],'alpha_bbox_px':list(occupied) if occupied else None,
                       'coverage_ratio':round(cover,5),'border_touch':touch,
                       'crop_sha256_rgba':hashlib.sha256(crop.tobytes()).hexdigest(),'pixel_scan':state}
                result['regions'].append(entry)
                all_regions.append((entry,crop))
                if len(all_regions)>MAX_REGIONS:
                    result['errors'].append(f'More than {MAX_REGIONS} regions; split into multiple ZIPs')
                    break
        for start in range(0,len(all_regions),64):
            page=all_regions[start:start+64]
            width=CONTACT_COLS*THUMB[0]; height=math.ceil(len(page)/CONTACT_COLS)*THUMB[1]
            sheet=Image.new('RGB',(width,height),'#172336')
            d=ImageDraw.Draw(sheet)
            for i,(entry,crop) in enumerate(page):
                px=(i%CONTACT_COLS)*THUMB[0];py=(i//CONTACT_COLS)*THUMB[1]
                # Alpha checker preview; only generated QA pages use non-transparent backgrounds.
                tile=Image.new('RGBA',(132,132),(44,60,82,255)); td=ImageDraw.Draw(tile)
                for yy in range(0,132,12):
                    for xx in range(0,132,12):
                        if (xx//12+yy//12)%2 == 0: td.rectangle((xx,yy,xx+11,yy+11),fill=(32,48,68,255))
                cp=crop.copy();cp.thumbnail((128,128),Image.Resampling.LANCZOS)
                tile.alpha_composite(cp,((132-cp.width)//2,(132-cp.height)//2))
                sheet.paste(tile.convert('RGB'),(px+12,py+4))
                d.text((px+6,py+139),f"#{start+i+1} {entry['id'].split('.')[-1][:16]}",fill='white')
                d.text((px+6,py+155),entry['pixel_scan'],fill='#ffb86c' if entry['pixel_scan']!='PASS' else '#90d4aa')
            name=f'contact-{start//64+1:03d}.png'
            sheet.save(report_dir/name)
            result['contact_sheets'].append(name)
    if strict and result['warnings']:
        result['errors'].append(f'Strict isolated-sprite policy: {len(result["warnings"])} pixel warnings')
    result['validation']='FAIL' if result['errors'] else 'PASS'
    save_report(result,report_dir)
    return result

def save_report(result,report_dir):
    (report_dir/'qa-report.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    summary=(f"VISUAL ATLAS QA RECEIPT\nArchive: {result['archive']}\n"
       f"Structural and pixel validation: {result['validation']}\n"
       f"Packs: {result['packs']} | Regions: {len(result['regions'])} | Sequences: {result['sequences']} | Compositions: {result['compositions']} | States: {result['state_sets']}\n"
       f"Regions scanned: {len(result['regions'])} | Contact sheets: {len(result['contact_sheets'])}\n"
       f"Warnings: {len(result['warnings'])} | Errors: {len(result['errors'])}\n"
       f"Visual-semantic inspection: {result['visual_review']}\n"
       f"Status: {'NEEDS FIXES' if result['errors'] else 'READY FOR VISUAL REVIEW / BUILDER PREVIEW'}\n"
       f"Details: {report_dir/'qa-report.json'}\n")
    (report_dir/'qa-receipt.txt').write_text(summary,encoding='utf-8')
    print(summary)
    for msg in result['errors'][:10]:print('ERROR:',msg,file=sys.stderr)
    for msg in result['warnings'][:10]:print('WARN:',msg,file=sys.stderr)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('zip_path',type=Path)
    p.add_argument('--out',type=Path,help='QA output directory (default: <ZIP-stem>-qa)')
    p.add_argument('--strict',action='store_true',help='Require isolated sprites with no edge contacts; inappropriate for full-bleed artwork')
    args=p.parse_args()
    output=args.out or args.zip_path.parent/(args.zip_path.stem+'-qa')
    data=scan(args.zip_path,output,args.strict)
    return 0 if not data['errors'] else 1

if __name__=='__main__':
    sys.exit(main())
