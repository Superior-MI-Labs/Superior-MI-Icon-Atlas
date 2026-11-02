#!/usr/bin/env python3
"""Deterministically extract 16 *candidate* item sprites from provided original concept image.

Source is NOT a pixel-exact atlas and not true alpha; extract conservatively,
never claim production approval without visual crop review. Requires Pillow/numpy/OpenCV.
"""
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'source-expansion.png'
NAMES=['Azure Crystal','Iron Ore','Rolled Leather','Timber Log','Ruby Gemstone','Arcane Ink','Rune Hammer','Lockpicks','Frost Ward','Venom Dagger','Healing Herb','Spiked Mace','Energy Elixir','Brass Compass','Necrotic Curse','Crystal Wand']
SLUGS=['material.azure_crystal','material.iron_ore','material.rolled_leather','material.timber_log','material.ruby_gemstone','material.arcane_ink','tool.rune_hammer','tool.lockpicks','ability.frost_ward','weapon.venom_dagger','material.healing_herb','weapon.spiked_mace','potion.energy_elixir','tool.brass_compass','ability.necrotic_curse','weapon.crystal_wand']

def extract(im,col,row):
    # The generator positions each item *approximately* in a 4x4 layout.
    w,h=im.size
    x0=round(col*w/4); x1=round((col+1)*w/4)
    y0=round(row*h/4); y1=round((row+1)*h/4)
    src=np.array(im.crop((x0,y0,x1,y1)).convert('RGB'),dtype=np.uint8)
    mi=src.min(axis=2).astype(float); ma=src.max(axis=2).astype(float); sat=ma-mi
    # A faint off-white checkerboard is baked into the RGB source. Identify
    # colored/dark material, not the checkerboard, without trusting source grid pixel geometry.
    confident=(mi<235)|(sat>23)
    plausible=(mi<245)|(sat>14)
    confident[:3,:]=False;confident[-3:,:]=False;confident[:,:3]=False;confident[:,-3:]=False
    mask=np.where(plausible,cv2.GC_PR_FGD,cv2.GC_PR_BGD).astype('uint8')
    mask[:5,:]=cv2.GC_BGD;mask[-5:,:]=cv2.GC_BGD
    mask[:,:5]=cv2.GC_BGD;mask[:,-5:]=cv2.GC_BGD
    mask[confident]=cv2.GC_FGD
    bg=np.zeros((1,65),np.float64); fg=np.zeros((1,65),np.float64)
    cv2.grabCut(src,mask,None,bg,fg,4,cv2.GC_INIT_WITH_MASK)
    binary=np.where((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD),255,0).astype(np.uint8)
    n,labels,stats,_=cv2.connectedComponentsWithStats(binary,8)
    for i in range(1,n):
        x,y,ww,hh,area=[int(v) for v in stats[i]]
        if area<16:binary[labels==i]=0
    # Preserve intentionally separated sparks/particles above the main silhouettes.
    # Avoid output at sheet edges; original source is sampled at true 4x4 boundaries.
    binary[:5,:]=0;binary[-5:,:]=0;binary[:,:5]=0;binary[:,-5:]=0
    ys,xs=np.where(binary>0)
    if len(xs)<800:raise ValueError(f'Empty or insufficient sprite at {row},{col}')
    loX,hiX=max(0,xs.min()-2),min(src.shape[1],xs.max()+3)
    loY,hiY=max(0,ys.min()-2),min(src.shape[0],ys.max()+3)
    spr=src[loY:hiY,loX:hiX,:].astype(np.float32)
    alpha=binary[loY:hiY,loX:hiX].astype(np.uint8)
    # Stop opaque white fringes from false-background extraction.
    # Decontaminate pale edge pixels by applying a simple 1 px matte fade.
    er=cv2.erode(alpha,np.ones((3,3),np.uint8))
    edge=(alpha>0)&(er==0)
    # Edges are semi-transparent; the core stays opaque, leaving deliberate pixel clusters.
    alpha[edge]=np.where((spr[edge].min(axis=1)>226)&((spr[edge].max(axis=1)-spr[edge].min(axis=1))<30),0,160).astype(np.uint8)
    # Retain detailed source color, do not recolor or invent silhouettes.
    rgba=np.dstack([spr.astype(np.uint8),alpha])
    obj=Image.fromarray(rgba,'RGBA')
    lim=112
    scale=min(lim/obj.width,lim/obj.height)
    # Downsample with nearest neighbor to preserve intentionally chunky pixel clusters.
    obj=obj.resize((max(1,round(obj.width*scale)),max(1,round(obj.height*scale))),Image.Resampling.NEAREST)
    tile=Image.new('RGBA',(128,128));tile.alpha_composite(obj,((128-obj.width)//2,(128-obj.height)//2))
    return tile

def build():
    source=Image.open(SOURCE)
    assert source.size==(1254,1254), f'Unexpected input geometry {source.size}; recalibrate extraction'
    atlas=Image.new('RGBA',(512,512))
    for i,(name,slug) in enumerate(zip(NAMES,SLUGS)):
        tile=extract(source,i%4,i//4)
        tile.save(ROOT/'qa'/f'extracted-{i:02d}.png')
        atlas.alpha_composite(tile,((i%4)*128,(i//4)*128))
    out=ROOT/'textures'/'icons-01.png'
    atlas.save(out,optimize=True,compress_level=9)
    print('saved',out,out.stat().st_size,'bytes')
if __name__=='__main__':build()
