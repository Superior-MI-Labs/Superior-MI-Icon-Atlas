#!/usr/bin/env python3
"""Conservatively isolate complete art from the 4x4 dark-matte source sheet.

Source is a *review candidate*, not a pixel-exact original alpha atlas. Never
trim a silhouette to force it inside bounds: crop only per measured source-cell
interiors; fail if any foreground touches an edge. Source coverage QA runs prior
to resizing, so a damaged sprite cannot be hidden by post-resize margins.
"""
from pathlib import Path
import cv2, numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent
NAMES=['Ornate Key','Treasure Chest','Traveler Journal','Rune Tablet','Forest Mushroom','Rustic Bread','Gold Pouch','Blueberries','Flame Sword','Verdant Staff','Lightning Bolt','Healing Aura','Amethyst Cluster','Golden Bell','Treasure Map','Amethyst Necklace']
SLUGS=['quest.ornate_key','quest.treasure_chest','item.traveler_journal','quest.rune_tablet','food.forest_mushroom','food.rustic_bread','currency.gold_pouch','food.blueberries','weapon.flame_sword','weapon.verdant_staff','ability.lightning_bolt','ability.healing_aura','material.amethyst_cluster','item.golden_bell','quest.treasure_map','accessory.amethyst_necklace']

def extract(src, col, row):
  h,w=src.shape[:2];x0=round(w*col/4);y0=round(h*row/4);x1=round(w*(col+1)/4);y1=round(h*(row+1)/4)
  rgb=src[y0:y1,x0:x1].copy();hh,ww=rgb.shape[:2]
  # The matte is dark navy and mildly gradient; infer it from outer cell border,
  # then protect foreground pixels by brightness/chroma and GrabCut context.
  border=np.concatenate([rgb[:20,:,:].reshape(-1,3),rgb[-20:,:,:].reshape(-1,3),rgb[:, :20,:].reshape(-1,3),rgb[:,-20:,:].reshape(-1,3)],axis=0)
  color=np.median(border,axis=0)
  dist=np.linalg.norm(rgb.astype('float32')-color,axis=2)
  maxi=rgb.max(axis=2);mini=rgb.min(axis=2);sat=maxi.astype('int16')-mini.astype('int16')
  mask=np.full((hh,ww),cv2.GC_PR_BGD,dtype='uint8')
  mask[(dist>27)|(maxi>84)|(sat>53)]=cv2.GC_PR_FGD
  mask[(dist>65)&((maxi>115)|(sat>70))]=cv2.GC_FGD
  rim=18
  mask[:rim,:]=cv2.GC_BGD;mask[-rim:,:]=cv2.GC_BGD;mask[:,:rim]=cv2.GC_BGD;mask[:,-rim:]=cv2.GC_BGD
  if np.count_nonzero(mask==cv2.GC_FGD)<150:raise ValueError(f'no definite foreground: {row},{col}')
  bg=np.zeros((1,65),np.float64);fg=np.zeros((1,65),np.float64)
  cv2.grabCut(rgb,mask,None,bg,fg,4,cv2.GC_INIT_WITH_MASK)
  binary=np.isin(mask,[cv2.GC_FGD,cv2.GC_PR_FGD]).astype('uint8')*255
  # Reject tiny, distant matte specks, but preserve glow and separated decorations.
  n,lab,st,_=cv2.connectedComponentsWithStats(binary,8)
  if n<2:raise ValueError(f'empty {row},{col}')
  largest=int(1+np.argmax(st[1:,4]));primary=st[largest]; cx=primary[0]+primary[2]/2;cy=primary[1]+primary[3]/2
  for j in range(1,n):
    if j==largest:continue
    x,y,cw,ch,area=[int(z) for z in st[j]]
    if area<7 or ((x+cw/2-cx)**2+(y+ch/2-cy)**2)**.5>ww*.43:binary[lab==j]=0
  ys,xs=np.where(binary>0)
  if len(xs)<400:raise ValueError(f'too small {row},{col}')
  raw_bbox=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
  raw_margins=[raw_bbox[0],raw_bbox[1],ww-raw_bbox[2],hh-raw_bbox[3]]
  if min(raw_margins)<15:raise ValueError(f'SOURCE TRUNCATED: {row},{col}: margins {raw_margins}')
  xA=max(0,raw_bbox[0]-2);xB=min(ww,raw_bbox[2]+2);yA=max(0,raw_bbox[1]-2);yB=min(hh,raw_bbox[3]+2)
  rgba=np.dstack((rgb,binary))
  icon=Image.fromarray(rgba,'RGBA').crop((xA,yA,xB,yB))
  scale=min(111/icon.width,111/icon.height)
  icon=icon.resize((max(1,round(icon.width*scale)),max(1,round(icon.height*scale))),Image.Resampling.NEAREST)
  tile=Image.new('RGBA',(128,128));tile.alpha_composite(icon,((128-icon.width)//2,(128-icon.height)//2))
  return tile,{'raw_bbox':raw_bbox,'source_margins':raw_margins,'source_cell':[x0,y0,x1-x0,y1-y0]}

def build():
  im=Image.open(ROOT/'source-wave3.png').convert('RGB');a=np.array(im)
  atlas=Image.new('RGBA',(512,512));data=[]
  (ROOT/'qa').mkdir(exist_ok=True)
  for i,(name,slug) in enumerate(zip(NAMES,SLUGS)):
    tile,info=extract(a,i%4,i//4);atlas.alpha_composite(tile,((i%4)*128,(i//4)*128))
    tile.save(ROOT/'qa'/f'wave3-{i:02d}.png')
    data.append({'name':name,'slug':slug,**info})
  atlas.save(ROOT/'textures/icons-02.png',optimize=True,compress_level=9)
  (ROOT/'qa/wave3-source-coverage.json').write_text(__import__('json').dumps(data,indent=2)+'\n')
  print('Wave3 extracted 16 icons. Saved 512x512 PNG.')
if __name__=='__main__':build()
