"""Derived, bounded previews of ordinary region crops, never runtime textures."""
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
from pathlib import PurePosixPath

MAX_SIZE=(200,124)


def eligible(asset):
    return (asset.get('kind')=='region' and asset.get('discovery','standalone')!='hidden'
            and not asset.get('trim_offset_px') and not asset.get('nine_slice_px')
            and asset.get('logical_size_px',asset['rect_px'][2:])==asset['rect_px'][2:])


def build_region_previews(archive,index,packs,authored_ids,dest):
    """Read the exact generated ZIP; complex geometry stays with the shared renderer."""
    try:
        from PIL import Image
    except ImportError:
        return {}  # stdlib-only local site builds retain the live preview fallback
    result={}
    folder=dest/'previews'
    folder.mkdir(exist_ok=True)
    for ref,pack in zip(index['packs'],packs):
        by_texture=defaultdict(list)
        for asset in pack['assets']:
            if asset['id'] in authored_ids and eligible(asset):
                by_texture[asset['texture']].append(asset)
        for key,assets in by_texture.items():
            path=PurePosixPath(ref['manifest']).parent/pack['textures'][key]['path']
            with Image.open(BytesIO(archive.read(path.as_posix()))) as source:
                rgba=source.convert('RGBA')
                for asset in assets:
                    x,y,w,h=asset['rect_px']
                    if min(x,y)<0 or min(w,h)<1 or x+w>rgba.width or y+h>rgba.height:
                        raise ValueError('Invalid preview crop: '+asset['id'])
                    thumb=rgba.crop((x,y,x+w,y+h))
                    thumb.thumbnail(MAX_SIZE,Image.Resampling.LANCZOS)
                    buf=BytesIO()
                    thumb.save(buf,format='PNG')
                    data=buf.getvalue()
                    name=sha256(data).hexdigest()+'.png'
                    file=folder/name
                    if not file.exists():file.write_bytes(data)
                    result[asset['id']]='previews/'+name
    return result
