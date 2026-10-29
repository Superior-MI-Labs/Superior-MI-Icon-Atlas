#!/usr/bin/env python3
"""Real browser visual-state acceptance for Visual Atlas ZIP collections.

This is a *separate* optional Chromium qualification gate. Requires Playwright,
Pillow and an installed Chromium. Never claims artwork semantics or visual polish.
Usage:
  python tests/browser_visual_matrix.py --spec tests/visual-scenarios.json --out /tmp/visual-qa

Scenario JSON is a versioned, no-code contract an AI can generate for a new pack.
Only manifests and images from explicit local ZIPs are loaded. No network server.
"""
from __future__ import annotations
import argparse
import base64
from io import BytesIO
import json
from pathlib import Path
import re
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'

SCRIPTS = (
    'vendor/jszip.min.js', 'timeline-core.js', 'visual-core.js',
    'collection-core.js', 'bag-store.js', 'interaction-core.js',
    'slot-core.js', 'builder.js',
)


def verify_spec(spec):
    if not isinstance(spec, dict) or spec.get('schema') != 'smi-visual-scenarios/1':
        raise ValueError('Expected smi-visual-scenarios/1')
    cases = spec.get('cases')
    if not isinstance(cases, list) or not 1 <= len(cases) <= 40:
        raise ValueError('Expected 1..40 visual cases')
    for case in cases:
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,70}', case.get('id', '')):
            raise ValueError('Case ID must be a safe slug')
        if not re.fullmatch(r'[a-z0-9-]+\.zip', case.get('pack', '')):
            raise ValueError('Pack must be a local ZIP basename')
        if not isinstance(case.get('preview_name'),str) or not case['preview_name'].strip():
            raise ValueError(f'{case["id"]}: missing preview_name')
        if case.get('asset') is not None and not re.fullmatch(r'[a-zA-Z0-9_.-]+',case['asset']):
            raise ValueError(f'{case["id"]}: invalid asset id')
        samples = case.get('samples')
        if not isinstance(samples, list) or not 2 <= len(samples) <= 20:
            raise ValueError(f'{case["id"]}: expected 2..20 samples')
        labels = [s.get('id') for s in samples]
        if any(not isinstance(x, str) or not re.fullmatch('[a-z0-9-]+', x) for x in labels) or len(labels) != len(set(labels)):
            raise ValueError(f'{case["id"]}: sample IDs must be unique slugs')
        for s in samples:
            if not isinstance(s.get('time_ms', 0), (int, float)) or s.get('time_ms', 0) < 0 or s.get('time_ms', 0) > 2000:
                raise ValueError(f'{case["id"]}: invalid time_ms')
            if not isinstance(s.get('inputs', {}), dict):
                raise ValueError(f'{case["id"]}: inputs must be an object')
        assertions = case.get('assertions')
        if not isinstance(assertions, list) or not assertions:
            raise ValueError(f'{case["id"]}: at least one assertion required')
        for rule in assertions:
            if rule.get('type') not in ('different', 'same', 'green_increases', 'output_equals'):
                raise ValueError(f'{case["id"]}: unsupported assertion {rule.get("type")}')
            keys = (rule.get('a'), rule.get('b')) if rule['type'] in ('different', 'same') else (
                rule.get('samples', []) if rule['type'] == 'green_increases' else (rule.get('sample'),))
            if any(k not in labels for k in keys):
                raise ValueError(f'{case["id"]}: assertion references missing sample')


def loaded_html():
    return re.sub(r'<script\b[^>]*\bsrc="[^"]+"[^>]*></script>', '', (SITE / 'builder.html').read_text())


def draw_sample(page, sample, out_file):
    for key, value in sample.get('inputs', {}).items():
        found = page.locator('#input-controls label').filter(has_text=re.compile(r'^\s*' + re.escape(key) + r'\s*', re.I))
        if found.count() != 1:
            raise AssertionError(f'Input {key} not found uniquely ({found.count()} controls)')
        control = found.locator('input,select').first
        tag, kind = control.evaluate('(e)=>[e.tagName.toLowerCase(),e.type]')
        if kind == 'checkbox':
            control.set_checked(bool(value))
        else:
            control.evaluate('''(e,v)=>{
                e.value=String(v);
                e.dispatchEvent(new Event(e.type==='range'?'input':'change',{bubbles:true}));
            }''', value)
    if 'state' in sample:
        control = page.locator('#input-controls label').filter(has_text=re.compile(r'^\s*State\s*', re.I)).locator('select').first
        control.select_option(sample['state'])
    if 'preset' in sample:
        control = page.locator('#input-controls label').filter(has_text=re.compile(r'^\s*Preset\s*', re.I)).locator('select').first
        control.select_option(sample['preset'])
    # Paused render clock controlled by the same public playhead the user can edit.
    page.locator('#playhead').evaluate('''(e,v)=>{
      e.value=String(v);e.dispatchEvent(new Event('input',{bubbles:true}));
    }''', sample.get('time_ms', 0))
    page.wait_for_timeout(160)
    raw = page.locator('#stage').evaluate('(e)=>e.toDataURL("image/png").split(",")[1]')
    data = base64.b64decode(raw)
    out_file.write_bytes(data)
    image = Image.open(BytesIO(data)).convert('RGBA')
    return image, page.locator('#interaction-outputs').inner_text() if page.locator('#interaction-outputs').count() else ''


def pixel_change(a, b, tolerance=12):
    if a.size != b.size:
        raise AssertionError(f'Canvas size mismatch: {a.size} vs {b.size}')
    changed = 0
    for p, q in zip(a.get_flattened_data(), b.get_flattened_data()):
        if max(abs(x-y) for x,y in zip(p,q)) > tolerance:
            changed += 1
    return changed


def green_count(im):
    return sum(1 for r,g,b,a in im.get_flattened_data() if a>100 and g>r*1.25 and g>b*1.10 and g>70)


def check_case(case, images, outputs):
    findings=[]
    for rule in case['assertions']:
        typ=rule['type'];ok=False
        if typ in ('different', 'same'):
            a,b=rule['a'],rule['b'];count=pixel_change(images[a],images[b],rule.get('tolerance',12))
            if typ == 'different':
                minimum=rule.get('min_changed_pixels', 40);ok=count>=minimum
                detail=f'{a}/{b}: {count} changed pixels (need >= {minimum})'
            else:
                maximum=rule.get('max_changed_pixels', 0);ok=count<=maximum
                detail=f'{a}/{b}: {count} changed pixels (need <= {maximum})'
        elif typ=='green_increases':
            values=[green_count(images[x]) for x in rule['samples']]
            minimum=rule.get('min_step', 100)
            ok=all(b-a>=minimum for a,b in zip(values,values[1:]))
            detail=f'green pixel counts {values}; each step must increase >= {minimum}'
        else:
            output=outputs[rule['sample']]
            try:
                parsed=json.loads(output.split('Outputs: ',1)[1]);actual=parsed.get(rule['field'])
            except (ValueError,IndexError,TypeError): actual=None
            expected=rule['equals'];ok=actual==expected
            detail=f'{rule["sample"]}: {rule["field"]}={actual!r}, expected {expected!r}'
        findings.append({'assertion':typ,'status':'PASS' if ok else 'FAIL','detail':detail})
    return findings


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--spec',type=Path,default=ROOT/'tests/visual-scenarios.json')
    ap.add_argument('--out',type=Path,default=Path('/tmp/smi-visual-matrix'))
    ap.add_argument('--chromium',default='',help='Optional explicit Chromium path; otherwise detect system or Playwright browser')
    args=ap.parse_args()
    spec=json.loads(args.spec.read_text());verify_spec(spec)
    if not (SITE/'builder.js').is_file():raise SystemExit('Build the site first: python tools/build_site.py')
    try:from playwright.sync_api import sync_playwright
    except ImportError:raise SystemExit('Browser QA requires: python -m pip install playwright')
    args.out.mkdir(parents=True,exist_ok=True)
    report={'schema':'smi-visual-render-qa/1','cases':[],'visual_semantic_review':'NOT AUTOMATICALLY VERIFIED'}
    failures=[]
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True,executable_path=(args.chromium or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else playwright.chromium.executable_path)),args=['--no-sandbox'])
        try:
            for case in spec['cases']:
                archive=SITE/'demo'/case['pack']
                if not archive.is_file():raise FileNotFoundError(archive)
                page=browser.new_page(viewport={'width':1500,'height':1024},device_scale_factor=1)
                errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.set_content(loaded_html())
                for css in ('styles.css','builder.css'):page.add_style_tag(content=(SITE/css).read_text())
                payload={'registry':json.loads((SITE/'featured-packs.json').read_text()),'zip':base64.b64encode(archive.read_bytes()).decode()}
                page.evaluate('''(data)=>{
                  window.ICON_ATLAS_DATA={version:'visual-QA',sheets:[],icons:[]};
                  window.fetch=async url=>{
                    const s=String(url);
                    if(s==='featured-packs.json')return new Response(JSON.stringify(data.registry),{status:200});
                    if(s==='demo/'+data.filename){
                      const raw=atob(data.zip),out=new Uint8Array(raw.length);
                      for(let i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i);
                      return new Response(out,{status:200,headers:{'Content-Type':'application/zip'}});
                    }
                    return new Response('',{status:404});
                  };
                }''',{**payload,'filename':case['pack']})
                for path in SCRIPTS:
                    src=(SITE/path).read_text()
                    if path=='builder.js':src=src.replace("new URLSearchParams(location.search).get('example')",json.dumps(case['pack']))
                    page.add_script_tag(content=src)
                page.locator('#builder-status').get_by_text('Opened '+case['pack'],exact=False).wait_for(timeout=15000)
                if case.get('asset'):
                    page.locator(f'#asset-list .asset-entry[data-asset-id="{case["asset"]}"]').click(timeout=5000)
                page.locator('#preview-name').get_by_text(case['preview_name'],exact=True).wait_for(timeout=5000)
                page.locator('#play').click() # freeze clock for deterministic captures
                samples={};outputs={};directory=args.out/case['id'];directory.mkdir(parents=True,exist_ok=True)
                for sample in case['samples']:
                    img, output=draw_sample(page,sample,directory/(sample['id']+'.png'))
                    samples[sample['id']]=img;outputs[sample['id']]=output
                findings=check_case(case,samples,outputs)
                if errors:findings.append({'assertion':'browser_page_errors','status':'FAIL','detail':'; '.join(errors)})
                status='PASS' if all(f['status']=='PASS' for f in findings) else 'FAIL'
                if status!='PASS':failures.append(case['id'])
                report['cases'].append({'id':case['id'],'pack':case['pack'],'status':status,'samples':list(samples),'findings':findings})
                print(status,case['id'])
                for f in findings:print('  ',f['status'],f['detail'])
                page.close()
        finally:browser.close()
    report['status']='FAIL' if failures else 'PASS'
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Final:',report['status'],'Cases:',len(report['cases']),'Evidence:',args.out)
    return 1 if failures else 0

if __name__=='__main__':sys.exit(main())
