#!/usr/bin/env python3
"""Read-only asset and metadata QA; reports duplicates and unreviewed backlog."""
import hashlib,json,collections,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from atlasctl import load,validate

def audit():
    m=load();checks=validate(deep=True)
    byhash=collections.defaultdict(list)
    for path in ROOT.rglob('*'):
        if not path.is_file() or '.git' in path.parts or 'site' in path.parts:continue
        if path.suffix.lower() not in ('.png','.json','.svg'):continue
        byhash[hashlib.sha256(path.read_bytes()).hexdigest()].append(str(path.relative_to(ROOT)))
    duplicates=[paths for paths in byhash.values() if len(paths)>1]
    bystatus=collections.Counter(i['review_status'] for i in m['icons'])
    bydomain=collections.Counter(i['domain'] for i in m['icons'])
    names=[str(p.relative_to(ROOT)) for p in ROOT.rglob('foreground-mask.png')]
    report={'schema':'smi-icon-atlas-audit/1','total_icons':len(m['icons']),'sheets':len(m['sheets']),
            'root_manifest_bytes':(ROOT/'manifest.json').stat().st_size,
            'review_status':dict(bystatus),'domains':dict(bydomain),
            'duplicate_files':duplicates,'leftover_mask_files':names,
            'validation_errors':checks,'preview_images':'inspection-preview.png files retained as explicit review artifacts, not published with the site',
            'source_images':'source-images retained for provenance and future independent art review'}
    return report
if __name__=='__main__':
    report=audit()
    print(json.dumps(report,indent=2))
    sys.exit(bool(report['validation_errors'] or report['leftover_mask_files']))
