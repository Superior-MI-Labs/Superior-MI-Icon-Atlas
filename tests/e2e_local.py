"""Optional real-Chromium UI test. Loads authentic PNG bytes as data URLs because
some restricted environments block *all* navigation (even localhost/file URLs).

Production hosting is covered by the static build and path-integrity tests.
"""
import base64
import json
from pathlib import Path
import tempfile
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
site=ROOT/'site'
data=(site/'catalog-data.js').read_text(encoding='utf-8')
data=json.loads(data.split('window.ICON_ATLAS_DATA=',1)[1].rsplit(';',1)[0])
urlmap={}
for s in data['sheets']:
  for key in ('path','foreground_mask','black_outline'):
    path=s[key]
    if path not in urlmap:
      urlmap[path]='data:image/png;base64,'+base64.b64encode((site/path).read_bytes()).decode('ascii')
    s[key]=urlmap[path]
for entry in data['icons']:entry['sheet']=urlmap[entry['sheet']]
# One real icon is sufficient for testing canvas; avoids huge CSS data URLs in restricted Chromium.
data['icons']=[x for x in data['icons'] if x['id']=='icons.original.programming.bug.symbol']

with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
  context=browser.new_context(accept_downloads=True,viewport={'width':1350,'height':920},device_scale_factor=1)
  page=context.new_page()
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  html=(site/'index.html').read_text(encoding='utf-8')
  html=html.replace('<link rel="stylesheet" href="styles.css">','').replace('<script src="catalog-data.js" defer></script>','').replace('<script src="app.js" defer></script>','')
  print('setting content',flush=True)
  page.set_content(html,timeout=15000)
  print('injecting stylesheet',flush=True)
  page.add_style_tag(content=(site/'styles.css').read_text(encoding='utf-8'))
  print('injecting catalog',flush=True)
  page.add_script_tag(content='window.ICON_ATLAS_DATA='+json.dumps(data)+';')
  print('injecting app',flush=True)
  page.add_script_tag(content=(site/'app.js').read_text(encoding='utf-8'))
  print('rendered',flush=True)
  assert page.locator('article.item').count()==1
  page.screenshot(path=str(ROOT/'site-preview.png'),full_page=False)
  page.locator('#search').fill('bug')
  print('bug search results',page.locator('article.item').count())
  assert page.locator('article.item').count()==1
  page.locator('article.item button.thumb-btn').first.click()
  assert page.locator('#detail').evaluate('(e)=>e.open')
  expected=page.locator('#detail-id').inner_text()+'.png'
  with page.expect_download(timeout=20000) as info: page.locator('#download').click()
  dl=info.value
  assert dl.suggested_filename==expected
  with tempfile.TemporaryDirectory() as td:
    path=Path(td)/expected;dl.save_as(str(path))
    img=Image.open(path)
    print('PNG',dl.suggested_filename,img.size,img.mode,'corner',img.getpixel((0,0)))
    assert img.size==(96,96) and img.mode=='RGBA' and img.getpixel((0,0))[3]==0
    page.locator('#tint-enabled').check()
    page.locator('#tint-color').fill('#00ff00')
    with page.expect_download(timeout=20000) as other:page.locator('#download').click()
    tint_dl=other.value
    assert tint_dl.suggested_filename==expected
    tint_path=Path(td)/'green.png';tint_dl.save_as(str(tint_path))
    rgba=Image.open(tint_path).convert('RGBA');pix=list(rgba.getdata())
    assert any(g>r+40 for r,g,b,a in pix if a>0)
    assert any(r==g==b==0 and a>0 for r,g,b,a in pix)
  assert not errors,errors
  print('PASS: gallery, search, detail, transparent PNG crop, exact ID filename, tint, unchanged black outline')
  browser.close()
