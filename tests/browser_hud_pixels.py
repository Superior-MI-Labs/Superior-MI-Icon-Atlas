#!/usr/bin/env python3
"""Optional REAL Chromium render QA: actual input 0/50/100 canvas pixels must differ.

Run AFTER tools/build_site.py. Requires playwright, Pillow and an installed Chromium.
No network, GitHub Pages connection, or locally running web server is needed.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import sys,tempfile
from PIL import Image
from io import BytesIO
import base64,json,re
root=Path(__file__).resolve().parents[1]
outdir=Path(sys.argv[1]) if len(sys.argv)>1 else Path(tempfile.gettempdir())/'smi-hud-browser-qa'
outdir.mkdir(parents=True,exist_ok=True)
site=root/'site'
def stripped(p):
    return re.sub(r'<script\b[^>]*\bsrc="[^"]+"[^>]*></script>','',(site/p).read_text())
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1540,'height':1024},device_scale_factor=1)
    errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(stripped('builder.html'))
    page.add_style_tag(content=(site/'styles.css').read_text())
    page.add_style_tag(content=(site/'builder.css').read_text())
    data={
      'index':json.loads((site/'featured-packs.json').read_text()),
      'zip':base64.b64encode((site/'demo/interactive-hud.zip').read_bytes()).decode()
    }
    page.evaluate('''(data)=>{
      window.ICON_ATLAS_DATA={version:'QA',sheets:[],icons:[]};
      window.fetch=async url=>{
        const s=String(url);
        if(s==='featured-packs.json')return new Response(JSON.stringify(data.index),{status:200});
        if(s==='demo/interactive-hud.zip'){
          const raw=atob(data.zip),u=new Uint8Array(raw.length);
          for(let i=0;i<raw.length;i++)u[i]=raw.charCodeAt(i);
          return new Response(u,{status:200,headers:{'Content-Type':'application/zip'}});
        }
        return new Response('',{status:404});
      };
    }''',data)
    for name in ['vendor/jszip.min.js','timeline-core.js','visual-core.js','collection-core.js','bag-store.js','interaction-core.js','slot-core.js','builder.js']:
      src=(site/name).read_text()
      if name=='builder.js':src=src.replace("new URLSearchParams(location.search).get('example')", "'interactive-hud.zip'")
      page.add_script_tag(content=src)
    page.locator('#builder-status').get_by_text('Opened interactive-hud.zip',exact=False).wait_for(timeout=20000)
    print('status:',page.locator('#builder-status').inner_text())
    page.locator('#preview-name').get_by_text('Interactive energy meter',exact=False).wait_for(timeout=5000)
    slider=page.locator('#input-controls input[type=range]')
    assert slider.count()==1,slider.count()
    counts=[]
    for value in (0,50,100):
      slider.evaluate('(node,v)=>{node.value=String(v); node.dispatchEvent(new Event("input",{bubbles:true}));}',value)
      page.wait_for_timeout(300)
      png=page.locator('#stage').screenshot()
      im=Image.open(BytesIO(png)).convert('RGBA')
      # Count distinctly green pixels, independently of outputs or controls
      green=sum(1 for r,g,b,a in im.get_flattened_data() if a>100 and g>r*1.25 and g>b*1.10 and g>70)
      counts.append(green)
      out=outdir/f'meter-{value}.png';out.write_bytes(png)
      print('input',value,'green pixels',green,'outputs:',page.locator('#interaction-outputs').inner_text())
    print('pageerrors',errors)
    assert not errors,errors
    assert counts[0] < counts[1] < counts[2],counts
    assert counts[0] < 10 and counts[1]>250 and counts[2]>counts[1]*1.45,counts
    page.screenshot(path=str(outdir/'builder-screenshot.png'),full_page=True)
    print('PASS: actual Chromium canvas green-fill area increases 0 -> 50 -> 100, with numeric outputs')
    browser.close()
