#!/usr/bin/env python3
"""Candidate validation, independent of output generation and art approval."""
from pathlib import Path
from PIL import Image
import hashlib,json
R=Path(__file__).resolve().parent

def validate():
    manifest=json.loads((R/'manifest.json').read_text())
    collection=json.loads((R/'collection.json').read_text())
    indexed={a['id']:a for a in manifest['assets']}
    assert manifest['schema']=='smi-visual-pack/1'
    assert collection['schema']=='smi-visual-collection/1'
    assert len(indexed)==len(manifest['assets'])==65
    assert collection['entry_asset'] in indexed
    pixels={}
    for key,entry in manifest['textures'].items():
        path=R/entry['path'];data=path.read_bytes()
        assert hashlib.sha256(data).hexdigest()==entry['sha256'],key
        im=Image.open(path)
        assert im.mode=='RGBA' and im.size==(entry['width_px'],entry['height_px']),key
        pixels[key]=im
    items=[]
    for a in indexed.values():
        if a['kind']=='region':
            im=pixels[a['texture']];x,y,w,h=a['rect_px']
            assert 0<=x<im.width and 0<=y<im.height and x+w<=im.width and y+h<=im.height,a['id']
            alpha=im.crop((x,y,x+w,y+h)).getchannel('A')
            bbox=alpha.getbbox()
            if a['id']=='smi.game.pixel01.fx.clear':assert bbox is None
            else:assert bbox is not None,a['id']
            if a['texture']!='effects':
                assert a['logical_size_px']==[128,128] and w==h==128
                margins=[bbox[0],bbox[1],128-bbox[2],128-bbox[3]]
                assert min(margins)>=6,(a['id'],margins)
                items.append(a)
        if a['kind']=='state_set':
            assert a['default_state'] in a['states']
            assert all(v in indexed for v in a['states'].values()),a['id']
        if a['kind']=='composition':
            assert len(a.get('layers',[]))>=1
            for l in a['layers']:
                if 'asset' in l:assert l['asset'] in indexed,(a['id'],l['asset'])
                if 'slot' in l:assert l['slot'] in a['slots']
            for slot in a.get('slots',{}).values():
                assert slot['default'] in slot['options']
                assert all(ref in indexed for ref in slot['options'])
    assert len(items)==48
    comp=indexed['smi.game.pixel01.widget.item']
    assert set(comp['slots']['icon']['options'])=={a['id'] for a in items}
    baseline=json.loads((R/'qa'/'candidate-pixel-baseline.json').read_text())
    assert len(baseline)==48
    for a in items:
        x,y,w,h=a['rect_px']
        actual=hashlib.sha256(pixels[a['texture']].crop((x,y,x+w,y+h)).tobytes()).hexdigest()
        assert baseline[a['id']]==actual,('Artwork changed since last review',a['id'])
    bad=dict(items[0]);bad['rect_px']=[128,0,128,128]
    def thumbhash(a):
        x,y,w,h=a['rect_px']
        return hashlib.sha256(pixels[a['texture']].crop((x,y,x+w,y+h)).tobytes()).hexdigest()
    assert thumbhash(bad)!=baseline[bad['id']],'Shifted rect escaped pixel baseline'
    altered=pixels[items[0]['texture']].copy();x,y,_,_=items[0]['rect_px'];altered.paste((0,0,0,0),(x+90,y,x+128,y+128))
    assert hashlib.sha256(altered.crop((x,y,x+128,y+128)).tobytes()).hexdigest()!=baseline[items[0]['id']],'Amputation escaped baseline'
    print('PASS: 48 real image regions, 13 overlay regions, 1 transparent-state composition, 2 state sets, 1 item composition; refs, hashes, gutters, and negative regressions')
    print('WARNING: Alpha margins and baselines are not semantic completeness; live Builder/creator review separately required')

if __name__=='__main__':validate()
