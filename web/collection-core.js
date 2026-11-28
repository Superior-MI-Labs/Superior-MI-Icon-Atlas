"use strict";
/* Pure, reusable multi-manifest collection resolver: no DOM, ZIP, or network APIs. */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.VisualAtlasCollections=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  const MAX_PACKS=96,MAX_ASSETS=12000,MAX_TEXTURES=512;
  function safePath(path){return typeof path==='string'&&path.length>0&&path.length<512&&!path.startsWith('/')&&!path.includes('\\')&&!path.includes(':')&&!path.includes('\0')&&!path.split('/').some(s=>!s||s==='.'||s==='..');}
  function parent(path){const i=path.lastIndexOf('/');return i<0?'':path.slice(0,i);}
  function join(base,path){if(!safePath(path))throw Error('Unsafe texture path: '+path);const out=base?base+'/'+path:path;if(!safePath(out))throw Error('Unsafe resolved path: '+out);return out;}
  // Concept data is descriptive, separate from visual rendering and stat simulation.
  const conceptId=v=>typeof v==='string'&&/^[a-z][a-z0-9_.-]{0,127}$/.test(v);
  const ruleId=v=>typeof v==='string'&&/^[a-z][a-z0-9_.-]{0,119}\/[1-9][0-9]{0,5}$/.test(v);
  const unitId=v=>typeof v==='string'&&/^[a-z][a-z0-9_.-]{0,63}$/.test(v);
  const record=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
  const only=(v,keys)=>record(v)&&Object.keys(v).every(k=>keys.includes(k));
  const bounded=(v,min,max)=>Number.isFinite(v)&&v>=min&&v<=max;
  const shortString=(v,max)=>typeof v==='string'&&v.length>0&&v.length<=max;
  function validValue(v){
    if(v?.kind==='quantity')return only(v,['kind','value','unit'])&&bounded(v.value,-1e9,1e9)&&unitId(v.unit);
    if(v?.kind==='dice')return only(v,['kind','count','sides','modifier','unit'])&&Number.isInteger(v.count)&&bounded(v.count,1,100)&&Number.isInteger(v.sides)&&bounded(v.sides,2,1000)&&Number.isInteger(v.modifier)&&bounded(v.modifier,-1000000,1000000)&&unitId(v.unit);
    if(v?.kind==='proportion')return only(v,['kind','fraction','basis','rounding','unit','cap'])&&bounded(v.fraction,0,10)&&conceptId(v.basis)&&['none','floor','ceil','nearest'].includes(v.rounding)&&unitId(v.unit)&&(v.cap===undefined||bounded(v.cap,0,1e9));
    if(v?.kind==='boolean')return only(v,['kind','value'])&&typeof v.value==='boolean';
    return false;
  }
  function validMap(v,allowEmpty=false){
    return record(v)&&Object.keys(v).length<129&&(allowEmpty||Object.keys(v).length>0)&&Object.entries(v).every(([k,x])=>conceptId(k)&&validValue(x));
  }
  function validateConcepts(items,assets=null){
    if(items===undefined)return;
    if(!Array.isArray(items)||items.length>3000)throw Error('Invalid concept collection');
    const ids=new Set(),linked=assets===null?null:new Set(assets.map(a=>a.concept_id));
    for(const item of items){
      if(!only(item,['schema','id','name','description','license','physical','defaults'])||item.schema!=='smi-concept/1'||!conceptId(item.id)||!shortString(item.name,160)||!shortString(item.license,128)||ids.has(item.id))throw Error('Invalid or duplicate concept '+item?.id);
      if(item.description!==undefined&&(typeof item.description!=='string'||item.description.length>4000))throw Error('Invalid concept description '+item.id);
      if(item.physical!==undefined&&(!only(item.physical,['width_m','depth_m','height_m','mass_kg','capacity_l'])||!Object.keys(item.physical).length||Object.values(item.physical).some(v=>!bounded(v,0,1e9)||v===0)))throw Error('Invalid physical properties '+item.id);
      if(item.defaults!==undefined&&(!record(item.defaults)||!Object.keys(item.defaults).length||Object.keys(item.defaults).length>32||Object.entries(item.defaults).some(([k,v])=>!ruleId(k)||!validMap(v))))throw Error('Invalid ruleset defaults '+item.id);
      if(linked&&!linked.has(item.id))throw Error('Unreferenced concept '+item.id);
      ids.add(item.id);
    }
  }
  // Resolve explicitly chosen profiles; conflicting definitions must not silently
  // stack. Overrides are separate from immutable authored defaults.
  function resolveDefaults(concept,rulesets=[],overrides={}){
    validateConcepts([concept]);
    if(!Array.isArray(rulesets)||rulesets.length>32||new Set(rulesets).size!==rulesets.length||!validMap(overrides,true))throw Error('Invalid ruleset selection or overrides');
    const result=new Map();
    for(const id of rulesets){
      if(!ruleId(id)||!Object.hasOwn(concept.defaults||{},id))throw Error('Unknown ruleset '+id);
      for(const [key,value] of Object.entries(concept.defaults[id])){
        if(result.has(key)&&!equivalent(result.get(key),value))throw Error('Conflicting ruleset default '+key);
        result.set(key,value);
      }
    }
    for(const [key,value] of Object.entries(overrides)){
      if(!result.has(key))throw Error('Unknown override '+key);
      const previous=result.get(key);
      if(previous.unit!==value.unit||(previous.kind==='boolean')!==(value.kind==='boolean'))throw Error('Incompatible override '+key);
      result.set(key,value);
    }
    return structuredClone(Object.fromEntries(result));
  }
  // Versioned property vocabulary and source planning; never evaluate damage,
  // roll randomness, tick clocks or mutate instances in the content resolver.
  const kinds=['quantity','dice','proportion','boolean'];
  const boundedRecord=(v,max)=>record(v)&&Object.keys(v).length<=max;
  const own=(v,k)=>Object.hasOwn(v,k);
  const distinctKinds=v=>Array.isArray(v)&&v.length>0&&v.length<=kinds.length&&new Set(v).size===v.length&&v.every(k=>kinds.includes(k));
  function validateRuleRegistry(registry){
    if(!only(registry,['schema','id','properties','modules','bases'])||registry.schema!=='smi-ruleset-registry/1'||!ruleId(registry.id)||!boundedRecord(registry.properties,512)||!boundedRecord(registry.modules,128)||!boundedRecord(registry.bases,128))throw Error('Invalid ruleset registry');
    for(const [key,p] of Object.entries(registry.properties)){
      if(!conceptId(key)||!only(p,['unit','kinds','operation','min','max','integer'])||!distinctKinds(p.kinds)||!['base','add','multiply','policy'].includes(p.operation)||
        (p.kinds.includes('boolean')?(p.kinds.length!==1||p.unit!==undefined||p.operation!=='policy'||p.min!==undefined||p.max!==undefined||p.integer!==undefined):(!unitId(p.unit)||p.operation==='policy'))||
        (p.operation==='multiply'&&(p.unit!=='ratio'||p.kinds.some(k=>k!=='quantity')||!(p.min>=0)))||
        (p.min!==undefined&&!bounded(p.min,-1e9,1e9))||(p.max!==undefined&&!bounded(p.max,-1e9,1e9))||(p.min!==undefined&&p.max!==undefined&&p.min>p.max)||(p.integer!==undefined&&typeof p.integer!=='boolean'))throw Error('Invalid property contract '+key);
    }
    for(const [key,unit] of Object.entries(registry.bases))if(!conceptId(key)||!unitId(unit))throw Error('Invalid proportion basis '+key);
    for(const [id,module] of Object.entries(registry.modules)){
      if(!ruleId(id)||!boundedRecord(module,128)||!Object.keys(module).length)throw Error('Invalid module '+id);
      for(const [key,allowed] of Object.entries(module))if(!own(registry.properties,key)||!distinctKinds(allowed)||allowed.some(k=>!registry.properties[key].kinds.includes(k)))throw Error('Invalid module property '+id+'/'+key);
    }
  }
  function checkRegisteredValue(registry,key,value,allowed){
    if(!own(registry.properties,key)||!validValue(value))throw Error('Unknown or invalid property '+key);
    const p=registry.properties[key];
    if(!(allowed||p.kinds).includes(value.kind)||value.unit!==p.unit)throw Error('Incompatible type/unit '+key);
    if(value.kind==='proportion'&&(!own(registry.bases,value.basis)||registry.bases[value.basis]!==value.unit))throw Error('Incompatible proportion basis '+key);
    const range=(v)=>v>=(p.min??-1e9)&&v<=(p.max??1e9);
    if(value.kind==='quantity'&&(!range(value.value)||(p.integer&&!Number.isInteger(value.value))))throw Error('Property out of range '+key);
    if(value.kind==='dice'&&(!range(value.count+value.modifier)||!range(value.count*value.sides+value.modifier)))throw Error('Dice outcomes out of range '+key);
    if(value.kind==='proportion'&&((p.integer&&value.rounding==='none')||(value.cap!==undefined&&(!range(value.cap)||(p.integer&&!Number.isInteger(value.cap))))))throw Error('Invalid proportion cap/rounding '+key);
  }
  // One candidate per source/module/property. Explicit selection or override
  // resolves collisions; even equal values keep distinct source provenance.
  // Modifier properties are returned as data, not automatically applied.
  function resolveContributors(registry,contributors,rulesets=[],selections={},overrides={}){
    validateRuleRegistry(registry);
    if(!Array.isArray(contributors)||contributors.length>128||!Array.isArray(rulesets)||rulesets.length>32||new Set(rulesets).size!==rulesets.length||!boundedRecord(selections,128)||!validMap(overrides,true))throw Error('Invalid contributor resolution request');
    for(const id of rulesets)if(!ruleId(id)||!own(registry.modules,id))throw Error('Unknown ruleset '+id);
    const sources=new Set(),usedModules=new Set(),candidates=new Map();
    for(const source of contributors){
      if(!only(source,['id','role','concept','archive_sha256'])||!conceptId(source.id)||!conceptId(source.role)||sources.has(source.id)||(source.archive_sha256!==undefined&&(typeof source.archive_sha256!=='string'||!/^[a-f0-9]{64}$/.test(source.archive_sha256))))throw Error('Invalid or duplicate contributor '+source?.id);
      sources.add(source.id);validateConcepts([source.concept]);
      for(const id of rulesets){
        const profile=source.concept.defaults?.[id];if(!profile)continue;
        usedModules.add(id);
        for(const [key,value] of Object.entries(profile)){
          const module=registry.modules[id];
          if(!own(module,key))throw Error('Unsupported module property '+id+'/'+key);
          checkRegisteredValue(registry,key,value,module[key]);
          if(!candidates.has(key))candidates.set(key,[]);
          candidates.get(key).push({source:source.id,role:source.role,concept:source.concept.id,module:id,...(source.archive_sha256?{archive_sha256:source.archive_sha256}:{}),value});
        }
      }
    }
    if(candidates.size>128)throw Error('Too many resolved properties');
    for(const [key,selection] of Object.entries(selections)){
      if(!candidates.has(key)||!only(selection,['source','module'])||!conceptId(selection.source)||!ruleId(selection.module)||!candidates.get(key).some(x=>x.source===selection.source&&x.module===selection.module)||own(overrides,key))throw Error('Invalid or conflicting source selection '+key);
    }
    for(const [key,value] of Object.entries(overrides)){
      if(!candidates.has(key))throw Error('Unknown override '+key);
      checkRegisteredValue(registry,key,value);
    }
    const conflicts=[],resolved=[];
    for(const key of [...candidates.keys()].sort()){
      const options=candidates.get(key).sort((a,b)=>a.source<b.source?-1:a.source>b.source?1:a.module<b.module?-1:a.module>b.module?1:0);
      const selection=own(selections,key)?selections[key]:undefined;
      const chosen=selection?options.find(x=>x.source===selection.source&&x.module===selection.module):options.length===1?options[0]:null;
      if(own(overrides,key))resolved.push({key,operation:registry.properties[key].operation,value:overrides[key],origin:{role:'application_override'}});
      else if(chosen){const {value,...origin}=chosen;resolved.push({key,operation:registry.properties[key].operation,value,origin});}
      else conflicts.push(key);
    }
    // No partially resolved plan is returned on ambiguity.
    return structuredClone({ok:conflicts.length===0,conflicts,values:conflicts.length?null:Object.fromEntries(resolved.map(({key,...v})=>[key,v])),candidates:Object.fromEntries([...candidates.entries()].sort(([a],[b])=>a<b?-1:a>b?1:0)),unusedModules:rulesets.filter(id=>!usedModules.has(id)).sort()});
  }
  function resolveCollection(index,definitions,fallbackName='Imported collection'){
    // definitions: [{path,pack}] where every path is archive-relative and distinct.
    if(!Array.isArray(definitions)||!definitions.length||definitions.length>MAX_PACKS)throw Error('Collection must contain 1–'+MAX_PACKS+' pack manifests');
    const manifests=new Map();
    for(const {path,pack} of definitions){
      if(!safePath(path)||manifests.has(path))throw Error('Duplicate or unsafe manifest path: '+path);
      if(!pack||pack.schema!=='smi-visual-pack/1'||typeof pack.pack_id!=='string'||!pack.pack_id||!Array.isArray(pack.assets)||!pack.assets.length||typeof pack.textures!=='object'||!pack.textures||Array.isArray(pack.textures))throw Error('Invalid visual pack at '+path);
      if(pack.assets.length>3000||Object.keys(pack.textures).length>200)throw Error('Pack too large: '+path);
      manifests.set(path,pack);
    }
    let groups;
    if(index!==null&&index!==undefined){
      if(index.schema!=='smi-visual-collection/1'||typeof index.collection_id!=='string'||!index.collection_id||!Array.isArray(index.packs)||!index.packs.length||index.packs.length>MAX_PACKS)throw Error('Invalid smi-visual-collection/1 root index');
      const used=new Set();
      groups=index.packs.map(item=>{
        if(!item||typeof item.manifest!=='string'||!manifests.has(item.manifest)||used.has(item.manifest))throw Error('Collection references missing or duplicate manifest '+item?.manifest);
        used.add(item.manifest);
        return {path:item.manifest,label:typeof item.label==='string'&&item.label.trim()?item.label:manifests.get(item.manifest).pack_id,category:typeof item.category==='string'?item.category:''};
      });
      if(used.size!==manifests.size)throw Error('Collection index does not list all pack manifests');
    }else{
      groups=[...manifests.keys()].sort().map(path=>({path,label:manifests.get(path).pack_id,category:''}));
    }
    const assets=[],textures={},interfaces={},previewProfiles=[],profileIds=new Set(),statProfiles=[],statIds=new Set(),concepts=[],conceptIds=new Set(),assetIds=new Set(),packIds=new Set(),texturePaths=new Set(),groupInfo=[];
    const licenseSet=new Set();
    for(let n=0;n<groups.length;n++){
      const group=groups[n],pack=manifests.get(group.path),prefix='p'+n+'_';
      if(packIds.has(pack.pack_id))throw Error('Duplicate pack_id within ZIP: '+pack.pack_id);
      packIds.add(pack.pack_id);
      licenseSet.add(pack.license||'UNSPECIFIED');
      validateConcepts(pack.concepts);
      for(const item of pack.concepts||[]){
        if(conceptIds.has(item.id))throw Error('Duplicate concept '+item.id);
        conceptIds.add(item.id);concepts.push(structuredClone(item));licenseSet.add(item.license);
      }
      for(const profile of pack.preview_profiles||[]){
        if(profileIds.has(profile.id))throw Error('Duplicate preview profile '+profile.id);
        profileIds.add(profile.id);previewProfiles.push(structuredClone(profile));
      }
      for(const profile of pack.stat_profiles||[]){
        if(statIds.has(profile.id))throw Error('Duplicate stat profile '+profile.id);
        statIds.add(profile.id);statProfiles.push(structuredClone(profile));
      }
      for(const [id,def] of Object.entries(pack.interfaces||{})){
        if(Object.hasOwn(interfaces,id)&&!equivalent(interfaces[id],def))throw Error('Conflicting interface contract '+id);
        interfaces[id]=structuredClone(def);
      }
      const groupIds=[];
      for(const [key,texture] of Object.entries(pack.textures)){
        if(!texture||typeof texture.path!=='string')throw Error('Invalid texture '+key+' in '+group.path);
        const file=join(parent(group.path),texture.path);
        const uniqueKey=prefix+key;
        // Different packs can intentionally reuse the same image. Metadata is not merged implicitly.
        textures[uniqueKey]={...texture,path:file};
        texturePaths.add(file);
      }
      for(const source of pack.assets){
        if(!source||typeof source.id!=='string'||!source.id||assetIds.has(source.id))throw Error('Duplicate or invalid asset ID: '+source?.id);
        assetIds.add(source.id);
        const a={...source};
        if(a.kind==='region'){
          if(typeof a.texture!=='string'||!Object.hasOwn(pack.textures,a.texture))throw Error('Missing texture declaration for '+a.id);
          a.texture=prefix+a.texture;
        }
        a.sourcePack=pack.pack_id;
        a.sourceGroup=group.path;
        a.sourceLabel=group.label;
        a.license=a.license||pack.license||'UNSPECIFIED';
        assets.push(a);groupIds.push(a.id);
      }
      groupInfo.push({...group,pack_id:pack.pack_id,ids:groupIds});
    }
    if(assets.length>MAX_ASSETS||Object.keys(textures).length>MAX_TEXTURES)throw Error('Collection exceeds asset or texture limit');
    // Legacy concept_id links may remain unresolved; authored definitions may not be orphaned.
    const linked=new Set(assets.map(a=>a.concept_id));
    for(const item of concepts)if(!linked.has(item.id))throw Error('Unreferenced concept '+item.id);
    const exists=id=>assetIds.has(id);
    for(const profile of previewProfiles)if(!exists(profile.asset))throw Error('Unknown preview profile asset '+profile.asset);
    for(const profile of statProfiles)if(!exists(profile.asset))throw Error('Unknown stat profile asset '+profile.asset);
    for(const a of assets){
      const refs=a.kind==='sequence'? (a.frames||[]).map(f=>f.asset):a.kind==='state_set'?Object.values(a.states||{}):a.kind==='composition'?[...(a.layers||[]).filter(l=>l.asset).map(l=>l.asset),...Object.values(a.slots||{}).flatMap(s=>s.options||[])]:[];
      for(const ref of [...refs,...(Array.isArray(a.spatial?.views?.assets)?a.spatial.views.assets:[])])if(!exists(ref))throw Error('Unknown collection reference '+ref+' from '+a.id);
    }
    const entry=(index&&typeof index.entry_asset==='string'&&index.entry_asset)||assets.find(a=>a.kind==='composition')?.id||assets.find(a=>a.kind==='state_set')?.id||assets.find(a=>a.kind==='sequence')?.id||assets[0].id;
    if(!exists(entry))throw Error('Unknown collection entry_asset '+entry);
    const name=(index&&typeof index.name==='string'&&index.name.trim()&&index.name)||fallbackName;
    const collectionId=index?.collection_id||'smi.local.'+String(fallbackName).replace(/[^a-zA-Z0-9.-]/g,'-');
    return {
      pack:{schema:'smi-visual-pack/1',pack_id:collectionId,version:index?.version||'1.0.0',description:'Resolved collection: '+name,license:licenseSet.size===1?[...licenseSet][0]:'MIXED',interfaces,preview_profiles:previewProfiles,stat_profiles:statProfiles,...(concepts.length?{concepts}:{}),textures,assets},
      bag:{id:collectionId,name,version:index?.version||'1.0.0',description:index?.description||'',entry,groups:groupInfo,assetIds:[...assetIds],textureCount:texturePaths.size}
    };
  }
  // A single deterministic dependency traversal for public export, private export,
  // and package QA. Dependency extraction is injected from the canonical slot core.
  function dependencyClosure(roots,getAsset,refs,existing=new Set()){
    const closure=new Set(existing),active=new Set();
    function walk(id){
      if(active.has(id))throw Error('Cyclic asset dependency: '+id);
      if(closure.has(id))return;
      const asset=getAsset(id);
      if(!asset)throw Error('Missing asset dependency: '+id);
      active.add(id);closure.add(id);
      for(const ref of refs(asset))walk(ref);
      active.delete(id);
    }
    for(const id of roots)walk(id);
    return closure;
  }
  // Compare authored meaning, independent of ZIP path, object key order, and bag ownership.
  function canonical(value){
    if(Array.isArray(value))return value.map(canonical);
    if(value&&typeof value==='object')return Object.fromEntries(Object.keys(value).sort().filter(k=>value[k]!==undefined).map(k=>[k,canonical(value[k])]));
    return value;
  }
  const equivalent=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
  function authoredAsset(asset){
    const copy={...asset};
    for(const key of ['pack','source','sourcePack','sourceGroup','sourceLabel','ownerBag','texture'])delete copy[key];
    return copy;
  }
  function sameAsset(a,b,interfacesA,interfacesB){
    if(!equivalent(authoredAsset(a),authoredAsset(b)))return false;
    const refs=[...(a.implements||[]),...Object.values(a.slots||{}).map(s=>s.accepts)];
    return refs.every(id=>Object.hasOwn(interfacesA||{},id)&&Object.hasOwn(interfacesB||{},id)&&equivalent(interfacesA[id],interfacesB[id]));
  }
  async function sameBytes(a,b){
    if(!a||!b||a.size!==b.size)return false;
    if(a===b)return true;
    const [left,right]=await Promise.all([a.arrayBuffer(),b.arrayBuffer()]);
    const x=new Uint8Array(left),y=new Uint8Array(right);
    return x.every((v,i)=>v===y[i]);
  }
  // Selection state belongs to the host. The portable archive contract is shared.
  async function writeSelection(zip,{assets,rootId,packId,version='1.0.0',getTexture,getInterfaces,previewProfiles=[],statProfiles=[],concepts=[],licenseText=null,sourceNotices=[],maxEntry=24*1024*1024}){
    if(!assets.some(a=>a.id===rootId))throw Error('Missing export root '+rootId);
    const ids=new Set(assets.map(a=>a.id)),textures={},mapping=new Map(),interfaces={};
    const chosen=assets.map(a=>structuredClone(a));
    for(const a of chosen){
      if(a.kind==='region'){
        if(!mapping.has(a.texture)){
          const t=await getTexture(a.texture);
          if(!t?.blob||!Number.isInteger(t.width_px)||!Number.isInteger(t.height_px)||t.width_px<1||t.height_px<1||t.blob.size>maxEntry)throw Error('Invalid or oversized texture '+a.texture);
          const id='t'+(mapping.size+1),ext=t.path?.match(/\.(png|jpe?g|webp|gif)$/i)?.[0].toLowerCase()||'.png';
          const path='textures/'+id+ext;
          mapping.set(a.texture,id);textures[id]={path,width_px:t.width_px,height_px:t.height_px};zip.file(path,t.blob);
        }
        a.texture=mapping.get(a.texture);
      }
      for(const ref of [...(a.implements||[]),...Object.values(a.slots||{}).map(s=>s.accepts)]){
        const def=getInterfaces(a)?.[ref];
        if(!def)throw Error('Missing interface '+ref+' for '+a.id);
        if(Object.hasOwn(interfaces,ref)&&!equivalent(interfaces[ref],def))throw Error('Conflicting interface '+ref);
        interfaces[ref]=def;
      }
      for(const key of ['pack','source','sourcePack','sourceGroup','sourceLabel','ownerBag','review_status'])delete a[key];
    }
    const profiles=items=>items.filter(p=>ids.has(p.asset)).map(p=>{const copy=structuredClone(p);delete copy.ownerBag;return copy;});
    const previews=profiles(previewProfiles),stats=profiles(statProfiles);
    const conceptLinks=new Set(chosen.map(a=>a.concept_id));
    const definitions=concepts.filter(item=>conceptLinks.has(item.id)).map(item=>{const copy=structuredClone(item);delete copy.ownerBag;return copy;});
    validateConcepts(definitions,chosen);
    const licenses=new Set([...chosen.map(a=>a.license||'UNSPECIFIED'),...definitions.map(item=>item.license)]);
    const manifest={schema:'smi-visual-pack/1',pack_id:packId,version,description:'Portable asset: '+rootId,
      license:licenses.size===1?[...licenses][0]:'MIXED',interfaces,textures,assets:chosen,
      ...(previews.length?{preview_profiles:previews}:{}),...(stats.length?{stat_profiles:stats}:{}),...(definitions.length?{concepts:definitions}:{})};
    zip.file('manifest.json',JSON.stringify(manifest,null,2)+'\n');
    zip.file('collection.json',JSON.stringify({schema:'smi-visual-collection/1',collection_id:packId,name:chosen.find(a=>a.id===rootId).name||rootId,version,entry_asset:rootId,packs:[{manifest:'manifest.json'}]},null,2)+'\n');
    // Preserve original notice bytes, namespaced by source; never silently
    // turn a mixed or restricted license into an unrestricted grant.
    let noticeIndex=0;
    for(const notice of sourceNotices){
      if(!safePath(notice.path)||!notice.blob||notice.blob.size>maxEntry)throw Error('Invalid source notice');
      zip.file('LICENSES/source-'+(++noticeIndex)+'/'+notice.path,notice.blob);
    }
    zip.file('SOURCE-NOTICES.txt','Root asset: '+rootId+'\n\nPer-asset licenses:\n'+chosen.map(a=>a.id+' : '+(a.license||'UNSPECIFIED')).join('\n')+'\n\nConcept licenses:\n'+definitions.map(item=>item.id+' : '+item.license).join('\n')+'\nPreserve source rights and notices. Unknown license is not equivalent to CC0.\n');
    if(licenseText&&licenses.has('Apache-2.0')){const notice=await licenseText();if(notice)zip.file('LICENSES/Apache-2.0.txt',notice);}
    return manifest;
  }
  return Object.freeze({safePath,join,resolveCollection,dependencyClosure,writeSelection,equivalent,sameAsset,sameBytes,validateConcepts,resolveDefaults,validateRuleRegistry,resolveContributors,MAX_PACKS,MAX_ASSETS,MAX_TEXTURES});
});
