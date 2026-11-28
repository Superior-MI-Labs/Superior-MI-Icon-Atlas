#!/usr/bin/env python3
"""Derive static browser projection from canonical per-atlas manifests, stdlib only."""
from __future__ import annotations
import argparse
import json
import hashlib
import re
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from atlasctl import load,validate
from tools.sprite_grids import build_sprite_grids
from tools.browse_taxonomy import load_taxonomy, project_browse
from tools.browse_previews import build_region_previews
from tools.retain_archives import stage_current
from tools.asset_inventory import audit as audit_assets, source_collections, read_collection, archive_payload


def resolve_showcases(index,manifests,dest):
    """Project optional published demo links onto real assets, never pseudo-assets."""
    authored_ids={a['id'] for pack in manifests for a in pack['assets']}
    links,keywords,seen={},{},set()
    for showcase in index.get('showcases',[]):
        asset_id=showcase['asset'];page=showcase['page'];label=showcase['label']
        if (asset_id not in authored_ids or
            not re.fullmatch(r'[a-z0-9][a-z0-9_-]*\.html',page) or
            not (dest/page).is_file() or
            (asset_id,page) in seen or
            not isinstance(label,str) or not label.strip()):
            raise ValueError('Invalid/unpublished showcase: '+str(showcase))
        seen.add((asset_id,page))
        links.setdefault(asset_id,[]).append({'page':page,'label':label})
        keywords.setdefault(asset_id,[]).extend([label,*showcase.get('keywords',[])])
    return links,keywords


def visual_capabilities(asset, lookup, memo, active=None):
    """Derived affordances, not a certification of host or art compatibility."""
    ident=asset['id']
    if ident in memo:return memo[ident]
    active=set() if active is None else active
    if ident in active:raise ValueError('Cyclic published asset '+ident)
    active.add(ident)
    kind=asset['kind'];caps=set()
    if kind=='sequence' or asset.get('duration_ms'):caps.add('animated')
    if kind=='state_set':caps.add('states')
    if kind=='composition':
        caps.add('layered')
        if asset.get('inputs'):caps.add('typed-inputs')
        if asset.get('slots'):caps.add('compatible-slots')
        if asset.get('presets'):caps.add('presets')
        if asset.get('behavior',{}).get('on'):caps.add('visual-events')
        if 'use' in asset.get('behavior',{}).get('on',{}):caps.add('world-use')
    if asset.get('pivot') is not None:caps.add('authored-pivot')
    if asset.get('implements'):caps.add('slot-component')
    if asset.get('spatial'):
        caps.add('spatial-profile')
        if asset['spatial'].get('views'):caps.add('directional')
        if asset['spatial'].get('wind'):caps.add('wind-responsive')
    refs=([f['asset'] for f in asset['frames']] if kind=='sequence' else
          list(asset['states'].values()) if kind=='state_set' else
          [l['asset'] for l in asset.get('layers',[]) if 'asset' in l]+
          [v for s in asset.get('slots',{}).values() for v in s['options']] if kind=='composition' else [])
    refs += [ref for ref in asset.get('spatial',{}).get('views',{}).get('assets',[]) if ref!=ident]
    for ref in refs:
        if ref not in lookup:raise ValueError('Missing published dependency '+ref)
        if 'animated' in visual_capabilities(lookup[ref],lookup,memo,active):caps.add('animated')
    active.remove(ident);memo[ident]=sorted(caps);return memo[ident]


def build_collection_archive(folder, archive, record, publications):
    """One deterministic runtime ZIP, shared by collection QA and site publication."""
    archive.parent.mkdir(parents=True, exist_ok=True)
    index,packs=read_collection(folder)
    files,generated=archive_payload(ROOT,folder,index,packs,record,publications)
    with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=7) as z:
        for name,f in sorted(files.items()):
            if not f.is_file():raise ValueError('Missing runtime pack dependency: '+str(f))
            entry=ZipInfo(name,date_time=(2020,1,1,0,0,0))
            entry.compress_type=ZIP_DEFLATED
            entry.external_attr=(0o644<<16)
            payload=(json.dumps(generated,indent=2)+'\n').encode() if generated is not None and name=='collection.json' else f.read_bytes()
            z.writestr(entry,payload,compress_type=ZIP_DEFLATED,compresslevel=7)
    return archive


def build_one_collection(slug, archive):
    """Build only one authored collection, including its declared bundle dependencies."""
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        raise ValueError('Invalid collection slug: '+slug)
    folder=ROOT/'examples'/slug
    if folder not in source_collections(ROOT) or folder.resolve().parent!=(ROOT/'examples').resolve():
        raise ValueError('Unknown authored collection: '+slug)
    publication=json.loads((ROOT/'publications.json').read_text(encoding='utf-8'))
    if publication.get('schema')!='smi-publications/1':raise ValueError('Invalid publication policy')
    records=publication['collections']
    matches=[record for record in records if record['path']==folder.relative_to(ROOT).as_posix()]
    if len(matches)>1:raise ValueError('Duplicate publication record: '+slug)
    return build_collection_archive(folder, archive, matches[0] if matches else None, records)


def build(dest:Path|None=None):
    dest=Path(dest or ROOT/'site').resolve()
    m=load(ROOT)
    problems=validate(root=ROOT)
    if problems:raise ValueError('Invalid manifest: '+ '; '.join(problems[:5]))
    if dest==ROOT or ROOT in dest.parents and 'sheets' in dest.parts:
        raise ValueError('Refusing to build over source')
    dest.mkdir(parents=True,exist_ok=True)
    for name in ('index.html','styles.css','public-search.js','app.js','builder.html','builder.css','timeline-core.js','visual-core.js','input-core.js','collection-core.js','zip-core.js','bag-store.js','interaction-core.js','stat-core.js','slot-core.js','asset-renderer.js','builder.js','ai-guide.html','sky-motion-lab.html'):
        shutil.copy2(ROOT/'web'/name,dest/name)
    # Experimental preview sources; not a second Visual Atlas asset registry.
    motion_source=ROOT/'web'/'sky-motion-lab'
    motion_target=dest/'sky-motion-lab'
    if motion_target.exists():shutil.rmtree(motion_target)
    shutil.copytree(motion_source,motion_target)
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
    build_sprite_grids(dest/'templates')
    (dest/'demo').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'web'/'demo'/'starter-pack.zip',dest/'demo'/'starter-pack.zip')
    shutil.copy2(ROOT/'web'/'demo'/'potions-collection.zip',dest/'demo'/'potions-collection.zip')
    # Authored examples/ are the source of truth. Deterministic downloadable ZIPs are
    # generated here, never maintained as a second editable copy.
    publication=json.loads((ROOT/'publications.json').read_text(encoding='utf-8'))
    records={record['path']:record for record in publication['collections']}
    for folder in source_collections(ROOT):
        build_collection_archive(folder, dest/'demo'/(folder.name+'.zip'),
                                 records.get(folder.relative_to(ROOT).as_posix()), publication['collections'])

    def inspect_archive(path):
        with ZipFile(path) as z:
            files=set(z.namelist())
            index=json.loads(z.read('collection.json')) if 'collection.json' in files else None
            manifests=[]
            for name in sorted(files):
                if (name == 'manifest.json' or name.endswith('/manifest.json')) and z.getinfo(name).file_size <= 8 * 1024 * 1024:
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

    # Generate the playable prototype from the same authored ZIP as the Builder.
    # No second editable copy of animations or texture assets is published.
    sky=ROOT/'examples'/'sky-prototype'
    if (sky/'preview-template.html').is_file():
        html=(sky/'preview-template.html').read_text(encoding='utf-8')
        doc=json.loads((sky/'manifest.json').read_text(encoding='utf-8'))
        scene=json.loads((sky/'scenario.json').read_text(encoding='utf-8'))
        def embed(value):
            return json.dumps(value,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
        if html.count('__SKY_PACK_JSON__')!=1 or html.count('__SKY_SCENARIO_JSON__')!=1:
            raise ValueError('Sky template lost canonical placeholders')
        html=html.replace('__SKY_PACK_JSON__',embed(doc)).replace('__SKY_SCENARIO_JSON__',embed(scene))
        opener='<script>\n(()=>{'
        if html.count(opener)!=1 or html.count('image.src=record.path;')!=1:
            raise ValueError('Unexpected Sky playground script structure')
        html=html.replace(opener,'<script src="vendor/jszip.min.js"></script>\n<script>\n(async()=>{')
        loader="""const zipResponse=await fetch('demo/sky-prototype.zip');
if(!zipResponse.ok)throw Error('Prototype ZIP unavailable: '+zipResponse.status);
const zip=await JSZip.loadAsync(await zipResponse.arrayBuffer());
const textureUrls={};
for(const texture of Object.values(pack.textures)){
 const file=zip.file(texture.path);
 if(!file)throw Error('Missing texture '+texture.path);
 textureUrls[texture.path]=URL.createObjectURL(new Blob([await file.async('uint8array')],{type:'image/png'}));
}
"""
        html=html.replace('const textures={};let loaded=0;',loader+'const textures={};let loaded=0;')
        html=html.replace('image.src=record.path;','image.src=textureUrls[record.path];')
        ending='})();\n</script>'
        if html.count(ending)!=1:raise ValueError('Sky template terminator changed')
        html=html.replace(ending,"""})().catch(err=>{
 const p=document.createElement('p');p.textContent='Prototype failed to load: '+err.message;
 document.querySelector('.shell')?.prepend(p);
});
</script>""")
        (dest/'sky-prototype.html').write_text(html,encoding='utf-8')


    # Public discovery is derived from *approved* source manifests, never from
    # tutorial/demo ZIPs, private browser bags, or the archival monoline catalog.
    if publication.get('schema')!='smi-publications/1':raise ValueError('Invalid publication policy')
    inventory=audit_assets(ROOT)
    if inventory['errors']:raise ValueError('Asset inventory: '+'; '.join(inventory['errors'][:5]))
    (dest/'asset-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    public_assets=[];public_packs=[];seen_ids=set();seen_paths=set();browse_defaults={}
    if (dest/'previews').exists():shutil.rmtree(dest/'previews')
    for record in publication['collections']:
        folder=Path(record['path']); full=ROOT/folder
        if folder.is_absolute() or '..' in folder.parts or folder in seen_paths or not str(folder).startswith('examples/'):
            raise ValueError('Unsafe/duplicate published collection: '+str(folder))
        seen_paths.add(folder)
        if not record.get('approval') or not record.get('rights'):raise ValueError('Unapproved public collection')
        if record.get('visual_qa') not in ('reviewed','pending'):raise ValueError('Review status must be explicit')
        index,source_packs=read_collection(full)
        if index is None:raise ValueError('Published collection requires index: '+str(folder))
        manifests=[pack for _,pack in source_packs]
        expected=record.get('expected_assets')
        actual=sum(len(pack.get('assets',[])) for pack in manifests)
        if not isinstance(expected,int) or isinstance(expected,bool) or expected<1 or expected!=actual:
            raise ValueError(f'{folder}: publication inventory mismatch; expected {expected}, actual {actual}')
        pack_name=folder.name
        browse_defaults[pack_name]=index.get('classification',{})
        # Use the same generated ZIP as the existing builder importer.
        zip_name=pack_name+'.zip'
        if not (dest/'demo'/zip_name).is_file():raise ValueError('Missing published runtime ZIP: '+zip_name)
        pubpack={'id':pack_name,'name':index.get('name',pack_name),'zip':'demo/'+zip_name,
                 'published':record['published'],'visual_qa':record['visual_qa'],'entry':index['entry_asset'],
                 'archive_sha256':hashlib.sha256((dest/'demo'/zip_name).read_bytes()).hexdigest(),
                 'license':sorted({p.get('license','UNSPECIFIED') for p in manifests})}
        if any(l in ('UNSPECIFIED','UNKNOWN','') for l in pubpack['license']):raise ValueError('Unknown public license')
        public_packs.append(pubpack)
        showcases,keywords=resolve_showcases(index,manifests,dest)
        # Resolve dependencies from the exact derived archive (including bundled packs).
        with ZipFile(dest/'demo'/zip_name) as archive:
            runtime_index=json.loads(archive.read('collection.json'))
            runtime_packs=[json.loads(archive.read(ref['manifest'])) for ref in runtime_index['packs']]
            authored_ids={a['id'] for pack in manifests for a in pack['assets']}
            thumbnails=build_region_previews(archive,runtime_index,runtime_packs,authored_ids,dest)
        cover=next((a['id'] for pack in manifests for a in pack['assets'] if a['id'] in thumbnails and a.get('discovery','standalone')=='standalone'),None)
        if index['entry_asset'] in thumbnails:cover=index['entry_asset']
        if cover:pubpack['cover_asset']=cover
        lookup={a['id']:a for pack in runtime_packs for a in pack['assets']};cap_memo={}
        for pack in manifests:
            # Inherit style only when every styled source region agrees.
            region_styles={a['style'] for a in pack['assets'] if a['kind']=='region' and a.get('style')}
            inherited_style=next(iter(region_styles)) if len(region_styles)==1 else ''
            for a in pack['assets']:
                ident=a['id']
                if ident in seen_ids:raise ValueError('Duplicate public asset: '+ident)
                seen_ids.add(ident)
                # Exact names and tags come from the canonical manifest.
                capabilities=visual_capabilities(a,lookup,cap_memo)
                public_assets.append({
                    'capabilities':capabilities,'interfaces':sorted(a.get('implements',[])),
                    **({'spatial':a['spatial']} if 'spatial' in a else {}),
                    'slot_interfaces':sorted({v['accepts'] for v in a.get('slots',{}).values()}),
                    'id':ident,'name':a.get('name',ident.rsplit('.',1)[-1]),
                    **({'thumbnail':thumbnails[ident]} if ident in thumbnails else {}),
                    'kind':a['kind'],'discovery':a.get('discovery','standalone'),'style':a.get('style') or inherited_style,
                    **({'classification':a['classification']} if 'classification' in a else {}),
                    'tags':a.get('tags',[]),'subjects':a.get('subjects',[]),
                    'aliases':[*a.get('aliases',[]),*keywords.get(ident,[])],'concept_id':a.get('concept_id'),
                    'showcases':showcases.get(ident,[]),
                    'description':index.get('description','') if ident in showcases else a.get('description',''),
                    'variant':a.get('variant',''),'domain':a.get('domain') or index.get('name',pack_name),
                    'pack':pack_name,
                    'published':record['published'],'visual_qa':record['visual_qa'],'license':a.get('license',pack.get('license','')),
                    'category':index.get('name',pack_name),
                    'animated':'animated' in capabilities,
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

    browse=project_browse(public_assets,public_packs,browse_defaults,load_taxonomy())
    public_assets.sort(key=lambda a:(a['pack'],a['id']))
    stage_current(dest, {'schema':'smi-public-catalog/1','packs':public_packs})
    (dest/'public-catalog.json').write_text(json.dumps({'schema':'smi-public-catalog/1',
        'assets':public_assets,'packs':public_packs,'browse':browse,
        'synonyms':m.get('search',{}).get('synonyms',{}),'styles':m.get('styles',{}),
        'approved_count':approved_count,'discoverable_count':sum(not a.get('legacy') and a.get('discovery','standalone')=='standalone' for a in public_assets),'legacy_count':len(m['icons'])},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


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
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', nargs='?', type=Path, help='Full site output (default: site/)')
    parser.add_argument('--collection', help='Build only this authored collection slug')
    parser.add_argument('--out', type=Path, help='New output ZIP for --collection')
    args=parser.parse_args()
    if args.collection is not None:
        if args.destination is not None or args.out is None or args.out.suffix!='.zip' or args.out.exists():
            parser.error('--collection requires --out NEW.zip and no site destination')
        print('Built collection:',build_one_collection(args.collection,args.out.expanduser().resolve()))
    else:
        if args.out is not None:parser.error('--out requires --collection')
        path=(args.destination or ROOT/'site').expanduser().resolve()
        print(f'Built {build(path)} icons into {path}')