#!/usr/bin/env python3
"""Deterministic authoritative build: source raster + one authoring contract -> PNGs and manifest.

Never rebuild from the old decorative concept-board extraction. Every source tile
is bounded and inspected *before* packing; asset coordinates derive from cell index.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
from extract_wave3 import extract as dark_extract
from extract_expansion import extract as white_extract
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'textures'
SOURCE=[('icons','source-wave1-clean.png','dark'),('icons2','source-expansion.png','white'),('icons3','source-wave3.png','dark')]


def build():
 cfg=json.loads((ROOT/'authoring.json').read_text())
 (ROOT/'qa').mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
 assets=[];source_checks=[];texture_records={}
 for sheet,filename,mode in SOURCE:
  src=Image.open(ROOT/filename).convert('RGB')
  full=np.asarray(src)
  atlas=Image.new('RGBA',(512,512))
  records=[a for a in cfg['items'] if a['sheet']==sheet]
  assert len(records)==16,(sheet,len(records))
  for record in records:
   idx=record['index'];col,row=idx%4,idx//4
   if mode=='dark':tile,coverage=dark_extract(full,col,row)
   else:
    tile=white_extract(src,col,row)
    coverage={'source_cell':[round(src.width*col/4),round(src.height*row/4),round(src.width/4),round(src.height/4)],'review_required':'source originally on light checkerboard; review edge detail'}
   alpha=tile.getchannel('A'); bb=alpha.getbbox()
   assert bb is not None,record['id']
   x1,y1,x2,y2=bb
   assert min(x1,y1,128-x2,128-y2)>=6,(record['id'],bb)
   atlas.alpha_composite(tile,(col*128,row*128))
   a={k:v for k,v in record.items() if k not in ('index','sheet')}
   a.update({'kind':'region','texture':sheet,'rect_px':[col*128,row*128,128,128], 'logical_size_px':[128,128]})
   assets.append(a)
   source_checks.append({'id':a['id'],'sheet':sheet,'source_file':filename,'region':[col*128,row*128,128,128], 'silhouette_bbox':[x1,y1,x2,y2], 'margins':[x1,y1,128-x2,128-y2],**coverage})
  name={'icons':'icons-00.png','icons2':'icons-01.png','icons3':'icons-02.png'}[sheet]
  atlas.save(OUT/name,optimize=True,compress_level=9)
  by=(OUT/name).read_bytes()
  texture_records[sheet]={'path':'textures/'+name,'width_px':512,'height_px':512,'alpha':'straight','color_space':'srgb','sha256':hashlib.sha256(by).hexdigest()}
 # Shared overlays and appearance contracts are authored once, never repeated per item.
 fx=cfg['effects_components'];effect_path=OUT/'effects.png'
 assert effect_path.is_file(),'Missing authoritative effects.png'
 assert Image.open(effect_path).size==(896,256)
 texture_records['effects']={'path':'textures/effects.png','width_px':896,'height_px':256,'alpha':'straight','color_space':'srgb','sha256':hashlib.sha256(effect_path.read_bytes()).hexdigest()}
 assets.extend(fx)
 ids=[a['id'] for a in assets if a['kind']=='region' and a['texture']!='effects']
 assert len(ids)==48 and len(set(ids))==48
 comp=next(a for a in assets if a['id']=='smi.game.pixel01.widget.item')
 comp['slots']['icon']['options']=ids
 # Do not embed blanket approval claims; individually reported source/crop checks are evidence only.
 manifest={'schema':'smi-visual-pack/1','pack_id':'smi.game.pixel01','version':'0.3.0',
   'description':'48 HD fantasy pixel-art game icons and 17 reusable UI assets; original source sheets and manifest-based sprite extraction included.',
   'license':'CC0-1.0','textures':texture_records,
   'interfaces':cfg['interfaces'],'assets':assets}
 collection={'schema':'smi-visual-collection/1','collection_id':'smi.game.pixel01.wave123','name':'Pixel Fantasy — 48 Game Items & Interactive Effects','version':'0.3.0','description':'48 HD fantasy pixel-art item icons with 17 reusable state, rarity and interaction assets. Browse, search, download, and import into the Visual Atlas Builder.', 'entry_asset':comp['id'],'packs':[{'manifest':'manifest.json','label':'Fantasy Pixel Icons','category':'game-icons'}]}
 (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (ROOT/'collection.json').write_text(json.dumps(collection,indent=2)+'\n')
 (ROOT/'qa'/'source-coverage-all.json').write_text(json.dumps(source_checks,indent=2)+'\n')
 print('Built',len(ids),'item regions +',len(fx),'shared assets; 3 x 512px textures + effects; 65 total assets')

if __name__=='__main__':build()
