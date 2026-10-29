#!/usr/bin/env python3
"""Curate visual meaning in the one owning per-sheet manifest. Never change icon geometry."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from atlasctl import tokens


def review(ident,name,tags,subjects=(),aliases=(),concept=None,evidence='human-visual-review'):
    if not name.strip():raise ValueError('Nonempty reviewed icon name required')
    tags=list(dict.fromkeys(t.strip().casefold() for t in tags if t.strip()))
    if not tags:raise ValueError('At least one meaningful tag required')
    manifest=json.loads((ROOT/'manifest.json').read_text())
    for ref in manifest['sheets']:
        src=ROOT/ref['manifest']
        document=json.loads(src.read_text())
        for icon in document['icons']:
            if icon['id']!=ident:continue
            icon['review']={
                'status':'reviewed', 'art_status':'candidate','name':name.strip(),
                'tags':tags,'aliases':list(dict.fromkeys(a.strip() for a in aliases if a.strip())),
                'subjects':list(dict.fromkeys(s.strip() for s in subjects if s.strip())),
                'concept_id':concept,'evidence':evidence,
            }
            src.write_text(json.dumps(document,indent=2,ensure_ascii=False)+'\n')
            return ref['manifest']
    raise ValueError('Unknown icon ID: '+ident)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('id');p.add_argument('--name',required=True)
    p.add_argument('--tags',required=True,help='Comma-separated visual tags')
    p.add_argument('--subjects',default='',help='Comma-separated hierarchy facets')
    p.add_argument('--aliases',default='')
    p.add_argument('--concept')
    p.add_argument('--evidence',default='human-visual-review')
    a=p.parse_args()
    def split(s):return [x.strip() for x in s.split(',') if x.strip()]
    print(review(a.id,a.name,split(a.tags),split(a.subjects),split(a.aliases),a.concept,a.evidence))

if __name__=='__main__':
    try:main()
    except ValueError as e:print(e,file=sys.stderr);sys.exit(1)
