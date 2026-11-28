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
  // Optional visual and surface profiles. Region remains the renderable payload;
  // material channels never create an implicit dependency or an executable rule.
  function validateMaterialProfiles(asset,texture){
    const fail=()=>{throw Error('Invalid material/visual profile: '+asset.id);};
    const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
    const keys=(x,allowed)=>obj(x)&&Object.keys(x).every(k=>allowed.includes(k));
    const range=(x,a,b)=>typeof x==='number'&&Number.isFinite(x)&&x>=a&&x<=b;
    const strings=x=>Array.isArray(x)&&x.length<=128&&new Set(x).size===x.length&&x.every(v=>typeof v==='string'&&v.length>0&&v.length<=128);
    const text=(x,max)=>typeof x==='string'&&x.length>0&&x.length<=max;
    const p=asset.visual_profile,m=asset.material;
    if(p!==undefined){
      if(!keys(p,['schema','palette','palette_method','color_names'])||p.schema!=='smi-visual-profile/1'||!text(p.palette_method,64)||!strings(p.color_names)||!Array.isArray(p.palette)||p.palette.length<1||p.palette.length>16)fail();
      if(p.palette.some(c=>!keys(c,['hex','weight_bp'])||!/^#[0-9a-f]{6}$/.test(c.hex)||!Number.isInteger(c.weight_bp)||!range(c.weight_bp,0,10000))||p.palette.reduce((n,c)=>n+c.weight_bp,0)!==10000||new Set(p.palette.map(c=>c.hex)).size!==p.palette.length)fail();
    }
    if(m===undefined)return;
    if(asset.kind!=='region'||!texture||!keys(m,['schema','channels','role','repeat_intent','suggested_coverage_m','seam_screen','source','associations'])||m.schema!=='smi-surface-material/1'||!keys(m.channels,['base_color'])||m.channels.base_color!=='self'||!['surface','liquid_appearance','effect_appearance'].includes(m.role)||!Array.isArray(m.repeat_intent)||m.repeat_intent.length!==2||!m.repeat_intent.every(v=>['repeat','clamp','mirror'].includes(v)))fail();
    if(m.suggested_coverage_m!==undefined&&(!Array.isArray(m.suggested_coverage_m)||m.suggested_coverage_m.length!==2||!m.suggested_coverage_m.every(x=>range(x,1e-6,1e6))))fail();
    if(m.seam_screen!==undefined){const s=m.seam_screen;if(!keys(s,['method','x_mae','y_mae','x_ratio','y_ratio','screening'])||s.method!=='rgb-wrap-mae-v1'||!range(s.x_mae,0,1)||!range(s.y_mae,0,1)||!range(s.x_ratio,0,255)||!range(s.y_ratio,0,255)||!['low-discontinuity','review-required'].includes(s.screening))fail();}
    if(m.source!==undefined){const s=m.source;if(!keys(s,['filename','sha256','width_px','height_px','encoding','processing'])||!text(s.filename,512)||!/^[a-f0-9]{64}$/.test(s.sha256)||!Number.isInteger(s.width_px)||!range(s.width_px,1,8192)||!Number.isInteger(s.height_px)||!range(s.height_px,1,8192)||!text(s.encoding,64)||!text(s.processing,128))fail();}
    if(m.associations!==undefined){const s=m.associations;if(!keys(s,['environments','conditions'])||!strings(s.environments)||!strings(s.conditions))fail();}
    // Only whole, neutral, untrimmed regions are qualified for the initial role.
    if(asset.trim_offset_px||asset.nine_slice_px||!Array.isArray(asset.rect_px)||asset.rect_px.length!==4||asset.rect_px[0]!==0||asset.rect_px[1]!==0||asset.rect_px[2]!==texture.width_px||asset.rect_px[3]!==texture.height_px||asset.logical_size_px&&asset.logical_size_px.some((v,i)=>v!==asset.rect_px[i+2])||(texture.color_space!==undefined&&texture.color_space!=='srgb'))fail();
  }
  // Similarity is an optional discovery aid, never an asserted relationship,
  // automatic substitution, or permission to load another archive.
  function rankRelated(source,candidates,options={}){
    const {limit=8,categoryPrefixes=[],requiredRole=null,weights={semantic:0.65,color:0.25,style:0.10}}=options;
    if(!source||!Array.isArray(candidates)||!Number.isInteger(limit)||limit<1||limit>100||!Array.isArray(categoryPrefixes)||categoryPrefixes.some(x=>typeof x!=='string')||!['semantic','color','style'].every(k=>Number.isFinite(weights[k])&&weights[k]>=0)||weights.semantic+weights.color+weights.style<=0)throw Error('Invalid related-content query');
    const ignored=new Set('material surface texture base color tileable candidate painterly fantasy world environment raster 2d ground floor organic black white gray grey red orange yellow brown olive green teal blue purple pink'.split(' '));
    const tokens=a=>new Set([...(a.subjects||[]),...(a.tags||[]),...(a.aliases||[]),...(a.material?.associations?.environments||[]),...(a.material?.associations?.conditions||[])].flatMap(x=>String(x).toLowerCase().match(/[a-z0-9]+/g)||[]).filter(x=>x.length>2&&!ignored.has(x)));
    const lab=hex=>{const [r,g,b]=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);const l=Math.cbrt(.4122214708*r+.5363325363*g+.0514459929*b),m=Math.cbrt(.2119034982*r+.6806995451*g+.1073969566*b),s=Math.cbrt(.0883024619*r+.2817188376*g+.6299787005*b);return [.2104542553*l+.793617785*m-.0040720468*s,1.9779984951*l-2.428592205*m+.4505937099*s,.0259040371*l+.7827717662*m-.808675766*s];};
    const palette=a=>(a.visual_profile?.palette||[]).filter(c=>/^#[0-9a-f]{6}$/.test(c.hex)&&c.weight_bp>0).map(c=>({v:lab(c.hex),w:c.weight_bp/10000}));
    const cost=(a,b)=>a.reduce((n,x)=>n+x.w*Math.min(...b.map(y=>Math.hypot(...x.v.map((v,i)=>v-y.v[i])))),0);
    const t=tokens(source),p=palette(source),sum=weights.semantic+weights.color+weights.style;
    return candidates.filter(a=>a&&a.id!==source.id&&!a.legacy&&a.discovery!=='hidden'&&(!requiredRole||a.material?.role===requiredRole)&&(!categoryPrefixes.length||categoryPrefixes.some(prefix=>(a.category_path||a.classification?.category_path||[]).some(v=>v===prefix||v.startsWith(prefix+'.'))))).map(a=>{
      const v=tokens(a),shared=[...t].filter(k=>v.has(k)).sort(),semantic=shared.length/Math.max(1,new Set([...t,...v]).size),q=palette(a);
      const color=p.length&&q.length?Math.max(0,1-(cost(p,q)+cost(q,p))/.7):null,style=source.style&&a.style?Number(source.style===a.style):null;
      return {id:a.id,score:(semantic*weights.semantic+(color??0)*weights.color+(style??0)*weights.style)/sum,semantic,color,style,shared};
    }).filter(r=>r.shared.length>0||weights.semantic===0&&r.color!==null).sort((a,b)=>b.score-a.score||(a.id<b.id?-1:a.id>b.id?1:0)).slice(0,limit);
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
        validateMaterialProfiles(source,pack.textures[source.texture]);
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
        if(a.material)textures[a.texture].color_space='srgb';
        validateMaterialProfiles(a,textures[a.texture]);
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
  return Object.freeze({validateMaterialProfiles,rankRelated,safePath,join,resolveCollection,dependencyClosure,writeSelection,equivalent,sameAsset,sameBytes,validateConcepts,resolveDefaults,MAX_PACKS,MAX_ASSETS,MAX_TEXTURES});
});
