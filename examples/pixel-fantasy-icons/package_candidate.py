#!/usr/bin/env python3
"""Build an importable local-only ZIP from authoritative manifest and texture files."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED,ZipInfo
from verify_pack import validate
R=Path(__file__).resolve().parent

def build(out=None):
    validate()
    out=Path(out or (R.parent/'SMI-Pixel-Fantasy-48-Builder-Review.zip'))
    with ZipFile(out,'w',ZIP_DEFLATED,compresslevel=9) as z:
        for path in [R/'manifest.json',R/'collection.json',*sorted((R/'textures').glob('*.png'))]:
            entry=ZipInfo(path.relative_to(R).as_posix(),date_time=(2020,1,1,0,0,0));entry.compress_type=ZIP_DEFLATED;entry.external_attr=0o644<<16
            z.writestr(entry,path.read_bytes())
    print('ZIP',out)
    return out
if __name__=='__main__':build()
