"""Project browse metadata without changing canonical runtime assets or ZIPs."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FIELDS=('category_path','perspective','theme','medium')


def load_taxonomy(path=ROOT/'browse-taxonomy.json'):
    taxonomy=json.loads(Path(path).read_text(encoding='utf-8'))
    if taxonomy.get('schema')!='smi-browse-taxonomy/1' or set(taxonomy['dimensions'])!=set(FIELDS):
        raise ValueError('Invalid browse taxonomy')
    categories=taxonomy['dimensions']['category_path']['values']
    if any('.' in key and key.rsplit('.',1)[0] not in categories for key in categories):
        raise ValueError('Missing category parent')
    for rule in taxonomy['rules']:
        if not set(rule)<= {'packs','domain','subjects','set'} or not set(rule)-{'set'}:
            raise ValueError('Invalid browse migration rule')
        validate_values(rule['set'],taxonomy)
    return taxonomy


def validate_values(values,taxonomy):
    if not isinstance(values,dict) or not set(values)<=set(FIELDS)|{'family'}:
        raise ValueError('Unknown browse classification field')
    for key,value in values.items():
        if key=='family':
            if value not in taxonomy['families']:raise ValueError('Unknown collection family: '+str(value))
        elif not isinstance(value,list) or not value or len(value)!=len(set(value)) or any(v not in taxonomy['dimensions'][key]['values'] for v in value):
            raise ValueError('Unknown or duplicate browse value: '+key+' '+str(value))


def classify(asset,collection,taxonomy):
    """Explicit asset metadata > collection defaults > existing-source migration rules."""
    raw={}
    for rule in taxonomy['rules']:
        if 'packs' in rule and not any(asset['pack'].startswith(v) for v in rule['packs']):continue
        if 'domain' in rule and asset.get('domain') not in rule['domain']:continue
        if 'subjects' in rule and not any(s==v or s.startswith(v+'.') for s in asset.get('subjects',[]) for v in rule['subjects']):continue
        for k,v in rule['set'].items():raw.setdefault(k,v)
    for source in (collection,asset.get('classification',{})):
        validate_values(source,taxonomy);raw.update(source)
    raw.setdefault('category_path',['other'])
    raw.setdefault('perspective',['unknown'])
    raw.setdefault('theme',['unknown'])
    # Current catalog formats are raster PNG regions or composites of them.
    raw.setdefault('medium',['raster-2d'])
    paths=set()
    for leaf in raw['category_path']:
        parts=leaf.split('.')
        paths.update('.'.join(parts[:i]) for i in range(1,len(parts)+1))
    return {**raw,'category_path':sorted(paths)}


def project_browse(assets,packs,defaults,taxonomy):
    for asset in assets:
        asset.update(classify(asset,defaults.get(asset['pack'],{}),taxonomy))
    by_pack={}
    for a in assets:by_pack.setdefault(a['pack'],[]).append(a)
    for pack in packs:
        members=by_pack.get(pack['id'],[])
        listed=[a for a in members if a.get('discovery','standalone')=='standalone']
        pack['asset_count']=len(members)
        pack['listed_count']=len(listed)
        pack['categories']=sorted({v for a in listed for v in a['category_path']})
        families={a.get('family') for a in members}
        if len(families)==1 and None not in families:pack['family']=next(iter(families))
    # Only the vocabulary is exported, not migration rules.
    return {k:taxonomy[k] for k in ('schema','dimensions','families')}
