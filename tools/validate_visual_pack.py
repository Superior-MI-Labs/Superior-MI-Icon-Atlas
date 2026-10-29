#!/usr/bin/env python3
"""Validate a Visual Atlas pack ZIP: JSON Schema, dependencies and actual image geometry."""
from __future__ import annotations
import argparse
import io
import json
import sys
import zipfile
from pathlib import Path
from PIL import Image
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
MAX_ARCHIVE_BYTES=120*1024*1024
MAX_TEXTURE_BYTES=24*1024*1024

def validate_tracks(tracks, duration, label):
    errors=[]
    seen=set()
    allowed={'x','y','opacity','scale_x','scale_y','rotation_deg'}
    if len(tracks)>6:return [f'{label}: too many tracks']
    for track in tracks:
        prop=track['property']
        if prop not in allowed:errors.append(f'{label}: invalid track {prop}')
        if prop in seen:errors.append(f'{label}: duplicate track {prop}')
        seen.add(prop)
        if len(track['keyframes'])>240:errors.append(f'{label}: too many keyframes')
        prev=-1
        for key in track['keyframes']:
            time=key['time_ms'];val=key['value']
            if time<=prev or duration is not None and time>duration:errors.append(f'{label}: invalid keyframe time {time}')
            if prop=='opacity' and not 0<=val<=1:errors.append(f'{label}: opacity out of bounds')
            if prop in ('scale_x','scale_y') and not 0<=val<=20:errors.append(f'{label}: scale out of bounds')
            prev=time
    return errors

def check(pack_path:Path):
    errors=[]
    if not pack_path.is_file():return [f'ZIP missing: {pack_path}']
    if pack_path.stat().st_size>MAX_ARCHIVE_BYTES:return ['ZIP exceeds 120 MB compressed size limit']
    schema=json.loads((ROOT/'schemas/smi-visual-pack-v1.schema.json').read_text())
    with zipfile.ZipFile(pack_path) as z:
        bad=z.testzip()
        if bad:errors.append(f'Corrupted ZIP entry: {bad}')
        files={name for name in z.namelist() if not name.endswith('/')}
        if len(files)>4000:errors.append('More than 4000 entries')
        expanded=sum(z.getinfo(name).file_size for name in files)
        if expanded>MAX_ARCHIVE_BYTES:errors.append('ZIP exceeds 120 MB expanded-size limit')
        for name in files:
            if z.getinfo(name).file_size>MAX_TEXTURE_BYTES:errors.append('Oversized entry '+name)
        for name in files:
            if name.startswith('/') or '\\' in name or '..' in Path(name).parts or ':' in name:
                errors.append('Unsafe path: '+name)
        candidates=[]
        for name in sorted(files,key=len):
            if name.endswith('.json') and z.getinfo(name).file_size<MAX_TEXTURE_BYTES:
                try:
                    pack=json.loads(z.read(name))
                    if pack.get('schema')=='smi-visual-pack/1':candidates.append((name,pack))
                except (ValueError,UnicodeDecodeError):pass
        if not candidates:errors.append('No smi-visual-pack/1 JSON manifest found')
        for manifest_name,pack in candidates:
            errors.extend(f'{manifest_name}: {e.message}' for e in Draft202012Validator(schema).iter_errors(pack))
            if errors:continue
            prefix=manifest_name.rpartition('/')[0]
            def resolved(name):return f'{prefix}/{name}' if prefix else name
            for tid,t in pack['textures'].items():
                full=resolved(t['path'])
                if full not in files:errors.append(f'Missing image {full}');continue
                if z.getinfo(full).file_size>MAX_TEXTURE_BYTES:errors.append(f'Oversized image {full}');continue
                try:
                    with Image.open(io.BytesIO(z.read(full))) as img:
                        if img.size!=(t['width_px'],t['height_px']):errors.append(f'Wrong image dimensions {full}')
                except Exception as exc:errors.append(f'Invalid image {full}: {exc}')
            ids={a['id']:a for a in pack['assets']}
            if len(ids)!=len(pack['assets']):errors.append('Duplicate asset IDs')
            seen=set();active=set()
            def walk(asset_id):
                if asset_id in active:errors.append('Reference cycle: '+asset_id);return
                if asset_id in seen:return
                a=ids.get(asset_id)
                if a is None:errors.append('Unknown referenced asset '+asset_id);return
                active.add(asset_id)
                for ref in [*([x['asset'] for x in a.get('frames',[])]),*([x['asset'] for x in a.get('layers',[])]),*(a.get('states') or {}).values()]:walk(ref)
                active.remove(asset_id);seen.add(asset_id)
            for a in pack['assets']:
                if a['kind']=='region':
                    t=pack['textures'].get(a.get('texture'))
                    if not t:errors.append('Unknown texture '+a['id']);continue
                    x,y,w,h=a['rect_px']
                    if x+w>t['width_px'] or y+h>t['height_px']:errors.append('Out-of-bounds rect '+a['id'])
                    if a.get('nine_slice_px'):
                        l,top,r,bot=a['nine_slice_px']
                        if l+r>w or top+bot>h:errors.append('Nine-slice too large '+a['id'])
                if a['kind']=='state_set' and a['default_state'] not in a['states']:errors.append('Missing default state '+a['id'])
                if a['kind']=='composition':
                    duration=a.get('duration_ms')
                    for layer in a['layers']:
                        errors.extend(validate_tracks(layer.get('tracks',[]),duration,a['id']+'/'+layer['id']))

                        for key in [layer.get('state_from_input'),(layer.get('visible_when') or {}).get('input'),(layer.get('clip') or {}).get('input'),(layer.get('position_from_input') or {}).get('input')]:
                            if key and key not in a.get('inputs',{}):errors.append('Undeclared input '+key+' in '+a['id'])
                walk(a['id'])
    return errors

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('zip_path',type=Path)
    args=parser.parse_args();errs=check(args.zip_path)
    for e in errs:print('ERROR:',e,file=sys.stderr)
    print('PASS: Visual Atlas ZIP valid' if not errs else f'FAIL: {len(errs)} errors')
    sys.exit(bool(errs))
