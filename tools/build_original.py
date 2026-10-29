#!/usr/bin/env python3
"""Self-contained, independent geometric SVG artwork. No third-party glyphs or paths."""
from __future__ import annotations
from pathlib import Path
import hashlib, json, re, math, sys
from xml.sax.saxutils import escape
from io import BytesIO
from PIL import Image, ImageFilter, ImageChops, ImageDraw
import cairosvg

ROOT = Path(__file__).resolve().parents[1]
W,H,COLS,ROWS,CELL=2304,768,24,8,96
FG='#f5f5f5'; MID='#bcbcbc'; LT='#d8d8d8'

def R(x,y,w,h,r=0,f=FG):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{f}"/>'
def C(x,y,r,f=FG): return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{f}"/>'
def E(x,y,rx,ry,f=FG):return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{f}"/>'
def L(x1,y1,x2,y2,w=2.3,f=FG):return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{f}" stroke-width="{w}" stroke-linecap="round"/>'
def P(d,f=FG):return f'<path d="{d}" fill="{f}"/>'
def S(d,w=2.3,f=FG):return f'<path d="{d}" fill="none" stroke="{f}" stroke-linecap="round" stroke-linejoin="round" stroke-width="{w}"/>'
def POL(points,f=FG):return '<polygon points="'+points+'" fill="'+f+'"/>'
def G(s,transform):return f'<g transform="{transform}">{s}</g>'
def dots(points,r=1.4):return ''.join(C(x,y,r) for x,y in points)

def symbol(name):
    # All drawings below are authored from geometric primitives, not imported or traced art.
    a=[]; add=a.append
    if name=='node': add(R(5,5,22,22,5));add(C(16,16,6,MID))
    elif name=='port': add(R(3,11,11,10,2));add(C(24,16,5));add(L(14,16,19,16,3))
    elif name=='connection': add(C(6,8,3));add(C(26,24,3));add(S('M9 8 C24 8 8 24 23 24',3.4))
    elif name=='branch': add(L(7,3,7,27,3));add(S('M7 13 Q22 13 22 25',3));add(C(22,25,3))
    elif name=='function': add(S('M9 7 Q6 7 8 11 L14 16 8 21 Q6 25 9 25',3));add(L(18,9,25,9,2));add(L(21,6,21,12,2))
    elif name=='variable': add(R(4,6,24,20,4));add(C(10,16,2,MID));add(L(16,16,24,16,3))
    elif name=='integer': add(R(5,6,5,20,1));add(R(13,9,5,17,1,MID));add(R(21,5,5,21,1))
    elif name=='float': add(R(4,7,7,18,1));add(C(15,24,2));add(R(20,7,7,18,1,MID))
    elif name=='string': add(C(9,13,4));add(C(22,13,4));add(S('M11 13 Q11 24 5 25 M24 13 Q24 24 18 25',3))
    elif name=='array': add(R(3,7,7,18,2));add(R(12,7,8,18,2,MID));add(R(22,7,7,18,2))
    elif name=='dictionary': add(R(4,4,23,24,3));add(R(8,9,5,5,1,MID));add(L(17,11,24,11,3,MID));add(L(9,20,22,20,3,MID))
    elif name=='bug':add(E(16,18,8,10));add(C(16,9,5,MID));add(L(8,14,3,11,2));add(L(24,14,29,11,2));add(L(8,20,2,20,2));add(L(24,20,30,20,2));add(L(8,25,3,29,2));add(L(24,25,29,29,2));add(L(14,5,10,2,2));add(L(18,5,22,2,2))
    elif name=='class': add(R(4,6,24,20,3));add(R(8,10,16,3,1,MID));add(R(8,17,10,3,1,MID))
    elif name=='file':add(P('M6 3 H20 L26 10 V29 H6 Z'));add(P('M19 4 V11 H26',MID));add(L(10,17,22,17,2,MID));add(L(10,22,18,22,2,MID))
    elif name=='folder':add(P('M3 9 H13 L16 12 H29 V26 Q29 28 27 28 H5 Q3 28 3 26 Z'));add(R(4,7,10,4,1,MID))
    elif name=='terminal':add(R(3,5,26,22,4));add(S('M8 11 L14 16 L8 21',3,MID));add(L(17,22,24,22,2,MID))
    elif name=='database':add(E(16,7,12,5));add(R(4,8,24,18,0,MID));add(E(16,26,12,5));add(E(16,9,12,4,MID));add(S('M4 16 Q16 24 28 16',2,FG))
    elif name=='cloud':add(C(11,18,7));add(C(18,12,9));add(C(26,20,5));add(R(7,19,23,8,3))
    elif name=='cpu':add(R(7,7,18,18,3));add(R(12,12,8,8,1,MID));[add(L(i,3,i,7,2)) for i in (10,16,22)];[add(L(i,25,i,29,2)) for i in (10,16,22)];[add(L(3,i,7,i,2)) for i in (10,16,22)];[add(L(25,i,29,i,2)) for i in (10,16,22)]
    elif name=='gpu':add(R(3,6,26,20,2));add(C(12,16,7,MID));add(C(12,16,3,FG));add(R(22,10,3,4,1,MID));add(R(22,17,3,4,1,MID))
    elif name=='memory':add(R(4,10,24,13,2));[add(R(i,14,3,5,0,MID)) for i in (8,14,20)];[add(L(i,7,i,10,2)) for i in (8,13,19,24)];[add(L(i,23,i,26,2)) for i in (8,13,19,24)]
    elif name=='monitor':add(R(3,4,26,19,2));add(R(6,7,20,13,0,MID));add(L(16,23,16,28,3));add(L(10,29,22,29,3))
    elif name=='laptop':add(R(6,4,20,20,2));add(R(9,7,14,14,1,MID));add(P('M2 25 H30 L28 29 H4 Z'))
    elif name=='phone':add(R(9,2,14,28,3));add(R(11,6,10,18,1,MID));add(C(16,27,1.5,MID))
    elif name=='server':add(R(4,4,24,7,2));add(R(4,13,24,7,2));add(R(4,22,24,7,2));[add(C(9,i,1.4,MID)) for i in (8,17,26)]
    elif name=='router':add(R(4,16,24,11,3));add(L(9,16,6,6,2));add(L(23,16,26,6,2));add(C(10,22,1.5,MID));add(C(16,22,1.5,MID))
    elif name=='wifi':add(S('M3 12 Q16 0 29 12',3));add(S('M8 18 Q16 10 24 18',3));add(S('M12 24 Q16 20 20 24',3));add(C(16,28,2))
    elif name=='shield':add(P('M16 2 L28 7 V16 Q27 25 16 30 Q5 25 4 16 V7 Z'));add(P('M16 8 L23 11 V16 Q23 21 16 25 Q9 21 9 16 V11 Z',MID))
    elif name=='key':add(C(10,10,7));add(C(10,10,3,MID));add(L(15,15,28,28,4));add(L(22,22,26,18,3))
    elif name=='lock':add(R(6,14,20,15,3));add(S('M10 15 V10 A6 6 0 0 1 22 10 V15',3.5));add(C(16,21,2,MID))
    elif name=='gear':add(C(16,16,11));add(C(16,16,5,MID));[add(R(14,1,4,5,1)) if i==0 else None for i in (0,)];add(R(14,26,4,5,1));add(R(1,14,5,4,1));add(R(26,14,5,4,1))
    elif name=='wrench':add(S('M9 7 Q11 2 17 4 L14 9 L19 14 L24 11 Q26 17 21 20 Q17 23 13 19 L5 28 L3 25 L12 16 Q8 13 9 7',3.7))
    elif name=='hammer':add(R(6,4,19,7,2));add(P('M14 11 H18 L23 28 H17 Z'))
    elif name=='battery':add(R(3,8,25,18,3));add(R(28,14,3,7,1));add(P('M16 10 L9 19 H16 L14 25 L24 15 H17 Z',MID))
    elif name=='lightning':add(P('M19 2 L7 18 H15 L12 30 L26 12 H18 Z'))
    elif name=='flask':add(S('M12 3 H20 M14 3 V14 L5 27 Q4 29 8 29 H24 Q28 29 27 27 L18 14 V3',3.5));add(P('M10 23 H22 L24 27 H8 Z',MID))
    elif name=='atom':add(E(16,16,13,5));add(G(E(16,16,13,5),'rotate(60 16 16)'));add(G(E(16,16,13,5),'rotate(120 16 16)'));add(C(16,16,3,MID))
    elif name=='microscope':add(S('M17 4 L24 9 L20 14 L13 9 Z',3.5));add(S('M19 14 Q26 23 16 26',3));add(L(5,28,28,28,3));add(L(10,21,10,26,3))
    elif name=='telescope':add(P('M4 10 L25 4 L28 11 L7 18 Z'));add(L(16,17,16,26,3));add(L(11,29,21,29,3))
    elif name=='planet':add(C(16,16,9));add(G(E(16,16,16,5,MID),'rotate(-22 16 16)'));add(C(16,16,9,FG));add(S('M2 19 Q16 30 30 13',2.2,MID))
    elif name=='rocket':add(P('M16 2 Q27 9 23 21 L16 28 L9 21 Q5 9 16 2 Z'));add(C(16,13,4,MID));add(P('M12 24 L8 30 L7 24 Z',MID));add(P('M20 24 L25 30 L25 24 Z',MID))
    elif name=='robot':add(R(5,9,22,18,5));add(C(11,18,2,MID));add(C(21,18,2,MID));add(R(12,24,8,2,1,MID));add(L(16,4,16,9,3));add(C(16,3,2))
    elif name=='fish':add(E(14,16,10,6));add(P('M23 16 L30 9 V23 Z'));add(C(10,14,2,MID))
    elif name=='bird':add(P('M4 23 Q9 3 23 13 L29 10 L26 17 Q24 28 4 23 Z'));add(C(21,14,1.6,MID));add(P('M4 23 L2 14 L12 22 Z',MID))
    elif name=='paw':add(E(16,23,9,6));[add(C(x,y,r)) for x,y,r in [(6,12,3),(13,7,3),(21,7,3),(28,12,3)]]
    elif name=='leaf':add(P('M4 27 Q4 4 28 4 Q28 28 4 27 Z'));add(S('M6 26 L24 8',2.8,MID));add(L(15,17,10,10,2,MID))
    elif name=='tree':add(P('M16 2 L5 18 H10 L3 24 H29 L22 18 H27 Z'));add(R(14,23,4,8,1,MID))
    elif name=='flower':add(C(16,9,5));add(C(9,16,5));add(C(23,16,5));add(C(16,23,5));add(C(16,16,5,MID))
    elif name=='mountain':add(P('M2 27 L12 6 L21 21 L25 14 L31 27 Z'));add(P('M9 12 L12 6 L16 13 L12 11 Z',MID))
    elif name=='compass':add(C(16,16,13));add(P('M19 13 L25 7 L22 17 L13 19 Z',MID));add(P('M13 19 L7 25 L10 15 L19 13 Z'))
    elif name=='flag':add(L(7,3,7,30,3));add(P('M9 4 Q15 0 23 6 V18 Q16 13 9 18 Z'))
    elif name=='globe':add(C(16,16,13));add(E(16,16,6,13,MID));add(S('M3 16 H29',2.2));add(S('M6 9 Q16 15 26 9 M6 23 Q16 17 26 23',1.9))
    elif name=='house':add(P('M2 14 L16 2 L30 14 L26 18 V29 H6 V18 Z'));add(R(13,19,6,10,1,MID))
    elif name=='family':add(C(11,8,4));add(C(23,8,4));add(C(17,18,3,MID));add(P('M3 27 Q3 16 11 16 Q16 16 16 23 Q17 14 23 16 Q30 16 30 27 Z'));add(C(17,19,3,MID))
    elif name=='bus':add(R(4,6,24,20,4));add(R(7,9,18,9,1,MID));add(C(10,27,2));add(C(23,27,2))
    elif name=='bicycle':add(C(7,23,6));add(C(25,23,6));add(S('M7 23 L14 12 L20 23 H7 L14 12 L18 10',3));add(L(18,10,24,12,2))
    elif name=='camera':add(R(3,8,26,19,3));add(P('M9 8 L11 4 H19 L21 8 Z'));add(C(16,18,7,MID));add(C(16,18,3));add(C(25,12,2,MID))
    elif name=='clapper':add(R(5,13,23,16,2));add(P('M3 7 L26 3 L28 10 L5 14 Z',MID));[add(L(i,8,i+4,12,2)) for i in (7,15,23)]
    elif name=='music':add(S('M13 25 V7 L26 4 V21',4));add(E(8,26,5,3));add(E(21,22,5,3))
    elif name=='brush':add(P('M8 24 L20 3 L27 7 L14 27 Z'));add(E(7,27,5,3,MID))
    elif name=='ball':add(C(16,16,13));add(S('M7 7 Q17 13 25 25 M25 7 Q16 13 7 25',2.6,MID));add(C(16,16,4,MID))
    elif name=='chess':add(C(16,5,4));add(P('M11 10 H21 L19 18 L24 26 H8 L13 18 Z'));add(R(6,27,20,3,1,MID))
    elif name=='dice':add(R(4,4,24,24,4));add(dots([(10,10),(22,10),(16,16),(10,22),(22,22)],2))
    elif name=='bread':add(P('M5 15 Q1 6 10 6 Q16 1 22 6 Q31 5 27 15 V27 H5 Z'));add(R(9,16,14,7,2,MID))
    else:raise ValueError(name)
    return ''.join(a)

DOMAINS={
 'programming':['node','port','connection','branch','function','variable','integer','float','string','array','dictionary','class','bug'],
 'files':['file','folder','terminal','database','cloud'],
 'hardware':['cpu','gpu','memory','monitor','laptop','phone','server','router','wifi'],
 'security':['shield','key','lock'],
 'tools':['gear','wrench','hammer','battery','lightning'],
 'science':['flask','atom','microscope','telescope','planet','rocket','robot'],
 'nature':['fish','bird','paw','leaf','tree','flower','mountain'],
 'places':['compass','flag','globe','house','family'],
 'transport':['bus','bicycle'],
 'media':['camera','clapper','music','brush'],
 'games':['ball','chess','dice'],
 'food':['bread'],
}
NAMES=[(domain,name) for domain,names in DOMAINS.items() for name in names]
assert len(NAMES)==64,len(NAMES)
VARIANTS=['symbol','badge','tile']

def svg_doc(elements):return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'+elements+'</svg>'

def build():
    out=ROOT/'sheets/original-00';out.mkdir(parents=True,exist_ok=True)
    icons=[]; svg_parts=[]
    for idx,(domain,name) in enumerate(NAMES):
      for vi,variant in enumerate(VARIANTS):
        i=idx*3+vi; col=i%COLS;row=i//COLS
        src=symbol(name)
        if variant=='badge':
            src=C(16,16,15,LT)+G(src,'translate(5 5) scale(.6875)')
        elif variant=='tile':
            src=R(1,1,30,30,6,LT)+G(src,'translate(5 5) scale(.6875)')
        group=G(src,f'translate({col*CELL+16} {row*CELL+16}) scale(2)')
        svg_parts.append(group)
        ident=f'icons.original.{domain}.{name}.{variant}'
        search=[name,domain,variant,*re.split('[-_]+',name)]
        if name=='fish':search+=['ocean','sea','marine','animal']
        if name=='file':search+=['document','attachment']
        if name=='camera':search+=['photo','photograph','picture capture']
        if name=='clapper':search+=['movie','film','video','production']
        if name=='bug':search+=['debug','defect']
        if name=='family':search+=['parents','child','household']
        if name=='brush':search+=['painting','art','design']
        if name=='ball':search+=['sport','football','soccer']
        if name=='planet':search+=['astronomy','space']
        if name=='array':search+=['list','sequence']
        if name=='folder':search+=['directory']
        if name=='wifi':search+=['wireless','network']
        if name=='paw':search+=['pet','animal','footprint']
        if name=='integer':search+=['int','i32','i64','number']
        if name=='float':search+=['f32','f64','decimal','real number']
        icons.append({'id':ident,'concept_id':f'icons.original.{domain}.{name}', 'name':name.replace('-',' ').title(), 'domain':domain,'variant':variant,
         'cell':{'x':col,'y':row},'rect_px':{'x':col*CELL,'y':row*CELL,'w':CELL,'h':CELL},
         'uv':{'u0':col/COLS,'v0':row/ROWS,'u1':(col+1)/COLS,'v1':(row+1)/ROWS},
         'tags':sorted(set(search)), 'sheet':'sheets/original-00/atlas.png', 'source':{'kind':'independent-geometric-design','artist':'Superior MI Labs / generated from the accompanying geometric design source','third_party_glyph':False,'review':'design-review'},
         'license':'Apache-2.0','quality':'candidate-human-review', 'width_px':CELL,'height_px':CELL})
    svg=svg_doc(''.join(svg_parts))
    (out/'foreground.svg').write_text(svg,encoding='utf-8')
    image=Image.open(BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert('RGBA')
    # The dilation produces a solid pure-black 3 px outline external to the grayscale geometry.
    mask=image.getchannel('A')
    outline_alpha=ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(7)),mask)
    outline=Image.new('RGBA',(W,H),(0,0,0,0));outline.putalpha(outline_alpha)
    foreground=Image.new('RGBA',(W,H),(255,255,255,0));foreground.putalpha(mask)
    final=Image.alpha_composite(outline,image)
    final.save(out/'atlas.png',optimize=True)
    foreground.save(out/'foreground-mask.png',optimize=True)
    outline.save(out/'black-outline.png',optimize=True)
    # A visual vector master: source elements are editable; black edge via SVG filter.
    filt='<defs><filter id="outer" x="-15%" y="-15%" width="130%" height="130%"><feMorphology in="SourceAlpha" operator="dilate" radius="1.5" result="expanded"/><feComposite in="expanded" in2="SourceAlpha" operator="out" result="edge"/><feFlood flood-color="#000000" result="black"/><feComposite in="black" in2="edge" operator="in"/></filter></defs>'
    (out/'atlas.svg').write_text(svg_doc(filt+f'<g filter="url(#outer)">'+''.join(svg_parts)+'</g>'+''.join(svg_parts)),encoding='utf-8')
    # No opaque background in the production PNGs.
    index={i['id']:i for i in icons}
    manifest={
      'schema':'smi-icon-atlas/1','pack':'superior-mi-icon-atlas-original','version':'0.1.0','status':'design-review',
      'source_of_truth':'manifest.json', 'license':'Apache-2.0',
      'sheet':{'id':'icons.original.atlas-00','path':'sheets/original-00/atlas.png','foreground_mask':'sheets/original-00/foreground-mask.png','black_outline':'sheets/original-00/black-outline.png','source_svg':'sheets/original-00/foreground.svg','columns':COLS,'rows':ROWS,'cell_px':CELL,'width_px':W,'height_px':H,'alpha':'RGBA','origin':'top-left'},
      'artwork_policy':{'original_only':True,'excluded_from_default':['third-party-font','third-party-icon','brand-trademark','unknown-provenance'],'origin_method':'independent geometric construction','automatic_public_clearance':False},
      'icons':icons,
    }
    for e in icons:
        cr=final.crop((e['rect_px']['x'],e['rect_px']['y'],e['rect_px']['x']+CELL,e['rect_px']['y']+CELL))
        e['crop_rgba_sha256']=hashlib.sha256(cr.tobytes()).hexdigest()
    manifest['sheet']['sha256']=hashlib.sha256((out/'atlas.png').read_bytes()).hexdigest()
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    # Checkerboard preview, separate from the transparent actual sheet.
    cb=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(cb)
    for x in range(0,W,16):
      for y in range(0,H,16):
       d.rectangle([x,y,x+15,y+15],fill=('#343b46' if (x//16+y//16)%2 else '#46505b'))
    cb.paste(final,(0,0),final)
    cb.resize((1728,576)).save(out/'inspection-preview.png')
    print(f'built {len(icons)} icons, {len(NAMES)} independent concepts')

if __name__=='__main__':build()
