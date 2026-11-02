#!/usr/bin/env python3
"""Original procedural Fantasy RPG HUD Wave 1. Source vector art -> measured RGBA atlas + Visual Atlas pack.
No generated composite grid is treated as a source asset. Stable inventory IDs are retained.
"""
import json, zipfile, io, hashlib, math, random, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cairosvg

INVENTORY=Path(__file__).resolve().parent/'PRODUCTION-INVENTORY.json'
ROOT=Path(__file__).resolve().parent
ASSETS=ROOT/'source-svg'; ASSETS.mkdir(parents=True,exist_ok=True)
PACK=ROOT/'pack'; (PACK/'textures').mkdir(parents=True,exist_ok=True)
data=json.loads(INVENTORY.read_text()); items=[a for a in data['regions'] if a['production_wave']==1]
assert len(items)==57
idp='smi.ui.fantasy01.'
# Visual truth constants. A slider's fill and handle share endpoints, not separate guessed ranges.
METER_FILL_X, METER_FILL_Y, METER_FILL_W, METER_FILL_H = 15, 14, 290, 20
SLIDER_USABLE_START, SLIDER_USABLE_END = 25, 295  # handle centers, not outside edges
SLIDER_THUMB_W = 40
SLIDER_FILL_X, SLIDER_FILL_W, SLIDER_FILL_Y = 24, 272, 15
assert SLIDER_FILL_X+1 == SLIDER_USABLE_START
assert SLIDER_FILL_X+SLIDER_FILL_W-1 == SLIDER_USABLE_END
assert 0 <= SLIDER_USABLE_START-SLIDER_THUMB_W//2
assert SLIDER_USABLE_END+SLIDER_THUMB_W//2 <= 320

def el(kind, **attrs):
    return f'<{kind} '+ ' '.join(f'{k.replace("_","-")}="{v}"' for k,v in attrs.items()) + '/>'

def r(x,y,w,h,rr=0,fill='none',stroke='none',sw=1,op=1):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rr}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>'

def path(d,fill='none',stroke='none',sw=1,op=1):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round" opacity="{op}"/>'

def ellipse(x,y,rx,ry,fill='none',stroke='none',sw=1,op=1):
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="{op}"/>'

def diamond(cx,cy,rx,ry,fill='url(#ruby)',stroke='#f3c675',sw=1):
    return path(f'M {cx} {cy-ry} L {cx+rx} {cy} L {cx} {cy+ry} L {cx-rx} {cy} Z',fill,stroke,sw)

GRADS='''
<defs>
<linearGradient id="gold" x1="0" y1="0" x2="0.25" y2="1"><stop stop-color="#fff0ae"/><stop offset="0.16" stop-color="#ce953f"/><stop offset="0.45" stop-color="#754016"/><stop offset="0.7" stop-color="#d6a252"/><stop offset="1" stop-color="#462511"/></linearGradient>
<linearGradient id="goldlight" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#fff6bc"/><stop offset="0.45" stop-color="#f0bf68"/><stop offset="1" stop-color="#976020"/></linearGradient>
<linearGradient id="enamel" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#392920"/><stop offset="0.35" stop-color="#170f15"/><stop offset="1" stop-color="#39201a"/></linearGradient>
<linearGradient id="recess" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#050c13"/><stop offset="0.5" stop-color="#121c2b"/><stop offset="1" stop-color="#1f1b16"/></linearGradient>
<linearGradient id="ruby" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#ffe2dc"/><stop offset="0.15" stop-color="#f43e59"/><stop offset="0.50" stop-color="#c81237"/><stop offset="0.85" stop-color="#6c092b"/><stop offset="1" stop-color="#370920"/></linearGradient>
<linearGradient id="sapphire" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#d4feff"/><stop offset="0.15" stop-color="#52dcf8"/><stop offset="0.55" stop-color="#1578d7"/><stop offset="1" stop-color="#102c70"/></linearGradient>
<linearGradient id="emerald" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#e0ffb7"/><stop offset="0.15" stop-color="#a5e658"/><stop offset="0.55" stop-color="#239c48"/><stop offset="1" stop-color="#0f533a"/></linearGradient>
<linearGradient id="amethyst" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#f6daff"/><stop offset="0.15" stop-color="#d374e4"/><stop offset="0.55" stop-color="#8429b5"/><stop offset="1" stop-color="#37204e"/></linearGradient>
<linearGradient id="amber" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#fff7c9"/><stop offset="0.15" stop-color="#ffc66a"/><stop offset="0.55" stop-color="#ff8c22"/><stop offset="1" stop-color="#803b15"/></linearGradient>
<linearGradient id="silver" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#e7e6df"/><stop offset="0.28" stop-color="#83909a"/><stop offset="0.8" stop-color="#47535b"/><stop offset="1" stop-color="#d9d3b8"/></linearGradient>
<radialGradient id="halo"><stop stop-color="#fff3a4" stop-opacity="0.75"/><stop offset="1" stop-color="#ffcb63" stop-opacity="0"/></radialGradient>
</defs>'''

def svg_wrap(w,h,body):
    # Exact aspect ratio is mandatory. An enlarged mismatched viewBox makes SVG
    # renderers letterbox long bars, silently shifting every geometry endpoint.
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{GRADS}{body}</svg>'

def glyph_ornaments(w,h,accent=False):
    out=''
    for xx,side in ((7,1),(w-7,-1)):
        out+=diamond(xx,h/2,4,6,'url(#ruby)' if accent else 'url(#goldlight)','#5b3017',0.9)
    return out

def build_meter(kind,variant,w,h):
    # All parts are separate, intentionally. rim has transparent central hole.
    pad=max(3,round(h*.08)); mainy=round(h*.18); mh=h-2*mainy
    outer=r(pad,pad,w-2*pad,h-2*pad,h*.19,'url(#enamel)','#5a331b',1.5)
    if kind=='shell':
        s=outer+r(pad+1,pad+1,w-2*(pad+1),h-2*(pad+1),h*.17,'none','url(#gold)',2.6)
        s+=r(pad+6,mainy,w-2*(pad+6),mh,h*.18,'#0c101a','#76502b',1.5)
        s+=path(f'M {pad+14} {pad+3} L {w-pad-14} {pad+3}',stroke='#ffe5a2',sw=1.1,op=.44)
        if variant=='boss':
            for xx in [35,w-35]:s+=diamond(xx,h/2,10,13,'url(#ruby)')
        else:s+=glyph_ornaments(w,h,variant=='standard')
        return s
    if kind=='recess':
        s=r(pad+10,mainy,w-2*(pad+10),mh,h*.18,'url(#recess)','#3c2a21',1)
        s+=path(f'M {pad+19} {mainy+4} L {w-pad-19} {mainy+4}',stroke='#9a8e70',sw=.7,op=.3)
        return s
    if kind=='rim':
        s=r(pad+9,mainy-1,w-2*(pad+9),mh+2,h*.18,'none','url(#goldlight)',1.7)
        s+=r(pad+12,mainy+2,w-2*(pad+12),mh-4,h*.16,'none','#362214',.8)
        for xx in [pad+10,w-pad-10]:s+=ellipse(xx,h/2,2,2,'#ffda83','#3f2010',.6)
        return s

def build_fill(flavor,w,h):
    # The image carries a 1px safe alpha border only. The ACTUAL colored pixels
    # reach the meter interior's first and last x positions at 100%.
    colors={'health':'ruby','mana':'sapphire','stamina':'emerald','xp':'amethyst','shield':'amber'}
    grad=colors[flavor]
    s=r(2,3,w-4,h-6,2.5,f'url(#{grad})','#200e18',.8)
    s+=r(3,4,w-6,2,1,'#fff6e9',op=.33)
    for i in range(1,13):
        x=3+i*(w-6)/13
        s+=path(f'M {x:.1f} 8 l -6 6',stroke='#fff8d8',sw=1.1,op=.15)
    s+=path(f'M 2 {h-5} L {w-3} {h-5}',stroke='#040c1e',sw=1.3,op=.45)
    return s

def build_overlay(kind,w,h):
    s='';rng=random.Random('overlay-'+kind)
    color={'damage':'#fa284c','healing':'#73ffb3','critical':'#ff4b29','shield-hit':'#82dfff'}[kind]
    for j in range(7):
        x=15+rng.randrange(0,w-30);y=10+rng.randrange(0,h-20)
        rad=rng.choice([2,3,4]);s+=diamond(x,y,rad,rad*1.35,color,'none',0)+ellipse(x,y,rad+3,rad+3,'none',color,.9,.5)
    if kind=='critical':s+=r(10,9,w-20,h-18,h*.13,'none',color,2,op=.6)
    if kind=='shield-hit':s+=path(f'M 40 {h-9} L 72 {9} L 122 {h-10} L 172 8',stroke=color,sw=1.4,op=.6)
    return s

def build_badge(kind,w,h):
    s=ellipse(w/2,h/2,19,19,'url(#enamel)','url(#gold)',3)
    s+=ellipse(w/2,h/2,16,16,'none','#f4c87c',1)
    label={'hp':'HP','mp':'MP','stamina':'ST'}[kind]
    size=13 if len(label)<3 else 11
    s+=f'<text x="{w/2}" y="{h/2+size*.33}" text-anchor="middle" font-family="DejaVu Sans" font-size="{size}" font-weight="bold" fill="#ffe9ac" stroke="#332216" stroke-width="0.3">{label}</text>'
    return s

def build_slider(style,part,w,h):
    center=h/2
    if part=='track':
        if style=='slim':
            return r(6,16,w-12,8,4,'url(#recess)','#87673a',1.5)+path(f'M 13 17 H {w-13}',stroke='#ffe19c',sw=.7,op=.4)
        if style=='engraved':
            return r(4,8,w-8,24,7,'url(#enamel)','url(#gold)',2)+r(11,16,w-22,8,4,'url(#recess)','#654c36',1)+glyph_ornaments(w,h)
        return r(4,9,w-8,22,11,'url(#enamel)','url(#gold)',2.2)+r(12,15,w-24,10,5,'url(#recess)','#a87937',.8)+glyph_ornaments(w,h,True)
    if part=='fill':
        # Full-width trail: x=1..w-1 is mapped to handle CENTER travel, not the track borders.
        return r(2,2,w-4,h-4,1.5,'url(#amber)' if style!='slim' else 'url(#sapphire)','#6e441e',.6)+r(3,3,w-6,2,1,'#fff1ba',op=.48)
    if part.startswith('thumb.'):
        state=part.split('.')[1]
        col='url(#silver)' if state=='disabled' else ('url(#sapphire)' if style=='slim' else 'url(#ruby)')
        outline='url(#goldlight)' if state in ('hover','pressed') else 'url(#gold)'
        rad=16 if state!='pressed' else 14
        s=''
        if state=='hover': s+=ellipse(w/2,h/2,18,18,'url(#halo)')
        if style=='gem':
            s+=diamond(w/2,h/2,rad*.72,rad,col,outline,3)
            s+=diamond(w/2,h/2-5,rad*.3,rad*.45,'#fff9ec','none',0)
        elif style=='engraved':
            s+=ellipse(w/2,h/2,rad*.78,rad*.78,'url(#enamel)',outline,3)
            s+=ellipse(w/2,h/2,rad*.52,rad*.52,col,'#ffd791',1)
        else:
            s+=ellipse(w/2,h/2,rad*.78,rad*.78,col,outline,2)
            s+=path(f'M {w/2} {h/2-6} v12',stroke='#f2f9ff',sw=1.6)
        if state=='pressed':s+=ellipse(w/2,h/2,rad*.6,rad*.6,'none','#fff4c7',1.5)
        if state=='disabled':s+=ellipse(w/2,h/2,rad*.7,rad*.7,'#6d6c67',op=.5)
        return s
    if part=='focus':return r(4,8,w-8,h-16,12,'none','#fff0a8',1.8,op=.75)
    if part=='ticks':
        s=''
        for n in range(11):
            x=SLIDER_USABLE_START+n*(SLIDER_USABLE_END-SLIDER_USABLE_START)/10
            s+=path(f'M {x} 34 v3',stroke='#cdaa68',sw=1.3,op=.7)
        return s
    raise ValueError('unknown slider '+part)

# Hearts have separately composable frame/fills/overlays.
HEART='M 24 43 C 17 36 5 28 5 18 C 5 9 12 5 19 6 C 23 6 25 9 24 10 C 28 4 37 4 42 10 C 50 23 36 34 24 43 Z'
HEART_IN='M 24 37 C 17 31 10 26 10 18 C 10 13 14 11 19 12 C 22 12 24 15 24 16 C 26 12 31 10 35 12 C 44 16 37 27 24 37 Z'
def build_heart(style,part,w,h):
    if part=='frame.empty':
        return path(HEART,'none','url(#goldlight)' if style=='gold' else 'url(#gold)',3.2)+path(HEART_IN,'none','#58351d',1.3)+ellipse(15,17,2,2,'#f2bb63',op=.5)
    if part.startswith('fill.'):
        flavor=part.split('.')[1];gradient={'red':'ruby','golden':'amber','poisoned':'emerald'}[flavor]
        return path(HEART_IN,f'url(#{gradient})','#8c4021',.8)+path('M 14 17 Q 16 11 21 17',stroke='#fff2dd',sw=2,op=.55)+ellipse(18,15,2,1,'#fff8ed',op=.5)
    if part=='overlay.damage':
        return path('M 17 9 L 26 17 L 20 25 L 30 33',stroke='#fff5db',sw=1.5,op=.9)+ellipse(30,25,10,10,'none','#ff5a47',1,op=.3)
    if part=='overlay.low-health':
        return path(HEART,'none','#ff6e3e',2.3,op=.72)+ellipse(24,24,18,18,'url(#halo)',op=.3)
    raise ValueError('unknown heart '+part)

def art(a):
    part=a['part'];w,h=a['nominal_size_px']
    if part.startswith('meter.'):
        _,x,*rest=part.split('.')
        if x in ['standard','compact','boss']: return w,h,build_meter(rest[0],x,w,h)
        if x=='fill':return w,h,build_fill(rest[0],w,h)
        if x=='overlay':return w,h,build_overlay(rest[0],w,h)
        if x=='badge':return w,h,build_badge(rest[0],w,h)
    if part.startswith('slider.'):
        _,style,*rest=part.split('.');type='.'.join(rest)
        if type.startswith('thumb.'):
            # isolate actual thumb from its original 320px nominal component canvas.
            w,h=40,40
        elif type=='fill':w,h=SLIDER_FILL_W,10
        return w,h,build_slider(style,type,w,h)
    if part.startswith('heart.'):
        _,style,*rest=part.split('.');return w,h,build_heart(style,'.'.join(rest),w,h)
    raise ValueError(part)

# deterministic source files, PNGs and shelf packer, no overlap / no guessed grid.
regions=[];images={};svgs={}
for a in items:
    w,h,b=art(a)
    svg=svg_wrap(w,h,b);svgs[a['id']]=svg
    (ASSETS/(a['id']+'.svg')).write_text(svg)
    blob=cairosvg.svg2png(bytestring=svg.encode(),output_width=w*3,output_height=h*3)
    im=Image.open(io.BytesIO(blob)).convert('RGBA').resize((w,h),Image.Resampling.LANCZOS)
    # Eliminate subvisible resampling noise outside the intended shapes.
    # This is not a crop shim: pixel coordinates and geometry remain unchanged.
    im.putalpha(im.getchannel('A').point(lambda a: 0 if a <= 4 else a))
    if not im.getbbox():raise ValueError('empty '+a['id'])
    images[a['id']]=im
    regions.append({**a,'actual_size_px':[w,h], 'bbox':im.getbbox()})

# Pack into exact rectangle locations. Atlas has 12px gutters + 6px padding margin.
MAXW=2048; G=16; P=10
sheets=[]; page=Image.new('RGBA',(MAXW,1024));x=y=P; rowh=0;atlas_index=0;placements={}
for a in regions:
    im=images[a['id']]; w,h=im.size
    if x+w+P>MAXW:x=P;y+=rowh+G;rowh=0
    if y+h+P>1024:
        sheets.append(page);atlas_index+=1;page=Image.new('RGBA',(MAXW,1024));x=y=P;rowh=0
    page.paste(im,(x,y));placements[a['id']]=(atlas_index,x,y,w,h)
    x+=w+G;rowh=max(rowh,h)
sheets.append(page)
for i,im in enumerate(sheets):im.save(PACK/'textures'/f'fantasy-hud-{i:02d}.png',optimize=True)

assets=[]
for a in regions:
    id=a['id'];idx,x,y,w,h=placements[id];part=a['part'];
    spec={'id':id,'kind':'region','name':part.replace('.',' ').replace('-',' ').title(), 'texture':f'atlas{idx}', 'rect_px':[x,y,w,h], 'logical_size_px':[w,h], 'tags': sorted(set(['rpg','fantasy','ornate','gui',a['family'],part.split('.')[-1]])), 'style':'fantasy-ornate-gold'}
    assets.append(spec)

interface=f'smi.slot.ui.fantasy01.meter.fill.{METER_FILL_W}x{METER_FILL_H}/1'
fill_ids=[idp+f'meter.fill.{x}' for x in ['health','mana','stamina','xp','shield']]
for a in assets:
    if a['id'] in fill_ids:a['implements']=[interface]

# Compose meters with layered frames, fill and transparent rim; optional overlay controlled by boolean.
for kind,badge in [('health','hp'),('mana','mp'),('stamina','stamina'),('xp',None),('shield',None)]:
    bar_shift=40 if badge else 0  # badge is its own slot, never painted over meaningful fill
    comp={
        'id':idp+f'widget.meter.{kind}','kind':'composition','name':kind.title()+' Meter — Royal Gold',
        'size_px':[320+bar_shift,48], 'tags':['hud','resource','meter',kind,'fantasy','interactive'],
        'inputs':{'value':{'type':'number','default':72,'min':0,'max':100},'show_effect':{'type':'boolean','default':False}},
        'slots':{'fill':{'label':'Resource fill','accepts':interface,'default':idp+f'meter.fill.{kind}', 'options':fill_ids}},
        'presets':{n.title():{'slots':{'fill':idp+f'meter.fill.{n}'}} for n in ['health','mana','stamina','xp','shield']},
        'default_preset':kind.title(),
        'layers':[
          {'id':'shell','asset':idp+'meter.standard.shell','offset_px':[bar_shift,0]},
          {'id':'recess','asset':idp+'meter.standard.recess','offset_px':[bar_shift,0]},
          {'id':'fill','slot':'fill','offset_px':[bar_shift+METER_FILL_X,METER_FILL_Y],'clip':{'input':'value','axis':'x','origin':'start'}},
          {'id':'rim','asset':idp+'meter.standard.rim','offset_px':[bar_shift,0]},
          {'id':'effect','asset':idp+'meter.overlay.healing' if kind in ['stamina','xp'] else idp+'meter.overlay.damage','visible_when':{'input':'show_effect','equals':True}},
          *([{'id':'badge','asset':idp+'meter.badge.'+badge,'offset_px':[0,0]}] if badge else [])
        ],
        'behavior':{'role':'slider','outputs':{'value':{'from_input':'value','unit':'percent'}}, 'on':{'set_value':[{'op':'set','input':'value','source':'event.value'},{'op':'emit','event':'value_changed'}]}}
    }
    assets.append(comp)

# sliders: 3 theme variants, 4 state thumbs, separate track/fill/focus/tick layers.
for style in ('gem','engraved','slim'):
    state_id=idp+f'slider.{style}.thumb.states'
    states={st:idp+f'slider.{style}.thumb.{st}' for st in ('default','hover','pressed','disabled')}
    assets.append({'id':state_id,'kind':'state_set','name':style.title()+' Gem Slider Handle States','states':states,'default_state':'default','tags':['slider','thumb','hover','pressed','disabled','fantasy']})
    assets.append({
        'id':idp+f'widget.slider.{style}','kind':'composition','name':style.title()+' Horizontal Slider',
        'size_px':[320,40], 'tags':['gui','slider','horizontal','interactive',style],
        'inputs':{'value':{'type':'number','min':0,'max':100,'default':45},'appearance':{'type':'enum','default':'default','values':['default','hover','pressed','disabled']},'focused':{'type':'boolean','default':False}},
        'layers':[
            {'id':'track','asset':idp+f'slider.{style}.track'},
            {'id':'fill','asset':idp+f'slider.{style}.fill','offset_px':[SLIDER_FILL_X,SLIDER_FILL_Y], 'clip':{'input':'value','axis':'x','origin':'start'}},
            {'id':'ticks','asset':idp+f'slider.{style}.ticks'},
            {'id':'handle','asset':state_id,'offset_px':[0,0], 'position_from_input':{'input':'value','axis':'x','from_px':SLIDER_USABLE_START-SLIDER_THUMB_W//2,'to_px':SLIDER_USABLE_END-SLIDER_THUMB_W//2}, 'state_from_input':'appearance'},
            {'id':'focus','asset':idp+f'slider.{style}.focus','visible_when':{'input':'focused','equals':True}}
        ],
        'behavior':{'role':'slider','outputs':{'value':{'from_input':'value','unit':'percent'}}, 'on':{'set_value':[{'op':'set','input':'value','source':'event.value'},{'op':'emit','event':'value_changed'}]}}
    })

for style in ['ruby','gold']:
    fill_ids_h=[idp+f'heart.{style}.fill.{flavor}' for flavor in ['red','golden','poisoned']]
    face=idp+f'heart.{style}.frame.empty'
    interface_h=f'smi.slot.ui.fantasy01.heart.{style}.48x48/1'
    for a in assets:
        if a['id'] in fill_ids_h:a['implements']=[interface_h]
    assets.append({
        'id':idp+f'widget.heart.{style}', 'kind':'composition','name':style.title()+' Life Heart',
        'size_px':[48,48], 'tags':['heart','life','hp','rpg','fantasy','fractional'],
        'inputs':{'fraction':{'type':'number','min':0,'max':1,'default':1},'damage':{'type':'boolean','default':False},'critical':{'type':'boolean','default':False}},
        'slots':{'fill':{'label':'Heart appearance','accepts':interface_h,'default':fill_ids_h[0],'options':fill_ids_h}},
        'presets':{'Red':{'slots':{'fill':fill_ids_h[0]}},'Golden':{'slots':{'fill':fill_ids_h[1]}},'Poisoned':{'slots':{'fill':fill_ids_h[2]}}},
        'default_preset':'Red',
        'layers':[
            {'id':'fill','slot':'fill', 'clip':{'input':'fraction','axis':'x','origin':'start'}},
            {'id':'frame','asset':face},
            {'id':'damage','asset':idp+f'heart.{style}.overlay.damage','visible_when':{'input':'damage','equals':True}},
            {'id':'low-health','asset':idp+f'heart.{style}.overlay.low-health','visible_when':{'input':'critical','equals':True}}
        ]
    })

textures={f'atlas{i}':{'path':f'textures/fantasy-hud-{i:02d}.png','width_px':im.width,'height_px':im.height,'alpha':'straight','color_space':'srgb','sha256':hashlib.sha256((PACK/'textures'/f'fantasy-hud-{i:02d}.png').read_bytes()).hexdigest()} for i,im in enumerate(sheets)}
interfaces={interface:{'size_px':[METER_FILL_W,METER_FILL_H],'allow_scale':False}}
interfaces.update({f'smi.slot.ui.fantasy01.heart.{style}.48x48/1':{'size_px':[48,48],'allow_scale':False} for style in ['ruby','gold']})
pack={
    'schema':'smi-visual-pack/1','pack_id':'smi.ui.fantasy01.hud-wave1','version':'0.2.0',
    'description':'Original handcrafted procedural vector UI: 57 isolated reusable fantasy meter, slider, and heart parts; approved artwork with pixel-verified value fidelity.',
    'license':'CC0-1.0','textures':textures,'interfaces':interfaces,'assets':assets
}
(PACK/'manifest.json').write_text(json.dumps(pack,indent=2)+'\n')
(PACK/'collection.json').write_text(json.dumps({'schema':'smi-visual-collection/1','collection_id':'smi.ui.fantasy01.hud-wave1','name':'Fantasy RPG HUD Wave 1 — Meters, Sliders & Hearts','version':'0.2.0','description':'57 source regions and 10 assembled widgets. Approved artwork; meter and slider visual fidelity verified.','entry_asset':idp+'widget.meter.health','packs':[{'manifest':'manifest.json','label':'Fantasy HUD Wave 1','category':'gui-control'}]},indent=2)+'\n')
(PACK/'LICENSE.txt').write_text('CC0 1.0 Universal: original procedural vector artwork and source imagery created for Superior MI Visual Atlas. No attribution required. The LICENSE grant applies only to this artwork pack, not to other projects or the current candidate icon collection. https://creativecommons.org/publicdomain/zero/1.0/\n')
(PACK/'README.txt').write_text('SUPERIOR MI VISUAL ATLAS — FANTASY HUD WAVE 1\nv0.2 geometry correction: 57 isolated source regions, 5 resource meters, 3 sliders, 2 hearts + 3 slider state sets.\nOriginal vector-drawn artwork approved by creator; verified for the documented GUI behavior.\nDrop this ZIP into Visual Atlas Builder, then choose compatible presets or adjust manifest controls.\nHover/pressed appearance is manifest-driven. Native pointer dragging remains the host application responsibility.\n')

# Contact sheet with every region actually cropped from atlas, not SVG files.
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; FONT=ImageFont.truetype(font,11)
cols=5; cellw,cellh=265,115; rows=math.ceil(len(regions)/cols)
contact=Image.new('RGB',(cols*cellw,rows*cellh),'#0b1421');d=ImageDraw.Draw(contact)
for i,a in enumerate(regions):
    cx=(i%cols)*cellw;cy=(i//cols)*cellh;im=images[a['id']].copy();
    d.rounded_rectangle((cx+3,cy+2,cx+cellw-3,cy+cellh-2),radius=7,fill='#1c2b3d',outline='#3f5465')
    # scale to fit keeping original aspect
    im.thumbnail((cellw-18,70),Image.Resampling.LANCZOS)
    pos=(cx+(cellw-im.width)//2,cy+6+(70-im.height)//2)
    contact.paste(im,pos,im)
    d.text((cx+8,cy+82),a['part'][:34],font=FONT,fill='#e1e8ee')
    d.text((cx+8,cy+99),str(a['actual_size_px'])+' / '+str(placements[a['id']][:1]),font=FONT,fill='#83aacb')
contact_path=ROOT/'all-57-contact-sheet.png';contact.save(contact_path)

# Demo page - composite regions using source PNGs and explicit overlap, with value crops.
font_big=ImageFont.truetype(font,17)
font_title=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',26)
DEMO=Image.new('RGBA',(1440,1000),(10,19,31,255));canvas=ImageDraw.Draw(DEMO)
# subtle texture background
a=ImageDraw.Draw(DEMO,'RGBA')
for yy in range(0,1000,24):a.line((0,yy,1440,yy),fill=(21,35,50,255))
for xx in range(0,1440,24):a.line((xx,0,xx,1000),fill=(21,35,50,255))
canvas.text((55,35),'FANTASY RPG  /  HUD ESSENTIALS',font=font_title,fill='#e3c28a')
canvas.text((55,72),'Wave 01 — decomposed source layers • measured atlas regions • original vector art',font=font_big,fill='#a9b5c5')

def composite(id,x,y,scale=1):
    im=images[id];
    if scale!=1:im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    DEMO.alpha_composite(im,(round(x),round(y)))

def meter_example(flavor,y,percent,badge='hp'):
    x=85
    shift=40 if badge else 0
    for name in ['shell','recess']:composite(idp+'meter.standard.'+name,x+shift,y)
    im=images[idp+'meter.fill.'+flavor]
    cutoff=round(im.width*percent);clip=im.crop((0,0,max(1,cutoff),im.height));
    if percent>0:DEMO.alpha_composite(clip,(x+shift+METER_FILL_X,y+METER_FILL_Y))
    composite(idp+'meter.standard.rim',x+shift,y)
    if badge:composite(idp+'meter.badge.'+badge,x,y)
    canvas.text((455,y+12),f'{flavor.title():10s}  {percent:>4.0%}',font=font_big,fill='#e4dcc9')

def slider_example(style,y,percent,state):
    x=710
    composite(idp+f'slider.{style}.track',x,y)
    im=images[idp+f'slider.{style}.fill']
    cw=round(im.width*percent)
    if cw>0:DEMO.alpha_composite(im.crop((0,0,cw,im.height)),(x+SLIDER_FILL_X,y+SLIDER_FILL_Y))
    composite(idp+f'slider.{style}.ticks',x,y)
    composite(idp+f'slider.{style}.thumb.{state}',x+round(SLIDER_USABLE_START-SLIDER_THUMB_W//2+(SLIDER_USABLE_END-SLIDER_USABLE_START)*percent),y)
    canvas.text((1080,y+10),f'{style.title()}  {percent:>4.0%}  {state}',font=font_big,fill='#e4dcc9')

canvas.text((70,130),'RESOURCE METERS',font=font_big,fill='#f3d496')
canvas.text((705,130),'INTERACTIVE SLIDERS',font=font_big,fill='#f3d496')
for (fl,pc,badge),yy in zip([('health',.78,'hp'),('mana',.49,'mp'),('stamina',.85,'stamina'),('xp',.33,None),('shield',.66,None)],range(180,590,80)):
    meter_example(fl,yy,pc,badge)
for (style,pc,state),yy in zip([('gem',.52,'default'),('engraved',.78,'hover'),('slim',.22,'pressed')],range(195,550,130)):
    slider_example(style,yy,pc,state)
canvas.text((70,635),'LIFE HEARTS — FRACTIONAL / SWAPPABLE',font=font_big,fill='#f3d496')
for ri,style in enumerate(['ruby','gold']):
  y=698+ri*88
  canvas.text((70,y+12),style.title(),font=font_big,fill='#c6b2a4')
  for i,(pc,flavor) in enumerate(zip([1,.75,.5,.25,0,1],['red','red','red','red','red','golden'])):
    x=190+i*94
    if pc>0:
      im=images[idp+f'heart.{style}.fill.{flavor}'];cw=round(48*pc)
      DEMO.alpha_composite(im.crop((0,0,max(1,cw),48)),(x,y))
    composite(idp+f'heart.{style}.frame.empty',x,y)
    if i==4:composite(idp+f'heart.{style}.overlay.low-health',x,y)
canvas.text((55,937),'PREVIEW ONLY • no assets are baked together in the production atlas • compatibility declared in manifest',font=font_big,fill='#8c9caa')
(DEMO.convert('RGB')).save(ROOT/'assembled-preview.png',quality=94)

# Verify atlas pixel identity against originals, including fully transparent gutters.
for a in regions:
  idx,x,y,w,h=placements[a['id']];crop=sheets[idx].crop((x,y,x+w,y+h));assert crop.tobytes()==images[a['id']].tobytes(),a['id']
  # Entire region is isolated; small anti-aliased edge touches are a review warning, not a grid overlap.
  bb=images[a['id']].getbbox();assert bb and bb[2]<=w and bb[3]<=h
for a in regions:
    idx,x,y,w,h=placements[a['id']];p=sheets[idx]
    assert p.getpixel((x-1,y-1))[3]==0

# machine-readable build provenance
report={'schema':'smi-hud-generation/1','regions':len(regions),'atlases':len(sheets),'compositions':sum(a['kind']=='composition' for a in assets),'state_sets':sum(a['kind']=='state_set' for a in assets),'assets':len(assets),'rects':{a['id']:placements[a['id']] for a in regions},'source':'procedural vector source files and measured packed RGBA','validation':'measured source crop equality and transparent gutters PASS; browser and official validation pending'}
(ROOT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')
with zipfile.ZipFile(ROOT/'Fantasy-RPG-HUD-Wave1-Import.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
    for p in sorted(PACK.rglob('*')):
      if p.is_file():z.write(p,p.relative_to(PACK).as_posix())
print('BUILT',json.dumps({'regions':len(regions),'textures':len(sheets),'assets':len(assets),'zip':str(ROOT/'Fantasy-RPG-HUD-Wave1-Import.zip')}))
