#!/usr/bin/env python3
"""Visual Atlas AI pack release gate: structural + visual QA + authored requirements.

This is a deterministic *declarative* acceptance runner, not an AI evaluator.
It never executes instructions, scripts or code from an uploaded ZIP.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import sys
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from tools.qualify_asset_zip import scan

TYPES={'asset_kind','sequence_frames','sequence_distinct_frames','state_contains','preset_selects','input_declared','tag_contains','input_range','layer_order','output_maps_from_input','event_declared','layer_uses_input'}

def check_acceptance(archive:Path,spec:dict)->list[str]:
    if not isinstance(spec,dict) or spec.get('schema')!='smi-ai-acceptance/1':return ['Acceptance file must use schema smi-ai-acceptance/1']
    checks=spec.get('checks')
    if not isinstance(checks,list) or not checks or len(checks)>100:return ['Provide 1..100 explicit request-specific checks']
    errors=[]
    with ZipFile(archive) as z:
        files={n for n in z.namelist() if not n.endswith('/')}
        entries={}
        for name in sorted(files):
            if name.endswith('.json') and z.getinfo(name).file_size<1_000_000:
                try:pack=json.loads(z.read(name))
                except (UnicodeDecodeError,ValueError):continue
                if pack.get('schema')=='smi-visual-pack/1':
                    for a in pack['assets']:
                        if a['id'] in entries:errors.append('Duplicate asset ID '+a['id'])
                        entries[a['id']]=(a,pack,name)
        for num,c in enumerate(checks,1):
            if not isinstance(c,dict) or c.get('type') not in TYPES or not isinstance(c.get('asset'),str):
                errors.append(f'Check {num}: requires known type and asset ID');continue
            aid=c['asset'];obj=entries.get(aid)
            if obj is None:errors.append(f'Check {num}: missing asset {aid}');continue
            a,pack,manifest=obj;t=c['type']
            if t=='asset_kind':
                if a['kind']!=c.get('kind'):errors.append(f'Check {num}: {aid} kind {a["kind"]!r}, expected {c.get("kind")!r}')
            elif t=='sequence_frames':
                count=len(a.get('frames',[]));at_least=c.get('at_least')
                if a['kind']!='sequence' or not isinstance(at_least,int) or at_least<=0 or count<at_least:
                    errors.append(f'Check {num}: {aid} needs sequence with >= {at_least} frames; found {count}')
            elif t=='sequence_distinct_frames':
                if a['kind']!='sequence':errors.append(f'Check {num}: {aid} is not a sequence');continue
                hashes=[]
                for f in a['frames']:
                    region=entries.get(f['asset'])
                    if not region or region[0]['kind']!='region':errors.append(f'Check {num}: only direct region frame checks supported for {aid}');break
                    r,p,m=region
                    tex=p['textures'][r['texture']]['path']
                    path=(PurePosixPath(m).parent / tex).as_posix()
                    if path not in files:errors.append(f'Check {num}: missing texture {path}');break
                    with Image.open(io.BytesIO(z.read(path))) as im:
                        x,y,w,h=r['rect_px'];img=im.convert('RGBA').crop((x,y,x+w,y+h))
                        hashes.append(hashlib.sha256(img.tobytes()).hexdigest())
                distinct=c.get('at_least',2)
                if not isinstance(distinct,int) or distinct<2 or len(set(hashes))<distinct:errors.append(f'Check {num}: only {len(set(hashes))} distinct frame crops in {aid}; require {distinct}')
            elif t=='state_contains':
                if a['kind']!='state_set' or c.get('state') not in a.get('states',{}):errors.append(f'Check {num}: missing state {c.get("state")} in {aid}')
            elif t=='preset_selects':
                preset=a.get('presets',{}).get(c.get('preset'),{})
                slot=(preset.get('slots') or {}).get(c.get('slot'))
                if a['kind']!='composition' or slot!=c.get('option'):errors.append(f'Check {num}: preset {c.get("preset")}/{c.get("slot")} selects {slot}, not {c.get("option")}')
            elif t=='input_declared':
                inp=a.get('inputs',{}).get(c.get('input'),{})
                if inp.get('type')!=c.get('input_type'):errors.append(f'Check {num}: input {c.get("input")} type mismatch in {aid}')
            elif t=='input_range':
                defn=a.get('inputs',{}).get(c.get('input'),{})
                if a['kind']!='composition' or defn.get('type')!='number' or defn.get('min')!=c.get('min') or defn.get('max')!=c.get('max'):
                    errors.append(f'Check {num}: numeric input {c.get("input")} range mismatch in {aid}')
            elif t=='layer_order':
                order=[l.get('id') for l in a.get('layers',[])]
                before,after=c.get('before'),c.get('after')
                if a['kind']!='composition' or before not in order or after not in order or order.index(before)>=order.index(after):
                    errors.append(f'Check {num}: layer {before} must render before {after} in {aid}')
            elif t=='output_maps_from_input':
                outputs=a.get('behavior',{}).get('outputs',{})
                if outputs.get(c.get('output'),{}).get('from_input')!=c.get('input'):
                    errors.append(f'Check {num}: output {c.get("output")} not mapped from input {c.get("input")}')
            elif t=='event_declared':
                if c.get('event') not in a.get('behavior',{}).get('on',{}):
                    errors.append(f'Check {num}: event {c.get("event")} is not declared for {aid}')
            elif t=='layer_uses_input':
                layer=next((l for l in a.get('layers',[]) if l.get('id')==c.get('layer')),None)
                use=c.get('binding')
                if use not in ('clip','position_from_input','visible_when','state_from_input'):
                    errors.append(f'Check {num}: unsupported layer binding {use}')
                elif not layer or (layer.get(use) if use=='state_from_input' else (layer.get(use) or {}).get('input')) != c.get('input'):
                    errors.append(f'Check {num}: layer {c.get("layer")} does not bind {use} to input {c.get("input")}')
            elif t=='tag_contains':
                if c.get('tag') not in a.get('tags',[]):errors.append(f'Check {num}: tag {c.get("tag")} absent from {aid}')
    return errors

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip',type=Path)
    parser.add_argument('--acceptance',type=Path,required=True,help='Creator-specific JSON checks: REQUIRED')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    try:
        spec=json.loads(args.acceptance.read_text(encoding='utf-8'))
        report=scan(args.zip,args.out)
        errors=check_acceptance(args.zip,spec) if report.get('validation')=='PASS' else ['Cannot evaluate acceptance: source archive structural/pixel checks failed']
    except Exception as e:
        print('FAIL: Acceptance runner could not execute:',e);return 1
    passed=report.get('validation')=='PASS' and not errors
    receipt={'schema':'smi-ai-handoff-receipt/1','archive':args.zip.name,'brief':spec.get('intent',''),
             'manifest_pixel_checks':report.get('validation'),'acceptance_status':'PASS' if not errors else 'FAIL',
             'acceptance_checks':len(spec.get('checks',[])),'acceptance_errors':errors,
             'visual_semantic_review':'NOT VERIFIED BY AUTOMATION',
             'delivery_status':'READY FOR VISUAL REVIEW' if passed else 'NEEDS FIXES'}
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'acceptance-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('\nCREATOR-SPECIFIC ACCEPTANCE:',receipt['acceptance_status'],f'({receipt["acceptance_checks"]} declared checks)')
    for error in errors:print('FAIL:',error)
    print('PIXEL / MANIFEST:',receipt['manifest_pixel_checks'])
    print('VISUAL SEMANTICS:',receipt['visual_semantic_review'])
    print('DELIVERY:',receipt['delivery_status'])
    print('Receipt:',args.out/'acceptance-receipt.json')
    return 0 if passed else 1

if __name__=='__main__':raise SystemExit(main())
