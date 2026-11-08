#!/usr/bin/env python3
"""Validate an offline Visual Atlas ZIP (one or many manifests) without executing its contents."""
from __future__ import annotations
import argparse
import io
import json
import sys
import zipfile
from pathlib import Path, PurePosixPath
from PIL import Image
from jsonschema import Draft202012Validator
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.validate_slots import check as check_slots

ROOT = Path(__file__).resolve().parents[1]
MAX_ARCHIVE_BYTES = 120 * 1024 * 1024
MAX_TEXTURE_BYTES = 24 * 1024 * 1024
MAX_TEXTURE_PIXELS = 8192 * 8192

def safe_path(name):
    return isinstance(name, str) and 0 < len(name) < 512 and not name.startswith('/') and not any(x in name for x in ('\\', ':', '\x00')) and all(p not in ('', '.', '..') for p in name.split('/'))

def validate_tracks(tracks, duration, label):
    errors, seen = [], set()
    allowed = {'x', 'y', 'opacity', 'scale_x', 'scale_y', 'rotation_deg'}
    if len(tracks) > 6: return [f'{label}: too many tracks']
    for track in tracks:
        prop = track['property']
        if prop not in allowed: errors.append(f'{label}: invalid track {prop}')
        if prop in seen: errors.append(f'{label}: duplicate track {prop}')
        seen.add(prop)
        if len(track['keyframes']) > 240: errors.append(f'{label}: too many keyframes')
        prev = -1
        for key in track['keyframes']:
            time, val = key['time_ms'], key['value']
            if time <= prev or duration is not None and time > duration: errors.append(f'{label}: invalid keyframe time {time}')
            if prop == 'opacity' and not 0 <= val <= 1: errors.append(f'{label}: opacity out of bounds')
            if prop in ('scale_x', 'scale_y') and not 0 <= val <= 20: errors.append(f'{label}: scale out of bounds')
            prev = time
    return errors

def validate_behavior(asset):
    errors = []
    behavior = asset.get('behavior')
    if behavior is None: return errors
    inputs = asset.get('inputs') or {}
    for key, output in behavior.get('outputs', {}).items():
        if output['from_input'] not in inputs: errors.append(f'{asset["id"]}: unknown output source {output["from_input"]}')
    for event, actions in behavior.get('on', {}).items():
        for action in actions:
            if action['op'] == 'emit': continue
            key = action['input']
            if key not in inputs: errors.append(f'{asset["id"]}: unknown behavior input {key}'); continue
            defn = inputs[key]
            if action['op'] == 'toggle' and defn['type'] != 'boolean':errors.append(f'{asset["id"]}: cannot toggle non-boolean {key}')
            if action['op'] == 'set' and 'value' in action:
                val = action['value']
                if defn['type'] == 'boolean' and not isinstance(val, bool): errors.append(f'{asset["id"]}: invalid boolean set {key}')
                if defn['type'] == 'number' and (isinstance(val, bool) or not isinstance(val, (int, float)) or val < defn.get('min',float('-inf')) or val > defn.get('max',float('inf'))): errors.append(f'{asset["id"]}: invalid numeric set {key}')
                if defn['type'] == 'enum' and val not in defn['values']: errors.append(f'{asset["id"]}: invalid enum set {key}')
    return errors

def validate_preview_profiles(packs, ids):
    """Profile metadata adapts input to already-declared states/events, not gameplay."""
    problems, names = [], set()
    for pack in packs:
        for profile in pack.get('preview_profiles', []):
            label = profile['id']
            if label in names:problems.append('Duplicate preview profile: ' + label)
            names.add(label)
            asset = ids.get(profile['asset'])
            if not asset or asset['kind'] not in ('state_set', 'composition'):
                problems.append(label + ': missing or incompatible target asset')
                continue
            def target_ok(target):
                if not isinstance(target, dict) or len(target) != 1:return False
                if asset['kind'] == 'state_set':
                    return target.get('state') in asset.get('states', {})
                return target.get('event') in (asset.get('behavior') or {}).get('on', {})
            if profile.get('neutral') is not None and not target_ok(profile['neutral']):
                problems.append(label + ': invalid neutral target')
            for name, action in profile['actions'].items():
                if not target_ok(action['target']):
                    problems.append(label + ': unknown state/event for ' + name)
                if action['mode'] == 'hold' and not target_ok(profile.get('neutral')):
                    problems.append(label + ': hold action missing neutral target')
            pressed = set()
            for bind in profile['bindings']:
                if bind['action'] not in profile['actions']:
                    problems.append(label + ': unknown bound action ' + bind['action'])
                key = (bind['device'], bind.get('code', bind.get('button')))
                if key in pressed:problems.append(label + ': duplicate physical binding ' + str(key))
                pressed.add(key)
    return problems


def validate_stat_profiles(packs, ids):
    """Stat definitions remain canonical; visual inputs are presentation bindings."""
    problems, names = [], set()
    for pack in packs:
        for profile in pack.get('stat_profiles', []):
            label=profile['id']
            if label in names:problems.append('Duplicate stat profile: '+label)
            names.add(label)
            asset=ids.get(profile['asset'])
            if not asset or asset['kind']!='composition':
                problems.append(label+': stat target must be a composition')
                continue
            stats=profile['stats']
            for key,stat in stats.items():
                if stat['max']<=stat['min'] or not stat['min']<=stat['initial']<=stat['max']:
                    problems.append(label+': invalid stat range '+key)
            for key,action in profile['actions'].items():
                if not action.get('costs') and not action.get('deltas') and not action.get('emit'):
                    problems.append(label+': empty stat action '+key)
                for stat,cost in action.get('costs',{}).items():
                    if stat not in stats or cost<=0:problems.append(label+': invalid cost '+key+'/'+stat)
                for stat,delta in action.get('deltas',{}).items():
                    if stat not in stats or delta==0:problems.append(label+': invalid delta '+key+'/'+stat)
                event=action.get('emit')
                if event and event not in (asset.get('behavior') or {}).get('on',{}):
                    problems.append(label+': unknown visual event '+key+'/'+event)
            bound=set()
            for bind in profile['bindings']:
                stat=stats.get(bind['stat'])
                inp=asset.get('inputs',{}).get(bind['input'])
                if (not stat or not inp or inp['type']!='number' or
                    stat['min']<inp.get('min',0) or stat['max']>inp.get('max',1) or
                    bind['input'] in bound):
                    problems.append(label+': invalid stat binding '+bind['stat']+'/'+bind['input'])
                bound.add(bind['input'])
    return problems


def check(pack_path: Path):
    errors = []
    if not pack_path.is_file():return [f'ZIP missing: {pack_path}']
    if pack_path.stat().st_size > MAX_ARCHIVE_BYTES:return ['ZIP exceeds 120 MB compressed size limit']
    schema = json.loads((ROOT/'schemas/smi-visual-pack-v1.schema.json').read_text())
    cschema = json.loads((ROOT/'schemas/smi-visual-collection-v1.schema.json').read_text())
    try: z = zipfile.ZipFile(pack_path)
    except (OSError, zipfile.BadZipFile) as exc: return [f'Invalid ZIP: {exc}']
    with z:
        infos = [i for i in z.infolist() if not i.is_dir()]
        files = {i.filename for i in infos}
        if len(infos) != len(files): errors.append('Duplicate ZIP member names')
        if len(infos) > 4000: errors.append('More than 4000 entries')
        if sum(i.file_size for i in infos) > MAX_ARCHIVE_BYTES: errors.append('ZIP exceeds 120 MB expanded-size limit')
        for i in infos:
            if i.file_size > MAX_TEXTURE_BYTES: errors.append('Oversized member ' + i.filename)
            if not safe_path(i.filename): errors.append('Unsafe path: ' + i.filename)
            if (i.external_attr >> 16) & 0o170000 == 0o120000: errors.append('Symlink entry forbidden: ' + i.filename)
        if errors:return errors
        if z.testzip() is not None:return ['Corrupted ZIP member']
        candidates, index, index_path = [], None, None
        for name in sorted(files):
            if not name.endswith('.json'): continue
            try: data = json.loads(z.read(name))
            except (ValueError, UnicodeDecodeError): continue
            if data.get('schema') == 'smi-visual-pack/1':candidates.append((name, data))
            elif data.get('schema') == 'smi-visual-collection/1':
                if index is not None:errors.append('Multiple collection indexes')
                index, index_path = data, name
        if not candidates:return errors+['No smi-visual-pack/1 manifest found']
        if len(candidates) > 96:return errors+['More than 96 manifests in ZIP']
        if index is not None:
            errors.extend('Collection: ' + e.message for e in Draft202012Validator(cschema).iter_errors(index))
            if errors:return errors
            root = index_path.rpartition('/')[0]
            listed = []
            for group in index['packs']:
                relative = group['manifest']
                resolved = root + '/' + relative if root else relative
                if not safe_path(relative) or resolved not in files:errors.append('Missing or unsafe manifest in collection index: ' + relative)
                listed.append(resolved)
            if len(set(listed)) != len(listed): errors.append('Collection index repeats a manifest')
            if set(listed) != {name for name, _ in candidates}: errors.append('Collection index must enumerate every Visual Atlas manifest')
        ids, pack_ids, valid_packs, repeated_layers = {}, set(), [], []
        for manifest_name, pack in candidates:
            problems = list(Draft202012Validator(schema).iter_errors(pack))
            errors.extend(f'{manifest_name}: {e.message}' for e in problems)
            if problems: continue
            valid_packs.append(pack)
            if pack['pack_id'] in pack_ids: errors.append('Duplicate pack_id: '+pack['pack_id'])
            pack_ids.add(pack['pack_id'])
            for asset in pack['assets']:
                if asset['id'] in ids: errors.append('Duplicate asset ID: ' + asset['id'])
                ids[asset['id']] = asset
            prefix = manifest_name.rpartition('/')[0]
            for tex in pack['textures'].values():
                path = tex['path']
                full = prefix + '/' + path if prefix else path
                if not safe_path(path) or not safe_path(full):errors.append('Unsafe texture path: '+str(path));continue
                if full not in files:errors.append(f'Missing image {full}');continue
                if z.getinfo(full).file_size > MAX_TEXTURE_BYTES:errors.append(f'Oversized image {full}');continue
                try:
                    with Image.open(io.BytesIO(z.read(full))) as img:
                        if img.size != (tex['width_px'], tex['height_px']):errors.append(f'Wrong image dimensions {full}')
                        if img.width * img.height > MAX_TEXTURE_PIXELS:errors.append(f'Excessive image pixels {full}')
                except Exception as exc: errors.append(f'Invalid image {full}: {exc}')
            for asset in pack['assets']:
                errors.extend(validate_behavior(asset))
                if asset['kind'] == 'region':
                    t = pack['textures'].get(asset['texture'])
                    if t is None: errors.append('Unknown texture ' + asset['id']);continue
                    x,y,w,h = asset['rect_px']
                    if x+w > t['width_px'] or y+h > t['height_px']:errors.append('Out-of-bounds rect ' + asset['id'])
                    # Trimming is opt-in: preserve legacy logical_size_px behavior.
                    # An explicit trim must fit the authored full logical pose.
                    if 'trim_offset_px' in asset:
                        logical = asset.get('logical_size_px')
                        if not logical:
                            errors.append('Trim offset requires logical canvas ' + asset['id'])
                        else:
                            ox, oy = asset['trim_offset_px']
                            lw, lh = logical
                            if ox < 0 or oy < 0 or ox + w > lw or oy + h > lh:
                                errors.append('Trimmed region outside logical canvas ' + asset['id'])
                        if asset.get('nine_slice_px'):
                            errors.append('Trim and nine-slice cannot be combined ' + asset['id'])
                    if asset.get('nine_slice_px'):
                        left,top,right,bottom = asset['nine_slice_px']
                        if left+right > w or top+bottom > h:errors.append('Nine-slice too large ' + asset['id'])
                elif asset['kind'] == 'state_set' and asset['default_state'] not in asset['states']:
                    errors.append('Missing default state ' + asset['id'])
                elif asset['kind'] == 'composition':
                    for key, inp in asset.get('inputs', {}).items():
                        if inp.get('type') == 'number':
                            if ('min' in inp) != ('max' in inp):
                                errors.append(f'{asset["id"]}: numeric input {key} must specify both min and max or neither')
                            if 'min' in inp and 'max' in inp and inp['max'] <= inp['min']:
                                errors.append(f'{asset["id"]}: numeric input {key} has invalid min/max')
                            if 'min' in inp and 'max' in inp and not inp['min'] <= inp['default'] <= inp['max']:
                                errors.append(f'{asset["id"]}: numeric input {key} default outside range')
                    repeat_layers=[layer for layer in asset['layers'] if layer.get('repeat')]
                    if len(repeat_layers)>1:errors.append(f'{asset["id"]}: only one repeated layer supported per composition')
                    repeated_layers.extend((asset,layer) for layer in repeat_layers)
                    for layer in asset['layers']:
                        errors.extend(validate_tracks(layer.get('tracks',[]),asset.get('duration_ms'),asset['id']+'/'+layer['id']))
                        for key in [layer.get('state_from_input'),(layer.get('visible_when') or {}).get('input'),(layer.get('clip') or {}).get('input'),(layer.get('position_from_input') or {}).get('input')]:
                            if key and key not in asset.get('inputs',{}):errors.append('Undeclared input '+key+' in '+asset['id'])
        for asset,layer in repeated_layers:
            r=layer['repeat']
            target=ids.get(layer.get('asset'))
            if not target or target['kind']!='state_set' or layer.get('slot'):
                errors.append(f'{asset["id"]}: repeat requires a directly referenced state_set')
                continue
            for key in (r['count_input'],r['value_input'],r['columns_input']):
                inp=asset.get('inputs',{}).get(key)
                if not inp or inp.get('type')!='number' or any(k not in inp for k in ('min','max')):
                    errors.append(f'{asset["id"]}: repeat input {key} must have a numeric range')
            for key in (r['count_input'],r['columns_input']):
                inp=asset.get('inputs',{}).get(key,{})
                if inp.get('min',0)<1 or inp.get('max',257)>256 or inp.get('step',1)!=1:
                    errors.append(f'{asset["id"]}: repeat count/column {key} requires integer 1..256 step 1')
            if asset.get('inputs',{}).get(r['value_input'],{}).get('step',1)!=1:
                errors.append(f'{asset["id"]}: repeat value requires integer steps')
            if set(r['levels'])-set(target['states']):
                errors.append(f'{asset["id"]}: repeat levels not in state_set {target["id"]}')
            count_max=asset.get('inputs',{}).get(r['count_input'],{}).get('max',0)
            value_max=asset.get('inputs',{}).get(r['value_input'],{}).get('max',0)
            if value_max<count_max*(len(r['levels'])-1):
                errors.append(f'{asset["id"]}: repeat value must cover full capacity')
        errors.extend(validate_stat_profiles(valid_packs, ids))
        errors.extend(validate_preview_profiles(valid_packs, ids))
        errors.extend(check_slots(valid_packs))
        if index and index.get('entry_asset') and index['entry_asset'] not in ids:errors.append('Unknown collection entry_asset: ' + index['entry_asset'])
        seen, active = set(), set()
        def walk(aid):
            if aid in active:errors.append('Reference cycle: ' + aid);return
            if aid in seen:return
            asset = ids.get(aid)
            if asset is None:errors.append('Unknown referenced asset ' + aid);return
            active.add(aid)
            refs = [x['asset'] for x in asset.get('frames',[])] + [x['asset'] for x in asset.get('layers',[]) if 'asset' in x] + list((asset.get('states') or {}).values()) + [choice for slot in asset.get('slots',{}).values() for choice in slot.get('options',[])]
            for ref in refs: walk(ref)
            active.remove(aid); seen.add(aid)
        for aid in ids:walk(aid)
    return errors

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip_path',type=Path)
    args = parser.parse_args(); errs=check(args.zip_path)
    for e in errs:print('ERROR:',e,file=sys.stderr)
    print('PASS: Visual Atlas ZIP valid' if not errs else f'FAIL: {len(errs)} errors')
    sys.exit(bool(errs))
