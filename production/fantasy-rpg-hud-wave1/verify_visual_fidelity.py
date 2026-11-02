#!/usr/bin/env python3
"""Request-specific, deterministic acceptance gate for meter and slider visual fidelity.

Consumes final Chromium screenshots produced from the exact ZIP. This gate checks
pixel occupancy, proportional range, and shared slider geometry. It intentionally
avoids claiming aesthetic approval or native pointer-dragging support.
"""
from pathlib import Path
from PIL import Image
import numpy as np, json
root=Path(__file__).resolve().parent
qa=root/'browser-qa'
values=[0,1,5,10,25,50,75,90,99,100]
checks=[]

# Compare rendered meter images against the zero-state, not the value label.
p=qa/'fantasy-health-tenth-percent-range'
base=np.asarray(Image.open(p/'v0.png').convert('RGB')).astype(np.int16)
full=np.asarray(Image.open(p/'v100.png').convert('RGB')).astype(np.int16)
counts=[];endpoints=[]
for v in values:
    img=np.asarray(Image.open(p/f'v{v}.png').convert('RGB')).astype(np.int16)
    diff=np.max(np.abs(img-base),axis=2)>16
    yy,xx=np.where(diff)
    counts.append(int(len(xx)))
    endpoints.append(int(xx.max()) if len(xx) else None)
assert counts[0]==0 and counts[1]>0 and counts[2]>counts[1], ('Low values invisible',counts)
assert all(b>=a for a,b in zip(counts,counts[1:])), ('Fill is nonmonotonic',counts)
assert all(abs(counts[i]/counts[-1]-values[i]/100)<0.065 for i in range(2,len(values))),('Fill is disproportionate',values,counts)
assert counts[-1] >= 2000,('Full fill not visible',counts[-1])
checks.append({'gate':'meter 0..100 proportional rendered area','result':'PASS','values':values,'changed_pixels':counts,'rightmost_changed_x':endpoints})

# These endpoints MUST come from the same authoring geometry, not two arbitrary guesses.
from importlib.machinery import SourceFileLoader
# Importing generator would rewrite the atlas, so read the source's named constants safely.
import ast
source=ast.parse((root/'generate.py').read_text())
vars_={}
for stmt in source.body:
    if isinstance(stmt,ast.Assign) and len(stmt.targets)==1 and isinstance(stmt.targets[0],ast.Name) and isinstance(stmt.value,ast.Constant):
        vars_[stmt.targets[0].id]=stmt.value.value
    elif isinstance(stmt,ast.Assign) and isinstance(stmt.value,ast.Tuple) and all(isinstance(x,ast.Constant) for x in stmt.value.elts):
        for target in stmt.targets:
            if isinstance(target,ast.Tuple):
                for name,value in zip(target.elts,stmt.value.elts): vars_[name.id]=value.value
m=json.loads((root/'pack/manifest.json').read_text());a={x['id']:x for x in m['assets']}
for style in ['gem','engraved','slim']:
  comp=a['smi.ui.fantasy01.widget.slider.'+style]
  fill=next(x for x in comp['layers'] if x['id']=='fill')
  handle=next(x for x in comp['layers'] if x['id']=='handle')
  region=a[fill['asset']]
  thumb=a[comp['layers'][3]['asset'].replace('.states','.default')] if False else a['smi.ui.fantasy01.slider.'+style+'.thumb.default']
  px=handle['position_from_input']
  center_left=px['from_px']+thumb['rect_px'][2]/2
  center_right=px['to_px']+thumb['rect_px'][2]/2
  effective_fill_start=fill['offset_px'][0]+2
  effective_fill_end=fill['offset_px'][0]+region['rect_px'][2]-2
  assert center_left>=thumb['rect_px'][2]/2 and center_right<=comp['size_px'][0]-thumb['rect_px'][2]/2,(style,'thumb outside canvas')
  assert abs(effective_fill_start-center_left)<=2 and abs(effective_fill_end-center_right)<=2,(style,'trail endpoints disagree')
  assert center_left>0 and center_right<320
  # Ten real browser screenshots must exist, not just a theoretical mapping.
  assert all((qa/f'fantasy-{style}-slider-range'/f'v{v}.png').stat().st_size>100 for v in values)
  checks.append({'gate':style+' slider shared endpoints and bounded handle','result':'PASS','fill_span':[effective_fill_start,effective_fill_end],'thumb_center_span':[center_left,center_right],'browser_samples':len(values)})

# Badge must not overlap the color-active data range at any input value.
for name in ['health','mana','stamina']:
  comp=a['smi.ui.fantasy01.widget.meter.'+name]
  badge=next(x for x in comp['layers'] if x['id']=='badge')
  fill=next(x for x in comp['layers'] if x['id']=='fill')
  badge_w=a[badge['asset']]['rect_px'][2]
  assert badge['offset_px'][0]+badge_w <= fill['offset_px'][0]+2,('badge hides low value',name)
checks.append({'gate':'badge and meter data span are non-overlapping','result':'PASS'})
report={'schema':'smi-ui-value-fidelity/1','status':'PASS','checks':checks,'notes':'This is a pixel and source-geometry gate; artistic signoff and native pointer input remain separate.'}
(root/'VISUAL-FIDELITY-QA.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: rendered 10-value meter proportionality, all three sliders, badge and source-geometry gates')
for c in checks: print('  '+c['gate'])
