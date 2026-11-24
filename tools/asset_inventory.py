"""Derived, read-only asset inventory. Source manifests and publications.json remain canonical."""
from pathlib import Path
from collections import Counter, defaultdict
import json

REVIEWS={"pending","reviewed"}

def source_collections(root):
    """A collection index or single root manifest defines a source directory."""
    return [folder for folder in sorted((Path(root)/"examples").iterdir())
            if folder.is_dir() and ((folder/"collection.json").is_file() or (folder/"manifest.json").is_file())]

def source_path(folder, relative):
    """Resolve archive-relative paths without traversal or symlink escapes."""
    if not isinstance(relative,str) or not relative or "\\" in relative or ":" in relative or any(p in ("", ".", "..") for p in relative.split("/")):
        raise ValueError("unsafe source path: "+str(relative))
    file=folder/relative
    if not file.resolve().is_relative_to(folder.resolve()) or not file.is_file():
        raise ValueError("unsafe/missing source file: "+relative)
    return file

def read_collection(folder):
    """Return the one authored index and its ordered, archive-relative manifests."""
    folder=Path(folder)
    index_file=folder/"collection.json"
    index=json.loads(index_file.read_text(encoding="utf-8")) if index_file.is_file() else None
    if index is not None:
        if index.get("schema")!="smi-visual-collection/1" or not isinstance(index.get("packs"),list) or not index["packs"]:
            raise ValueError("invalid collection index")
        names=[ref["manifest"] for ref in index["packs"]]
    else:
        names=["manifest.json"]
    if len(names)!=len(set(names)):raise ValueError("duplicate manifest path")
    packs=[]
    pack_ids=set()
    for name in names:
        file=source_path(folder,name)
        pack=json.loads(file.read_text(encoding="utf-8"))
        if pack.get("schema")!="smi-visual-pack/1" or not isinstance(pack.get("assets"),list) or not isinstance(pack.get("textures"),dict):
            raise ValueError("invalid manifest "+name)
        ident=pack.get("pack_id")
        if ident in pack_ids:raise ValueError("duplicate pack ID "+str(ident))
        pack_ids.add(ident)
        packs.append((file,pack))
    return index,packs

def runtime_files(folder,index,packs):
    """Exact archive payload, shared by inventory and deterministic ZIP build."""
    files={file for file,_ in packs}
    textures=set()
    if index is not None:files.add(source_path(folder,"collection.json"))
    for file,pack in packs:
        for texture in pack["textures"].values():
            target=source_path(file.parent,texture.get("path"))
            if not target.resolve().is_relative_to(folder.resolve()):
                raise ValueError("texture outside collection")
            textures.add(target)
        files.update(p for p in file.parent.glob("LICENSE*") if p.is_file())
        if (file.parent/"README.md").is_file():files.add(file.parent/"README.md")
    files.update(p for p in folder.glob("LICENSE*") if p.is_file())
    if (folder/"README.md").is_file():files.add(folder/"README.md")
    if any(not file.resolve().is_relative_to(folder.resolve()) for file in files):
        raise ValueError("runtime file outside collection")
    return files|textures,textures


def audit(root):
    root=Path(root);errors=[];warnings=[]
    policy=json.loads((root/"publications.json").read_text())
    if policy.get("schema")!="smi-publications/1":errors.append("Bad publication schema")
    pub={}
    for record in policy.get("collections",[]):
        key=record.get("path","");parts=Path(key)
        if parts.is_absolute() or ".." in parts.parts or len(parts.parts)!=2 or parts.parts[0]!="examples" or key in pub:
            errors.append("Invalid or duplicate publication path: "+key);continue
        if record.get("visual_qa") not in REVIEWS:errors.append("Missing explicit visual review for "+key)
        if not record.get("approval") or not record.get("rights"):errors.append("Missing release approval/rights for "+key)
        pub[key]=record
    groups=[];seen=defaultdict(list);reviews=Counter()
    for folder in source_collections(root):
        key=folder.relative_to(root).as_posix()
        try:
            index,packs=read_collection(folder)
            _,textures=runtime_files(folder,index,packs)
            items=[asset for _,pack in packs for asset in pack["assets"]]
        except (ValueError,OSError,KeyError,TypeError) as ex:
            errors.append(key+": "+str(ex));continue
        refs={file.relative_to(folder).as_posix() for file in textures}
        unreferenced=sorted(x.relative_to(folder).as_posix() for x in folder.rglob("*")
            if x.is_file() and "textures" in x.relative_to(folder).parts[:-1]
            and x.suffix.lower() in (".png",".webp",".jpg",".jpeg",".gif")
            and x.relative_to(folder).as_posix() not in refs)
        if unreferenced:warnings.append(key+": "+str(len(unreferenced))+" unreferenced texture(s)")
        record=pub.get(key)
        if record:
            if type(record.get("expected_assets")) is not int or record["expected_assets"]!=len(items):
                errors.append(key+": published asset count mismatch")
            reviews[record.get("visual_qa")]+=1
        for item in items:seen[item.get("id")].append(key)
        groups.append({"path":key,"published":bool(record),"visual_qa":record.get("visual_qa") if record else "unpublished",
            "assets":len(items),"textures":len(textures),"unreferenced_textures":unreferenced,
            "missing_names":sum(not a.get("name") for a in items),
            "missing_tags":sum(not a.get("tags") for a in items)})
    for key in pub:
        if key not in {group["path"] for group in groups}:errors.append(key+": published collection missing or invalid source")
    for key,owners in seen.items():
        if not isinstance(key,str) or not key:errors.append("Missing asset ID in "+str(owners))
        elif len(owners)>1:errors.append("Duplicate asset ID "+key+" in "+", ".join(owners))
    return {"schema":"smi-asset-inventory/1","summary":{
        "source_collections":len(groups),"published_collections":len(pub),
        "unpublished_collections":sum(not c["published"] for c in groups),
        "source_assets":sum(c["assets"] for c in groups),
        "published_assets":sum(c["assets"] for c in groups if c["published"]),
        "unreferenced_texture_files":sum(len(c["unreferenced_textures"]) for c in groups),
        "assets_missing_names":sum(c["missing_names"] for c in groups),
        "assets_missing_tags":sum(c["missing_tags"] for c in groups),
        "reviewed_collections":reviews["reviewed"],"published_pending_visual_review":reviews["pending"]
    },"collections":groups,"warnings":warnings,"errors":errors}

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument("--out",type=Path)
    args=ap.parse_args();report=audit(args.root);encoded=json.dumps(report,indent=2)+"\n"
    if args.out:args.out.parent.mkdir(exist_ok=True,parents=True);args.out.write_text(encoded)
    print(encoded,end="");raise SystemExit(bool(report["errors"]))
