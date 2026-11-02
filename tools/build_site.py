#!/usr/bin/env python3
"""Derive static browser projection from canonical per-atlas manifests, stdlib only."""
from __future__ import annotations
import json
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from atlasctl import load,validate


def build(dest:Path|None=None):
    dest=Path(dest or ROOT/'site').resolve()
    m=load(ROOT)
    problems=validate(root=ROOT)
    if problems:raise ValueError('Invalid manifest: '+ '; '.join(problems[:5]))
    if dest==ROOT or ROOT in dest.parents and 'sheets' in dest.parts:
        raise ValueError('Refusing to build over source')
    dest.mkdir(parents=True,exist_ok=True)
    for name in ('index.html','styles.css','public-search.js','app.js','builder.html','builder.css','timeline-core.js','visual-core.js','collection-core.js','bag-store.js','interaction-core.js','slot-core.js','asset-renderer.js','builder.js','ai-guide.html','featured.js'):
        shutil.copy2(ROOT/'web'/name,dest/name)
    vendor=ROOT/'web'/'vendor'
    if not (vendor/'jszip.min.js').is_file() or not (vendor/'JSZip-LICENSE.md').is_file(): raise ValueError('Missing bundled offline ZIP library')
    (dest/'vendor').mkdir(exist_ok=True)
    shutil.copy2(vendor/'jszip.min.js',dest/'vendor'/'jszip.min.js')
    shutil.copy2(vendor/'JSZip-LICENSE.md',dest/'vendor'/'JSZip-LICENSE.md')
    (dest/'schemas').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'schemas'/'smi-visual-pack-v1.schema.json',dest/'schemas'/'smi-visual-pack-v1.schema.json')
    shutil.copy2(ROOT/'schemas'/'smi-visual-collection-v1.schema.json',dest/'schemas'/'smi-visual-collection-v1.schema.json')
    # One canonical AI handoff split into short, versioned references.
    (dest/'ai').mkdir(exist_ok=True)
    for guide in sorted((ROOT/'docs'/'ai').rglob('*.md')):
        rel=guide.relative_to(ROOT/'docs'/'ai')
        target=dest/'ai'/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        # Source docs link to repo tests; hosted docs link to bundled QA examples.
        # Rewrite derived docs only, never modify the authored source links.
        content=guide.read_text(encoding='utf-8')
        source_ref=('../../../tests/visual-scenarios.json' if len(rel.parts)>1 else '../../tests/visual-scenarios.json')
        hosted_ref=('../../qa/visual-scenarios.json' if len(rel.parts)>1 else '../qa/visual-scenarios.json')
        target.write_text(content.replace(source_ref,hosted_ref),encoding='utf-8')
    # Publish authored production guides at the same relative site paths used
    # by the AI recipes; never publish duplicate hand-edited copies.
    for guide in sorted((ROOT/'docs'/'asset-production').glob('*.md')):
        target=dest/'asset-production'/guide.name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(guide,target)
    (dest/'qa').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'tests'/'visual-scenarios.json',dest/'qa'/'visual-scenarios.json')
    (dest/'templates').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'web'/'templates'/'authoring-grids.zip',dest/'templates'/'authoring-grids.zip')
    (dest/'demo').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'web'/'demo'/'starter-pack.zip',dest/'demo'/'starter-pack.zip')
    shutil.copy2(ROOT/'web'/'demo'/'potions-collection.zip',dest/'demo'/'potions-collection.zip')
    # Authored examples/ are the source of truth. Deterministic downloadable ZIPs are
    # generated here, never maintained as a second editable copy.
    for folder in sorted((ROOT/'examples').iterdir()):
        if not folder.is_dir() or not (folder/'manifest.json').is_file(): continue
        archive=dest/'demo'/(folder.name+'.zip')
        with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=7) as z:
            for f in sorted(folder.rglob('*')):
                if not f.is_file() or f.name=='preview.png' or f.suffix.lower() not in {'.json','.png','.md'}: continue
                entry=ZipInfo(f.relative_to(folder).as_posix(),date_time=(2020,1,1,0,0,0))
                entry.compress_type=ZIP_DEFLATED
                entry.external_attr=(0o644<<16)
                z.writestr(entry,f.read_bytes(),compress_type=ZIP_DEFLATED,compresslevel=7)

    def inspect_archive(path):
        with ZipFile(path) as z:
            files=set(z.namelist())
            index=json.loads(z.read('collection.json')) if 'collection.json' in files else None
            manifests=[]
            for name in sorted(files):
                if name.endswith('.json') and z.getinfo(name).file_size<1024*1024:
                    doc=json.loads(z.read(name))
                    if doc.get('schema')=='smi-visual-pack/1':manifests.append(doc)
            if not manifests:raise ValueError(f'No pack manifest: {path.name}')
            assets=[a for pack in manifests for a in pack['assets']]
            entry=index.get('entry_asset') if index else next((a['id'] for a in reversed(assets) if a['kind'] in ('composition','state_set','sequence')),assets[0]['id'])
            asset=next((a for a in assets if a['id']==entry),assets[-1])
            name=index.get('name') if index else asset.get('name') or path.stem.replace('-',' ').title()
            description=index.get('description','') if index else manifests[0].get('description','')
            return {'filename':path.name,'title':name,'description':description,
              'entry':entry,'assets':len(assets),'manifests':len(manifests),
              'kinds':sorted({a['kind'] for a in assets}),
              'tags':sorted({tag for a in assets for tag in a.get('tags',[])})[:24],
              'license':sorted({str(p.get('license','UNSPECIFIED')) for p in manifests})}
    featured=[inspect_archive(path) for path in sorted((dest/'demo').glob('*.zip'))]
    # Optional gallery artwork belongs to the authored example, not a second catalog.
    # Never include editorial preview art inside the runtime ZIP for that example.
    for item in featured:
        stem=Path(item['filename']).stem
        preview=ROOT/'examples'/stem/'preview.png'
        if preview.is_file():
            target=dest/'showcase'/f'{stem}.png'
            target.parent.mkdir(exist_ok=True)
            shutil.copy2(preview,target)
            item['preview']='showcase/'+target.name
    (dest/'featured-packs.json').write_text(json.dumps({'schema':'smi-featured-packs/1','packs':featured},indent=2)+'\n',encoding='utf-8')

    # Public discovery is derived from *approved* source manifests, never from
    # tutorial/demo ZIPs, private browser bags, or the archival monoline catalog.
    publication=json.loads((ROOT/'publications.json').read_text(encoding='utf-8'))
    if publication.get('schema')!='smi-publications/1':raise ValueError('Invalid publication policy')
    public_assets=[];public_packs=[];seen_ids=set();seen_paths=set()
    for record in publication['collections']:
        folder=Path(record['path']); full=ROOT/folder
        if folder.is_absolute() or '..' in folder.parts or folder in seen_paths or not str(folder).startswith('examples/'):
            raise ValueError('Unsafe/duplicate published collection: '+str(folder))
        seen_paths.add(folder)
        if not record.get('approval') or not record.get('rights'):raise ValueError('Unapproved public collection')
        index=json.loads((full/'collection.json').read_text(encoding='utf-8'))
        if index.get('schema')!='smi-visual-collection/1':raise ValueError('Invalid public collection index')
        manifests=[]
        for ref in index['packs']:
            relpath=Path(ref['manifest'])
            if relpath.is_absolute() or '..' in relpath.parts:raise ValueError('Unsafe manifest path')
            manifests.append(json.loads((full/relpath).read_text(encoding='utf-8')))
        if not manifests:raise ValueError('Empty public collection')
        expected=record.get('expected_assets')
        actual=sum(len(pack.get('assets',[])) for pack in manifests)
        if not isinstance(expected,int) or isinstance(expected,bool) or expected<1 or expected!=actual:
            raise ValueError(f'{folder}: publication inventory mismatch; expected {expected}, actual {actual}')
        pack_name=folder.name
        # Use the same generated ZIP as the existing builder importer.
        zip_name=pack_name+'.zip'
        if not (dest/'demo'/zip_name).is_file():raise ValueError('Missing published runtime ZIP: '+zip_name)
        pubpack={'id':pack_name,'name':index.get('name',pack_name),'zip':'demo/'+zip_name,
                 'published':record['published'],'entry':index['entry_asset'],
                 'license':sorted({p.get('license','UNSPECIFIED') for p in manifests})}
        if any(l in ('UNSPECIFIED','UNKNOWN','') for l in pubpack['license']):raise ValueError('Unknown public license')
        public_packs.append(pubpack)
        for pack in manifests:
            # Inherit style only when every styled source region agrees.
            region_styles={a['style'] for a in pack['assets'] if a['kind']=='region' and a.get('style')}
            inherited_style=next(iter(region_styles)) if len(region_styles)==1 else ''
            for a in pack['assets']:
                ident=a['id']
                if ident in seen_ids:raise ValueError('Duplicate public asset: '+ident)
                seen_ids.add(ident)
                # Exact names and tags come from the canonical manifest.
                public_assets.append({
                    'id':ident,'name':a.get('name',ident.rsplit('.',1)[-1]),
                    'kind':a['kind'],'style':a.get('style') or inherited_style,
                    'tags':a.get('tags',[]),'subjects':a.get('subjects',[]),
                    'aliases':a.get('aliases',[]),'concept_id':a.get('concept_id'),
                    'variant':a.get('variant',''),'domain':a.get('domain') or index.get('name',pack_name),
                    'pack':pack_name,
                    'published':record['published'],'license':a.get('license',pack.get('license','')),
                    'category':index.get('name',pack_name),
                    'animated':a['kind']=='sequence' or bool(a.get('duration_ms')),
                    'previewable':a['kind']!='region' or bool(a.get('rect_px'))
                })
    if not any(a['kind']=='composition' for a in public_assets):raise ValueError('No published finished compositions')
    approved_count=len(public_assets)
    # Historical icons use the original authoritative smi-icon-atlas/3 loader.
    # They are searchable as a clearly flagged archive, not approved new artwork.
    legacy_pack='legacy-icons'
    public_packs.append({'id':legacy_pack,'name':'Legacy Icons · Review Required',
                         'zip':None,'published':'2026-10-29','license':['Apache-2.0'],
                         'archived':True})
    for icon in m['icons']:
        r=icon['rect_px']
        if icon['id'] in seen_ids:raise ValueError('Archive ID collision: '+icon['id'])
        seen_ids.add(icon['id'])
        public_assets.append({
            'id':icon['id'],'name':icon['name'],'kind':'region',
            'style':icon['style'],'tags':icon['tags'],'subjects':icon['subjects'],
            'aliases':icon['aliases'],'concept_id':icon['concept_id'],'domain':icon['domain'],
            'variant':icon['variant'],'quality':icon['quality'],
            'pack':legacy_pack,'published':'2026-10-29',
            'license':icon['license'],'category':'Legacy Icons','animated':False,
            'previewable':True,'legacy':True,'review_status':icon['review_status'],
            'rights_reviewed':icon['provenance']['licensing_review'],
            'texture':icon['sheet'],'rect_px':[r['x'],r['y'],r['w'],r['h']]
        })

    public_assets.sort(key=lambda a:(a['pack'],a['id']))
    (dest/'public-catalog.json').write_text(json.dumps({'schema':'smi-public-catalog/1',
        'assets':public_assets,'packs':public_packs,
        'synonyms':m.get('search',{}).get('synonyms',{}),'styles':m.get('styles',{}),
        'approved_count':approved_count,'legacy_count':len(m['icons'])},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


    src_files=['manifest.json','LICENSE','NOTICE.md']
    registry=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    src_files.extend(ref['manifest'] for ref in registry['sheets'])
    assets=set()
    for sh in m['sheets']:
        assets.update(sh[k] for k in ('path','foreground_mask','black_outline'))
    for name in [*src_files,*sorted(assets)]:
        src=ROOT/name;target=dest/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,target)
    (dest/'.nojekyll').write_text('')
    # Read-only derived projection. No second manually editable icon registry.
    data={
        'version':m.get('version'), 'pack':m.get('pack'),
        'styles':m.get('styles',{}), 'synonyms':m.get('search',{}).get('synonyms',{}),
        'sheets':[{k:sh.get(k) for k in ('path','foreground_mask','black_outline','width_px','height_px','cell_px','style','domain')} for sh in m['sheets']],
        'icons':[{k:i.get(k) for k in ('id','name','concept_id','aliases','tags','subjects','review_status','quality','domain','style','variant','license','rect_px','sheet')} for i in m['icons']]
    }
    js=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    (dest/'catalog-data.js').write_text('"use strict";window.ICON_ATLAS_DATA='+js+';\n',encoding='utf-8')
    return len(m['icons'])

if __name__=='__main__':
    path=ROOT/'site' if len(sys.argv)<2 else Path(sys.argv[1]).expanduser().resolve()
    print(f'Built {build(path)} icons into {path}')