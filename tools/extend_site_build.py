# not a runtime module: patch tools/build_site.py after the existing renderer code is read.
from pathlib import Path
p=Path(__file__).with_name('build_site.py')
s=p.read_text()
s=s.replace('import json\n', 'import json\nfrom zipfile import ZipFile, ZIP_DEFLATED, ZipInfo\n')
s=s.replace("'builder.js','ai-guide.html')", "'builder.js','ai-guide.html','featured.js')")
s=s.replace('for guide in sorted((ROOT/\'docs\'/\'ai\').glob(\'*.md\')):\n        shutil.copy2(guide,dest/\'ai\'/guide.name)', '''for guide in sorted((ROOT/'docs'/'ai').rglob('*.md')):
        rel=guide.relative_to(ROOT/'docs'/'ai')
        target=dest/'ai'/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(guide,target)''')
s=s.replace("    src_files=['manifest.json','LICENSE','NOTICE.md']", '''    # Authored examples/ are the source of truth. Deterministic downloadable ZIPs are
    # generated here, never maintained as a second editable copy.
    for folder in sorted((ROOT/'examples').iterdir()):
        if not folder.is_dir() or not (folder/'manifest.json').is_file(): continue
        archive=dest/'demo'/(folder.name+'.zip')
        with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=7) as z:
            for f in sorted(folder.rglob('*')):
                if not f.is_file() or f.suffix.lower() not in {'.json','.png','.md'}: continue
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
    (dest/'featured-packs.json').write_text(json.dumps({'schema':'smi-featured-packs/1','packs':featured},indent=2)+'\\n',encoding='utf-8')

    src_files=['manifest.json','LICENSE','NOTICE.md']''')
p.write_text(s)
print('updated',p)
