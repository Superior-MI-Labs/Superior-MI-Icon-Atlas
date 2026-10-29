#!/usr/bin/env python3
"""Deterministic authoring of ORIGINAL geometric starter art; not required at runtime.
The resulting authored packs live under examples/ and are packed by build_site.py.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'examples'

def emit(name,pack,image):
    dest=OUT/name
    (dest/'textures').mkdir(parents=True,exist_ok=True)
    (dest/'manifest.json').write_text(json.dumps(pack,indent=2)+'\n')
    image.save(dest/'textures'/'atlas.png')
    (dest/'README.md').write_text(f'# {name} — geometry-only starter template\n\nOriginal CC0 geometric test artwork. Replace the artwork before commercial branding.\nEdit manifest.json and textures/atlas.png, then run the ZIP QA. This source directory is zipped by tools/build_site.py.\n')

def base(name,w,h):return {'schema':'smi-visual-pack/1','pack_id':'smi.examples.'+name,'version':'1.0.0','description':'Original geometric tutorial art for Visual Atlas. Not finished production artwork.','license':'CC0-1.0','textures':{'atlas':{'path':'textures/atlas.png','width_px':w,'height_px':h,'alpha':'straight'}},'assets':[]}

def region(id,x,y,w,h,name=None,tags=None):return dict(id=id,kind='region',texture='atlas',rect_px=[x,y,w,h],**({'name':name} if name else {}),**({'tags':tags} if tags else {}))

# Static icon. White on transparent, 96px safe border.
a=base('static-icon',96,96);a['assets']=[region('smi.example.icon.star',0,0,96,96,'Five-point star',['star','symbol','icon','white','monoline'])]
im=Image.new('RGBA',(96,96));d=ImageDraw.Draw(im);d.line([(48,13),(59,37),(84,39),(64,58),(70,83),(48,70),(26,83),(32,58),(12,39),(37,37),(48,13)],fill='white',width=5,joint='curve');emit('icons',a,im)

# Animation: three 96px cells, real exact geometry. White monoline pulse.
a=base('animated-icon',288,96);im=Image.new('RGBA',(288,96));d=ImageDraw.Draw(im)
for i,r in enumerate((19,25,33)):
    cx=48+96*i
    d.ellipse((cx-r,48-r,cx+r,48+r),outline=(255,255,255,255),width=5)
    d.line((cx-10,48,cx+10,48),fill='#FFFFFF',width=5)
    d.line((cx,38,cx,58),fill='#FFFFFF',width=5)
    a['assets'].append(region('smi.example.pulse.frame'+str(i+1),96*i,0,96,96))
a['assets'] += [{'id':'smi.example.pulse','kind':'sequence','name':'Looping pulse','default_fps':6,'playback':'loop','tags':['animation','icon','glow','pulse'], 'frames':[{'asset':'smi.example.pulse.frame'+str(i+1)} for i in range(3)]}]
emit('animated-icons',a,im)

# Character/object with two named sequences. A simple shape demonstrator, not character art.
a=base('character',384,192);im=Image.new('RGBA',(384,192));d=ImageDraw.Draw(im)
for row in range(2):
  for i in range(4):
    ox=i*96;oy=row*96;shift=(-6,0,6,0)[i] if row else 0
    # chassis, visor, legs, antenna; no artifact crosses cell boundary
    d.rounded_rectangle((ox+28+shift,oy+28,ox+68+shift,oy+64),radius=7,fill='#A9D7FA',outline='white',width=3)
    d.rounded_rectangle((ox+35+shift,oy+36,ox+61+shift,oy+45),radius=3,fill='#1C446B')
    d.line((ox+39+shift,oy+65,ox+34+shift,oy+78+(2 if i%2 else 0)),fill='white',width=5)
    d.line((ox+56+shift,oy+65,ox+62+shift,oy+78-(2 if i%2 else 0)),fill='white',width=5)
    d.line((ox+48+shift,oy+28,ox+48+shift,oy+17),fill='white',width=3)
    d.ellipse((ox+44+shift,oy+13,ox+52+shift,oy+21),fill='#88E6FF')
    a['assets'].append(region(f'smi.example.robot.{"idle" if row==0 else "walk"}.frame{i+1}',ox,oy,96,96))
for state in ('idle','walk'):
  a['assets'].append({'id':'smi.example.robot.'+state,'kind':'sequence','name':state.title()+' animation','default_fps':4 if state=='idle' else 8,'playback':'loop','tags':['robot','character','sprite','animation',state], 'frames':[{'asset':f'smi.example.robot.{state}.frame{i+1}'} for i in range(4)]})
a['assets'].append({'id':'smi.example.robot.states','kind':'state_set','name':'Robot animation states','default_state':'idle','states':{'idle':'smi.example.robot.idle','walk':'smi.example.robot.walk'},'tags':['robot','stateful','idle','walk']})
emit('character-animations',a,im)

# Numeric interactive GUI, with manifests for input and event/output contracts.
a=base('hud-meter',512,128);im=Image.new('RGBA',(512,128));d=ImageDraw.Draw(im)
d.rounded_rectangle((4,4,324,52),radius=12,fill='#0E2134',outline='#C0D5E8',width=3)
d.rounded_rectangle((12,60,308,84),radius=8,fill='#21BA8A',outline='#B8FFE8',width=2)
d.rounded_rectangle((337,4,380,52),radius=10,fill='#3E6F98',outline='white',width=3)
a['assets'] += [region('smi.example.hud.frame',0,0,328,56,'Meter frame'),region('smi.example.hud.fill',0,56,320,32,'Green fill'),region('smi.example.hud.thumb',332,0,52,56,'Slider thumb')]
a['assets'].append({'id':'smi.example.hud.meter','kind':'composition','name':'Interactive energy meter','size_px':[328,56],'tags':['health','mana','gui','slider','meter','progress'],'inputs':{'value':{'type':'number','default':72,'min':0,'max':100}},'behavior':{'role':'slider','outputs':{'value':{'from_input':'value','unit':'percent'}},'on':{'set_value':[{'op':'set','input':'value','source':'event.value'},{'op':'emit','event':'value_changed'}]}},'layers':[{'id':'fill','asset':'smi.example.hud.fill','offset_px':[9,12],'clip':{'input':'value','axis':'x','origin':'start'}},{'id':'frame','asset':'smi.example.hud.frame'}]})
emit('interactive-hud',a,im)
print('Wrote four authored starter pack sources under',OUT)
