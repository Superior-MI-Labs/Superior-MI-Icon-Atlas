"""Derived, read-only asset inventory. Source manifests and publications.json remain canonical."""
from pathlib import Path
from collections import Counter, defaultdict
import json

REVIEWS={"pending","reviewed"}

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
    for folder in sorted((root/"examples").glob("*")):
        file=folder/"manifest.json"
        if not file.is_file():continue
        key=folder.relative_to(root).as_posix()
        try:pack=json.loads(file.read_text())
        except (ValueError,OSError) as ex:errors.append(key+": unreadable manifest "+str(ex));continue
        if pack.get("schema")!="smi-visual-pack/1":errors.append(key+": invalid manifest");continue
        items=pack.get("assets",[]);textures=pack.get("textures",{})
        if not isinstance(items,list) or not isinstance(textures,dict):
            errors.append(key+": invalid assets/textures");continue
        refs=set()
        for texture in textures.values():
            name=texture.get("path","");p=Path(name)
            if p.is_absolute() or ".." in p.parts or not (folder/p).is_file():
                errors.append(key+": unsafe/missing texture "+name)
            else:refs.add(p.as_posix())
        unreferenced=sorted(x.relative_to(folder).as_posix() for x in (folder/"textures").rglob("*")
            if x.is_file() and x.suffix.lower() in (".png",".webp",".jpg",".jpeg",".gif")
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
        if not (root/key/"manifest.json").is_file():errors.append(key+": published collection missing root manifest")
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
