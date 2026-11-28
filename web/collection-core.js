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
  const relationKinds=['represented_by','compatible_with','requires','produces','transforms_into','unlocks','repairs','equips_to','applies_effect','triggers','harvested_from','uses_animation','uses_effect','uses_audio','contains'];
  const assetId=v=>typeof v==='string'&&v.length>0&&v.length<=256;
  const digestId=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
  function validRef(v){
    return only(v,['kind','id','archive_sha256'])&&['concept','asset'].includes(v.kind)&&(v.kind==='concept'?conceptId(v.id):assetId(v.id))&&(v.archive_sha256===undefined||digestId(v.archive_sha256));
  }
  const uniqueIds=(v,max)=>Array.isArray(v)&&v.length>0&&v.length<=max&&new Set(v).size===v.length&&v.every(conceptId);
  function validAxis(a){
    if(a?.kind==='enum')return only(a,['kind','values','default'])&&uniqueIds(a.values,32)&&(a.default===undefined||a.values.includes(a.default));
    if(a?.kind!=='ratio'||!only(a,['kind','current','maximum','bands'])||!conceptId(a.current)||!conceptId(a.maximum)||a.current===a.maximum||!Array.isArray(a.bands)||a.bands.length<1||a.bands.length>32)return false;
    let prev=-1;const seen=new Set();
    for(const band of a.bands){
      if(!only(band,['max','state'])||!bounded(band.max,0,1)||band.max<=prev||!conceptId(band.state)||seen.has(band.state))return false;
      prev=band.max;seen.add(band.state);
    }
    return prev===1;
  }
  const axisValues=a=>a.kind==='enum'?a.values:a.bands.map(b=>b.state);
  // Bounded action vocabulary. These are instructions for a host transaction,
  // not executable code, an inventory store, or an authorization decision.
  const roleId=v=>['actor','subject','target'].includes(v);
  const positiveCount=v=>Number.isInteger(v)&&bounded(v,1,1000000);
  const itemRef=v=>only(v,['id','archive_sha256'])&&conceptId(v.id)&&(v.archive_sha256===undefined||digestId(v.archive_sha256));
  const actionMagnitude=v=>validValue(v)&&v.kind!=='boolean'||only(v,['property'])&&conceptId(v.property);
  const actionGuard=v=>v===undefined||only(v,['property','equals'])&&conceptId(v.property)&&typeof v.equals==='boolean';
  const fixedMagnitude=v=>v.kind==='quantity'&&v.value>=0;
  const effectMagnitude=v=>v.kind==='quantity'?v.value>=0:v.kind==='dice'?v.count+v.modifier>=0:v.kind==='proportion';
  function validRequirement(r){
    if(!roleId(r?.owner))return false;
    switch(r.op){
      case 'inventory.has':return only(r,['op','owner','item','quantity'])&&itemRef(r.item)&&positiveCount(r.quantity);
      case 'state.is':return only(r,['op','owner','axis','value'])&&conceptId(r.axis)&&conceptId(r.value);
      case 'capability.has':return only(r,['op','owner','capability'])&&conceptId(r.capability);
      case 'stat.at_least':return only(r,['op','owner','stat','magnitude'])&&conceptId(r.stat)&&actionMagnitude(r.magnitude)&&(r.magnitude.property!==undefined||fixedMagnitude(r.magnitude));
      default:return false;
    }
  }
  function validOperation(r){
    if(!actionGuard(r?.when))return false;
    if(r?.op==='event.emit')return only(r,['op','event','when'])&&conceptId(r.event);
    if(!roleId(r?.owner))return false;
    switch(r.op){
      case 'inventory.consume':case 'inventory.produce':return only(r,['op','owner','item','quantity','when'])&&itemRef(r.item)&&positiveCount(r.quantity);
      case 'stat.consume':return only(r,['op','owner','stat','magnitude','when'])&&conceptId(r.stat)&&actionMagnitude(r.magnitude)&&(r.magnitude.property!==undefined||fixedMagnitude(r.magnitude)&&r.magnitude.value>0);
      case 'stat.change':return only(r,['op','owner','stat','direction','magnitude','when'])&&conceptId(r.stat)&&['increase','decrease'].includes(r.direction)&&actionMagnitude(r.magnitude)&&(r.magnitude.property!==undefined||effectMagnitude(r.magnitude));
      case 'state.set':return only(r,['op','owner','axis','value','when'])&&conceptId(r.axis)&&conceptId(r.value);
      default:return false;
    }
  }
  function validateActions(concept){
    if(concept.actions===undefined)return;
    if(!record(concept.actions)||!Object.keys(concept.actions).length||Object.keys(concept.actions).length>64)throw Error('Invalid concept actions '+concept.id);
    for(const [id,a] of Object.entries(concept.actions)){
      if(!conceptId(id)||!only(a,['description','kind','requirements','operations'])||!conceptId(a.kind)||(a.description!==undefined&&(typeof a.description!=='string'||a.description.length>1000))||(a.requirements!==undefined&&(!Array.isArray(a.requirements)||a.requirements.length>64||a.requirements.some(r=>!validRequirement(r))))||!Array.isArray(a.operations)||!a.operations.length||a.operations.length>64||a.operations.some(r=>!validOperation(r)))throw Error('Invalid concept action '+concept.id+'/'+id);
      // A subject cannot directly set its own derived axis. Other roles are
      // checked against their actual host instance contracts before commit.
      for(const o of a.operations)if(o.op==='state.set'&&o.owner==='subject'){
        const axis=concept.state_axes?.[o.axis];
        if(!axis||axis.kind!=='enum'||!axis.values.includes(o.value))throw Error('Invalid subject state action '+concept.id+'/'+id);
      }
    }
  }
  function planConceptAction(registry,concept,id,contributors,rulesets=[],selections={},overrides={}){
    validateConcepts([concept]);
    if(!conceptId(id)||!Object.hasOwn(concept.actions||{},id))throw Error('Unknown concept action '+id);
    const resolved=resolveContributors(registry,contributors,rulesets,selections,overrides);
    if(!resolved.ok)return {status:'conflict',conflicts:resolved.conflicts,plan:null,candidates:resolved.candidates};
    const action=concept.actions[id],missing=new Set();
    function valueFor(key){
      if(!Object.hasOwn(resolved.values,key)){missing.add(key);return undefined;}
      return resolved.values[key].value;
    }
    function prepare(o){
      if(o.when){
        const v=valueFor(o.when.property);
        if(v===undefined)return null;
        if(v.kind!=='boolean')throw Error('Action guard requires boolean '+o.when.property);
        if(v.value!==o.when.equals)return null;
      }
      const out=structuredClone(o);delete out.when;
      if(o.magnitude?.property!==undefined){
        const v=valueFor(o.magnitude.property);
        if(v===undefined)return null;
        out.magnitude=structuredClone(v);
        out.source_property=o.magnitude.property;
      }
      if(out.magnitude){
        const v=out.magnitude;
        if(o.op==='stat.at_least'&&!fixedMagnitude(v)||o.op==='stat.consume'&&(!fixedMagnitude(v)||v.value<=0)||o.op==='stat.change'&&!effectMagnitude(v))throw Error('Incompatible action magnitude '+o.op);
      }
      return out;
    }
    const requirements=(action.requirements||[]).map(prepare).filter(Boolean);
    const operations=action.operations.map(prepare).filter(Boolean);
    if(missing.size)return {status:'missing',missing:[...missing].sort(),plan:null};
    if(!operations.length)return {status:'empty',plan:null};
    // Nothing here reads or mutates game state. Even a ready plan can fail
    // permissions, inventory, cooldown, targets or stale-state checks at host.
    return structuredClone({status:'planned',plan:{concept:concept.id,action:id,kind:action.kind,requirements,operations,properties:resolved.values},unusedModules:resolved.unusedModules});
  }
  function checkConceptExtensions(item){
    if(item.capabilities!==undefined&&!uniqueIds(item.capabilities,64))throw Error('Invalid concept capabilities '+item.id);
    if(item.relationships!==undefined){
      const seen=new Set();
      if(!Array.isArray(item.relationships)||item.relationships.length<1||item.relationships.length>128)throw Error('Invalid concept relationships '+item.id);
      for(const relation of item.relationships){
        if(!only(relation,['kind','target'])||!relationKinds.includes(relation.kind)||!validRef(relation.target))throw Error('Invalid concept relationship '+item.id);
        const key=JSON.stringify(canonical(relation));
        if(seen.has(key))throw Error('Duplicate concept relationship '+item.id);
        seen.add(key);
      }
    }
    if(item.state_axes!==undefined&&(!record(item.state_axes)||Object.keys(item.state_axes).length<1||Object.keys(item.state_axes).length>16||Object.entries(item.state_axes).some(([key,a])=>!conceptId(key)||!validAxis(a))))throw Error('Invalid concept state axes '+item.id);
    validateActions(item);
    validateDiscoveryOffers(item.discovery_offers);
  }
  function validateRepresentations(concepts,assets){
    const byId=new Map((concepts||[]).map(c=>[c.id,c]));
    for(const a of assets){
      if(a.representation===undefined)continue;
      const d=byId.get(a.concept_id),p=a.representation;
      if(!d||!only(p,['role','when'])||!conceptId(p.role)||p.when!==undefined&&(!record(p.when)||Object.keys(p.when).length>16||Object.entries(p.when).some(([key,val])=>!Object.hasOwn(d.state_axes||{},key)||!axisValues(d.state_axes[key]).includes(val))))throw Error('Invalid representation '+a.id);
    }
  }
  // Semantic edges are discoverable, not render dependencies. References may
  // intentionally point outside the current archive; never chase them on load.
  function conceptGraph(concepts,assets){
    validateConcepts(concepts,assets);
    validateRepresentations(concepts,assets);
    const edges=[],edgeKeys=new Set(),byConcept=new Set((concepts||[]).map(c=>c.id)),byAsset=new Set(assets.map(a=>a.id)),reverse=new Map();
    const append=(source,kind,target)=>{
      const local=!target.archive_sha256&&(target.kind==='concept'?byConcept.has(target.id):byAsset.has(target.id));
      const edgeKey=JSON.stringify([source.kind,source.id,kind,target.kind,target.id,target.archive_sha256??null]);
      if(edgeKeys.has(edgeKey))return;
      edgeKeys.add(edgeKey);
      const e={source,kind,target,available_locally:local};
      const key=JSON.stringify([target.kind,target.id,target.archive_sha256??null]);
      if(!reverse.has(key))reverse.set(key,[]);
      reverse.get(key).push(e);edges.push(e);
    };
    for(const c of concepts||[])for(const e of c.relationships||[])append({kind:'concept',id:c.id},e.kind,e.target);
    for(const a of assets)if(byConcept.has(a.concept_id))append({kind:'concept',id:a.concept_id},'represented_by',{kind:'asset',id:a.id});
    // Derive reverse links on demand; graph cycles are legal.
    return structuredClone({edges,reverse:[...reverse].map(([key,links])=>({target:JSON.parse(key),links}))});
  }
  function projectStates(concept,instance={}){
    validateConcepts([concept]);
    if(!only(instance,['states','stats'])||(instance.states!==undefined&&!record(instance.states))||(instance.stats!==undefined&&!record(instance.stats)))throw Error('Invalid instance state');
    const axes=concept.state_axes||{},values=new Map(),missing=[];
    for(const [key,v] of Object.entries(instance.states||{})){
      if(!Object.hasOwn(axes,key)||axes[key].kind!=='enum'||!axes[key].values.includes(v))throw Error('Invalid explicit state '+key);
    }
    for(const [key,a] of Object.entries(axes)){
      if(a.kind==='enum'){
        const v=Object.hasOwn(instance.states||{},key)?instance.states[key]:a.default;
        if(v===undefined)missing.push(key);else values.set(key,v);
      }else{
        const stats=instance.stats||{};
        if(!Object.hasOwn(stats,a.current)||!Object.hasOwn(stats,a.maximum)){missing.push(key);continue;}
        const current=stats[a.current],maximum=stats[a.maximum];
        if(!bounded(maximum,0,1e9)||maximum===0||!bounded(current,0,maximum))throw Error('Invalid ratio state '+key);
        values.set(key,a.bands.find(b=>current/maximum<=b.max).state);
      }
    }
    return {states:Object.fromEntries(values),missing};
  }
  // Host chooses role and optional style; declared selector subsets match only
  // known state. Most specific match wins; ties are reported, not guessed.
  function selectRepresentation(concept,assets,{role,style,instance={},allowFallback=false}={}){
    validateConcepts([concept]);
    if(!conceptId(role)||(style!==undefined&&typeof style!=='string')||typeof allowFallback!=='boolean')throw Error('Invalid representation request');
    const available=assets.filter(a=>a.concept_id===concept.id);
    validateRepresentations([concept],available);
    const {states,missing}=projectStates(concept,instance);
    const candidates=available.filter(a=>a.representation?.role===role&&(style===undefined||a.style===style));
    const matches=candidates.filter(a=>Object.entries(a.representation.when||{}).every(([key,v])=>Object.hasOwn(states,key)&&states[key]===v));
    // An unconditional base is a fallback when there are known/unknown state
    // dimensions. A conditional match may leave orthogonal axes unspecified.
    const specific=matches.filter(a=>Object.keys(a.representation.when||{}).length>0);
    const pool=specific.length?specific:(!Object.keys(concept.state_axes||{}).length||allowFallback?matches:[]);
    const best=pool.length?Math.max(...pool.map(a=>Object.keys(a.representation.when||{}).length)):-1;
    const ids=pool.filter(a=>Object.keys(a.representation.when||{}).length===best).map(a=>a.id).sort();
    return {status:ids.length>1?'ambiguous':ids.length===0?'unavailable':best===0&&Object.keys(concept.state_axes||{}).length?'fallback':'matched',asset:ids.length===1?ids[0]:null,candidates:ids,states,missing};
  }
  function validateConcepts(items,assets=null){
    if(items===undefined)return;
    if(!Array.isArray(items)||items.length>3000)throw Error('Invalid concept collection');
    const ids=new Set(),linked=assets===null?null:new Set(assets.map(a=>a.concept_id));
    for(const item of items){
      if(!only(item,['schema','id','name','description','license','physical','defaults','capabilities','relationships','state_axes','actions','discovery_offers'])||item.schema!=='smi-concept/1'||!conceptId(item.id)||!shortString(item.name,160)||!shortString(item.license,128)||ids.has(item.id))throw Error('Invalid or duplicate concept '+item?.id);
      if(item.description!==undefined&&(typeof item.description!=='string'||item.description.length>4000))throw Error('Invalid concept description '+item.id);
      if(item.physical!==undefined&&(!only(item.physical,['width_m','depth_m','height_m','mass_kg','capacity_l'])||!Object.keys(item.physical).length||Object.values(item.physical).some(v=>!bounded(v,0,1e9)||v===0)))throw Error('Invalid physical properties '+item.id);
      if(item.defaults!==undefined&&(!record(item.defaults)||!Object.keys(item.defaults).length||Object.keys(item.defaults).length>32||Object.entries(item.defaults).some(([k,v])=>!ruleId(k)||!validMap(v))))throw Error('Invalid ruleset defaults '+item.id);
      checkConceptExtensions(item);
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
  /* Optional capability offers. Insert into the existing collection core.
   * Pure metadata matching; never retrieve archives, mutate state or activate offers. */
  const discoveryScopes = ['concept', 'representation', 'context'];
  const discoveryPhysicalUnits = Object.freeze({width_m:'m',depth_m:'m',height_m:'m',mass_kg:'kg',capacity_l:'l'});
  const discoveryNumber = x => bounded(x,-1e9,1e9);
  // The existing slot contract accepts bounded names ending in /1, not rule IDs.
  const discoveryInterfaceId = x => shortString(x,160)&&x.endsWith('/1');
  function discoveryValue(x) {
    // Reuse the canonical typed quantity/boolean validator. Enum is a known
    // discovery/context value, not a new gameplay magnitude kind.
    return (x?.kind==='boolean'||x?.kind==='quantity') ? validValue(x) : x?.kind==='enum' && only(x,['kind','value']) && conceptId(x.value);
  }
  function compileDiscoveryRequirements(requirements) {
    if (!Array.isArray(requirements) || requirements.length < 1 || requirements.length > 32) throw Error('Invalid discovery requirements');
    return requirements.map(r => {
      if (!record(r) || !discoveryScopes.includes(r.scope)) throw Error('Invalid discovery requirement scope');
      let group, predicate;
      if (r.op === 'capability.has') {
        if (!only(r,['scope','op','key']) || !conceptId(r.key)) throw Error('Invalid capability requirement');
        group='capabilities'; predicate=v=>v===true;
      } else if (r.op === 'interface.has') {
        if (!only(r,['scope','op','key']) || r.scope!=='representation' || !discoveryInterfaceId(r.key)) throw Error('Invalid interface requirement');
        group='interfaces'; predicate=v=>v===true;
      } else if (r.op === 'fact.equals') {
        if (!only(r,['scope','op','key','expected']) || !conceptId(r.key) || !discoveryValue(r.expected)) throw Error('Invalid equality requirement');
        group='properties'; predicate=v=>v.kind===r.expected.kind && v.value===r.expected.value && (v.kind!=='quantity'||v.unit===r.expected.unit);
      } else if (r.op === 'quantity.range') {
        if (!only(r,['scope','op','key','unit','min','max']) || !conceptId(r.key) || !unitId(r.unit) || !discoveryNumber(r.min)||!discoveryNumber(r.max)||r.min>r.max) throw Error('Invalid quantity range');
        group='properties'; predicate=v=>v.kind==='quantity'&&v.unit===r.unit&&v.value>=r.min&&v.value<=r.max;
      } else throw Error('Unsupported discovery requirement');
      return {requirement:structuredClone(r),group,predicate};
    });
  }
  function validateDiscoveryOffers(offers) {
    if (offers===undefined) return;
    if (!record(offers) || Object.keys(offers).length<1 || Object.keys(offers).length>32) throw Error('Invalid discovery offers');
    for (const [id,offer] of Object.entries(offers)) {
      if (!conceptId(id)||!only(offer,['role','requirements'])||!conceptId(offer.role)) throw Error('Invalid discovery offer '+id);
      compileDiscoveryRequirements(offer.requirements);
    }
  }
  function discoveryFact(value,source) {return {value,source};}
  function discoveryBlank() {return {capabilities:new Map(),interfaces:new Map(),properties:new Map()};}
  function discoveryConceptFacts(concept,ref) {
    const facts=discoveryBlank();
    if (!concept) return facts;
    if (concept.capabilities!==undefined && (!Array.isArray(concept.capabilities)||concept.capabilities.length>64||new Set(concept.capabilities).size!==concept.capabilities.length||!concept.capabilities.every(conceptId))) throw Error('Invalid catalog concept capabilities');
    for(const key of concept.capabilities||[]) facts.capabilities.set(key,discoveryFact(true,{ref,path:'capabilities'}));
    if(concept.physical!==undefined && (!record(concept.physical)||!Object.keys(concept.physical).length)) throw Error('Invalid physical projection');
    for(const [key,value] of Object.entries(concept.physical||{})) {
      if(!Object.hasOwn(discoveryPhysicalUnits,key)||!discoveryNumber(value)||value<=0) throw Error('Invalid physical projection '+key);
      facts.properties.set('physical.'+key,discoveryFact({kind:'quantity',value,unit:discoveryPhysicalUnits[key]},{ref,path:'physical.'+key}));
    }
    return facts;
  }
  function discoveryAssetFacts(asset,ref) {
    const facts=discoveryBlank();
    if(asset.interfaces!==undefined&&(!Array.isArray(asset.interfaces)||asset.interfaces.length>256||new Set(asset.interfaces).size!==asset.interfaces.length||!asset.interfaces.every(discoveryInterfaceId))) throw Error('Invalid catalog interfaces');
    for(const key of asset.interfaces||[]) facts.interfaces.set(key,discoveryFact(true,{ref,path:'interfaces'}));
    return facts;
  }
  function discoveryContextFacts(context) {
    const facts=discoveryBlank();
    if(context===undefined)return facts;
    if(!only(context,['capabilities','properties']))throw Error('Invalid query context');
    for(const group of ['capabilities','properties']) {
      if(!Object.hasOwn(context,group))continue;
      const values=context[group];
      if(!record(values)||Object.keys(values).length>128)throw Error('Invalid context group');
      for(const [key,value] of Object.entries(values)) {
        if(!conceptId(key)||(group==='capabilities'?typeof value!=='boolean':!discoveryValue(value)))throw Error('Invalid context fact');
        facts[group].set(key,discoveryFact(structuredClone(value),{kind:'query-context',path:group+'.'+key}));
      }
    }
    return facts;
  }
  function evaluateCompiledDiscovery(facts,compiled) {
    const evidence=compiled.map(({requirement:r,group,predicate})=>{
      const entry=facts[r.scope][group].get(r.key);
      return {requirement:r,status:!entry?'unknown':predicate(entry.value)?'compatible':'incompatible',evidence:entry||null};
    });
    const summary=rows=>!rows.length?'not-required':rows.some(x=>x.status==='incompatible')?'incompatible':rows.some(x=>x.status==='unknown')?'unknown':'compatible';
    return {status:summary(evidence),scopes:Object.fromEntries(discoveryScopes.map(s=>[s,summary(evidence.filter(e=>e.requirement.scope===s))])),evidence};
  }
  /* Catalog data is assumed to have passed existing publication validation.
   * Locators are claims, not verified bytes. Caller must use the exact provider
   * for retrieval; catalog_sha256 identifies the caller's catalog snapshot. */
  function createDiscoveryIndex(catalog,options={}) {
    return buildDiscoveryIndex(catalog,options,false);
  }
  // An isolated validated archive projection is not a public catalog or a
  // downloadable locator. Its identity is the digest of the actual ZIP bytes.
  function createArchiveDiscoveryIndex(pack,archive_sha256) {
    if(!digestId(archive_sha256)||!record(pack)||!shortString(pack.pack_id,256)||!Array.isArray(pack.assets))throw Error('Invalid archive discovery input');
    validateConcepts(pack.concepts,pack.assets);
    validateRepresentations(pack.concepts||[],pack.assets);
    const owner=pack.pack_id;
    const projection={schema:'smi-public-catalog/1',packs:[{id:owner,archive_sha256}],
      concepts:(pack.concepts||[]).map(c=>({...c,pack:owner})),
      assets:pack.assets.map(a=>({...a,pack:owner,interfaces:a.implements||[]}))};
    return buildDiscoveryIndex(projection,{catalog_sha256:archive_sha256},true);
  }
  function buildDiscoveryIndex(catalog,{catalog_sha256}={},localArchive=false) {
    const identity=(kind,id,archive_sha256)=>({kind,id,archive_sha256});
    const exactRef=r=>validRef(r)&&digestId(r.archive_sha256);
    const key=r=>JSON.stringify([r.kind,r.id,r.archive_sha256]);
    const cmp=(a,b)=>a<b?-1:a>b?1:0;
    if(!record(catalog)||catalog.schema!=='smi-public-catalog/1'||!digestId(catalog_sha256)||!Array.isArray(catalog.packs)||!Array.isArray(catalog.assets)||catalog.assets.length>50000||catalog.packs.length>4096||!Array.isArray(catalog.concepts??[])||(catalog.concepts??[]).length>20000) throw Error('Invalid discovery catalog');
    const packs=new Map(),concepts=new Map(),subjects=new Map(),offers=new Map(),byRole=new Map(),byKind={concept:[],asset:[]},unavailable=new Set();
    for(const p of catalog.packs) {
      if(!record(p)||typeof p.id!=='string'||!p.id||packs.has(p.id))throw Error('Duplicate or invalid pack');
      if(p.zip!=null&&!p.archived&&(!digestId(p.archive_sha256)||p.immutable_zip!==undefined&&p.immutable_zip!=='archives/sha256/'+p.archive_sha256+'.zip'))throw Error('Invalid pack locator');
      packs.set(p.id,p);
    }
    const packRef=(kind,id,owner)=>{
      const p=packs.get(owner);if(!p||p.archived||(!localArchive&&!p.zip)||!digestId(p.archive_sha256))return null;
      return identity(kind,id,p.archive_sha256);
    };
    function insertSubject(s) {const k=key(s.ref);if(subjects.has(k))throw Error('Duplicate subject');subjects.set(k,s);byKind[s.ref.kind].push(s);}
    for(const original of catalog.concepts||[]) {
      const c=structuredClone(original);
      if(!record(c)||!conceptId(c.id)||concepts.has(c.id))throw Error('Duplicate or invalid concept');
      const ref=packRef('concept',c.id,c.pack);if(!ref)throw Error('Unresolved concept owner');
      validateDiscoveryOffers(c.discovery_offers);
      const facts=discoveryConceptFacts(c,ref),subject={ref,concept:facts,representation:discoveryBlank(),entry:c};
      concepts.set(c.id,{owner:c.pack,subject});insertSubject(subject);
      for(const [id,offer] of Object.entries(c.discovery_offers||{})) {
        if(offers.size>=20000)throw Error('Too many discovery offers');
        const o={ref:{...ref,offer_id:id},role:offer.role,compiled:compileDiscoveryRequirements(offer.requirements)};
        const k=JSON.stringify([key(ref),id]);offers.set(k,o);if(!byRole.has(o.role))byRole.set(o.role,[]);byRole.get(o.role).push(o);
      }
    }
    const seenAssets=new Set();
    for(const original of catalog.assets) {
      const a=structuredClone(original);
      if(!record(a)||typeof a.id!=='string'||!a.id||a.id.length>256||seenAssets.has(a.id))throw Error('Duplicate or invalid asset');seenAssets.add(a.id);
      if(a.legacy||a.discovery==='hidden'){unavailable.add(a.id);continue;}
      const ref=packRef('asset',a.id,a.pack);
      if(!ref){unavailable.add(a.id);continue;}
      const c=concepts.get(a.concept_id);
      // An unresolved or cross-pack concept_id is a hint, not proof of identity.
      const facts=c&&c.owner===a.pack?c.subject.concept:discoveryBlank();
      insertSubject({ref,concept:facts,representation:discoveryAssetFacts(a,ref),entry:a});
    }
    for(const group of Object.values(byKind))group.sort((a,b)=>cmp(key(a.ref),key(b.ref)));
    for(const group of byRole.values())group.sort((a,b)=>cmp(JSON.stringify(a.ref),JSON.stringify(b.ref)));
    const allOffers=[...offers.values()].sort((a,b)=>cmp(JSON.stringify(a.ref),JSON.stringify(b.ref)));
    function offerLookup(ref) {
      if(!only(ref,['kind','id','archive_sha256','offer_id'])||ref.kind!=='concept'||!conceptId(ref.offer_id))throw Error('Invalid offer reference');
      const {offer_id,...owner}=ref;if(!exactRef(owner))throw Error('Invalid offer owner');return offers.get(JSON.stringify([key(owner),offer_id]));
    }
    function queryInternal(request,ranking=null) {
      if(!only(request,['direction','ref','role','target_kind','context','limit'])||!['subject','offer'].includes(request.direction)||!Number.isInteger(request.limit)||request.limit<1||request.limit>100||request.role!==undefined&&!conceptId(request.role))throw Error('Invalid discovery query');
      const forward=request.direction==='subject';
      if(forward&&!exactRef(request.ref))throw Error('Invalid subject reference');
      if(!forward&&!['concept','asset'].includes(request.target_kind))throw Error('Reverse query requires target kind');
      if(forward&&request.target_kind!==undefined)throw Error('Target kind only applies to reverse queries');
      const anchor=forward?subjects.get(key(request.ref)):offerLookup(request.ref);
      if(!anchor)throw Error('Unknown exact discovery identity');
      const context=discoveryContextFacts(request.context),others=forward?(request.role?byRole.get(request.role)||[]:allOffers):byKind[request.target_kind];
      const groups=Object.fromEntries(['compatible','unknown','incompatible'].map(s=>[s,{total:0,matches:[]} ]));
      const eligible=ranking?[]:null;
      const match=(subject,offer,result)=>({origin:'derived',relation:'compatible_with',role:offer.role,subject:subject.ref,offer:offer.ref,...result});
      for(const item of others) {
        const subject=forward?anchor:item,offer=forward?item:anchor;
        if(!forward&&request.role&&offer.role!==request.role)continue;
        if(subject.ref.archive_sha256===offer.ref.archive_sha256&&(subject.ref.kind==='concept'&&subject.ref.id===offer.ref.id||subject.entry.concept_id===offer.ref.id&&subject.entry.pack===concepts.get(offer.ref.id)?.owner))continue;
        const result=evaluateCompiledDiscovery({concept:subject.concept,representation:subject.representation,context},offer.compiled);
        const group=groups[result.status];group.total++;
        if(eligible&&result.status==='compatible')eligible.push(subject);
        if(group.matches.length<request.limit)group.matches.push(match(subject,offer,result));
      }
      if(ranking) {
        const weights=ranking.weights;
        const candidates=eligible.map(s=>s.entry);
        // Ranking is an optional preference over every already-eligible candidate,
        // not a hard filter and not a materialized all-pairs graph.
        const scores=rankRelated(ranking.source.entry,candidates,{weights,limit:request.limit});
        const eligibleById=new Map(eligible.map(s=>[s.ref.id,s]));
        const chosen=new Set();const rows=[];
        const add=(subject,preference)=>{
          chosen.add(subject.ref.id);
          rows.push({...match(subject,anchor,evaluateCompiledDiscovery({concept:subject.concept,representation:subject.representation,context},anchor.compiled)),preference});
        };
        for(const score of scores) {
          const subject=eligibleById.get(score.id);
          if(!subject)throw Error('Preference score for ineligible candidate');
          const dimensions=[...(score.shared.length?['semantic']:[]),...(score.color!==null?['color']:[]),...(score.style!==null?['style']:[])];
          const coverage=dimensions.reduce((n,k)=>n+weights[k],0)/(weights.semantic+weights.color+weights.style);
          add(subject,{...score,dimensions_with_evidence:dimensions,evidence_weight_fraction:coverage});
        }
        for(const subject of eligible) {if(rows.length>=request.limit)break;if(!chosen.has(subject.ref.id))add(subject,null);}
        groups.compatible.matches=rows;
      }
      return structuredClone({...(localArchive?{archive_sha256:catalog_sha256,scope:'local-archive'}:{catalog_sha256}),contract:'smi-capability-discovery/1',...(ranking?{ranking_scope:'all-compatible-candidates'}:{}),groups});
    }
    function query(request) { return queryInternal(request); }
    /* Reuse the current ranker; missing similarity signals do not disqualify an
     * eligible candidate. The original score is retained with explicit evidence. */
    function rankEligible(request,source,options={}) {
      if(request?.direction!=='offer'||request.target_kind!=='asset'||!exactRef(source)||source.kind!=='asset'||!only(options,['weights']))throw Error('Invalid eligible ranking request');
      const weights=options.weights??{semantic:0.65,color:0.25,style:0.10};
      const names=['semantic','color','style'];
      if(!only(weights,names)||!names.every(k=>Number.isFinite(weights[k])&&weights[k]>=0)||!Number.isFinite(names.reduce((n,k)=>n+weights[k],0))||names.reduce((n,k)=>n+weights[k],0)<=0)throw Error('Invalid preference weights');
      const src=subjects.get(key(source));if(!src)throw Error('Unknown exact ranking source');
      return queryInternal(request,{source:src,weights:structuredClone(weights)});
    }
    return Object.freeze({query,rankEligible,summary:()=>({subjects:subjects.size,offers:offers.size,excluded_assets:unavailable.size,...(localArchive?{archive_sha256:catalog_sha256,scope:'local-archive'}:{catalog_sha256})})});
  }
  // A bounded presentation of the existing catalog, not a second registry.
  // Static adjacency is derived once; dynamic discovery and similarity are
  // evaluated only for the focused node. No archive or semantic traversal fetch.
  function createRelationshipExplorer(catalog,discovery=null){
    if(catalog?.schema!=='smi-public-catalog/1'||!Array.isArray(catalog.assets)||catalog.assets.length>50000||!Array.isArray(catalog.packs)||!Array.isArray(catalog.concepts??[]))throw Error('Invalid relationship catalog');
    const key=r=>JSON.stringify([r.kind,r.id,r.archive_sha256??null]),compare=(a,b)=>a<b?-1:a>b?1:0;
    const packs=new Map(catalog.packs.map(p=>[p.id,p])),assets=new Map(),concepts=new Map(),nodes=new Map(),adj=new Map(),edgeKeys=new Set();
    function exact(kind,item){
      const p=packs.get(item.pack);
      return p&&!p.archived&&p.zip&&digestId(p.archive_sha256)?{kind,id:item.id,archive_sha256:p.archive_sha256}:null;
    }
    function addNode(ref,item=null){
      const k=key(ref);
      if(!nodes.has(k))nodes.set(k,{key:k,ref:{...ref},name:item?.name||ref.id,available:!!item,hidden:item?.discovery==='hidden',pack:item?.pack??null});
      return k;
    }
    for(const a of catalog.assets){if(a.legacy)continue;const r=exact('asset',a);if(!r)continue;if(assets.has(a.id))throw Error('Duplicate graph asset');assets.set(a.id,{item:a,ref:r,key:addNode(r,a)});}
    for(const c of catalog.concepts||[]){const r=exact('concept',c);if(!r)continue;if(concepts.has(c.id))throw Error('Duplicate graph concept');concepts.set(c.id,{item:c,ref:r,key:addNode(r,c)});}
    function target(r){
      if(!validRef(r))throw Error('Invalid graph reference');
      const current=(r.kind==='asset'?assets:concepts).get(r.id);
      if(current&&(!r.archive_sha256||r.archive_sha256===current.ref.archive_sha256))return current.key;
      return addNode(r);
    }
    const edge=(from,to,type,label,evidence={})=>({from,to,type,label,evidence,key:JSON.stringify([from,to,type,label,evidence.offer_id??null])});
    function staticEdge(from,to,type,label,evidence){
      const e=edge(from,to,type,label,evidence);if(edgeKeys.has(e.key))return;edgeKeys.add(e.key);
      for(const k of new Set([from,to])){if(!adj.has(k))adj.set(k,[]);adj.get(k).push(e);}
    }
    for(const a of assets.values()){
      const c=concepts.get(a.item.concept_id);
      if(c&&c.item.pack===a.item.pack)staticEdge(c.key,a.key,'representation',a.item.representation?.role||'represented_by',{selectors:a.item.representation?.when||{}});
      for(const id of a.item.render_refs||[]){
        // A bundled reference is to the source archive's member; the node is
        // the canonical current catalog owner for navigation, not a replacement
        // runtime locator. The exact source archive remains in the evidence.
        staticEdge(a.key,target({kind:'asset',id}),'dependency','uses',{source_archive_sha256:a.ref.archive_sha256,member_id:id,note:'Source archive member; node navigates to current catalog owner.'});
      }
    }
    for(const c of concepts.values())for(const r of c.item.relationships||[])staticEdge(c.key,target(r.target),'authored',r.kind,{target:r.target});
    for(const list of adj.values())list.sort((a,b)=>compare(a.key,b.key));
    function focus(ref,{depth=1,limit=28,types=['representation','dependency','authored','compatible','similarity']}={}){
      if(!validRef(ref)||!Number.isInteger(depth)||depth<1||depth>2||!Number.isInteger(limit)||limit<2||limit>40||!Array.isArray(types)||types.some(t=>!['representation','dependency','authored','compatible','unknown','incompatible','similarity'].includes(t)))throw Error('Invalid relationship view');
      const current=(ref.kind==='asset'?assets:concepts).get(ref.id);
      if(!current||ref.archive_sha256&&ref.archive_sha256!==current.ref.archive_sha256)throw Error('Unavailable graph focus');
      const root=current.key;
      const base=nodes.get(root),active=new Set(types),dynamic=[],counts={},errors=[];
      const recordMatch=(m,direction)=>{
        const other=direction==='subject'?m.offer:m.subject;
        const {offer_id,...owner}=other,otherKey=target(owner);
        if(otherKey===root)return;
        dynamic.push(edge(direction==='subject'?otherKey:root,direction==='subject'?root:otherKey,m.status,m.role,{offer_id:m.offer.offer_id,offer:m.offer,subject:m.subject,scopes:m.scopes,requirements:m.evidence,note:direction==='offer'&&base.ref.kind==='asset'?'Offer projected through the focused representation; authored owner is the concept.':undefined}));
      };
      const consume=(result,direction)=>{
        for(const [status,g] of Object.entries(result.groups)){
          counts[status]=(counts[status]||0)+g.total;
          if(active.has(status))for(const m of g.matches)recordMatch(m,direction);
        }
      };
      if(discovery&&base.ref.archive_sha256&&['compatible','unknown','incompatible'].some(t=>active.has(t))){
        try{
          consume(discovery.query({direction:'subject',ref:base.ref,limit:8}),'subject');
          const concept=base.ref.kind==='concept'?concepts.get(base.ref.id):concepts.get(assets.get(base.ref.id)?.item.concept_id);
          if(concept&&concept.item.pack===base.pack)for(const offer_id of Object.keys(concept.item.discovery_offers||{}).sort().slice(0,8)){
            consume(discovery.query({direction:'offer',ref:{...concept.ref,offer_id},target_kind:'asset',limit:8}),'offer');
          }
        }catch(e){errors.push('Capability evidence unavailable: '+e.message);}
      }
      const source=base.ref.kind==='asset'?assets.get(base.ref.id)?.item:null;
      if(source?.material&&active.has('similarity')){
        for(const m of rankRelated(source,catalog.assets,{limit:6,categoryPrefixes:['textures','world.terrain','world.vegetation','world.props']})){
          const t=assets.get(m.id);if(t&&t.key!==root)dynamic.push(edge(root,t.key,'similarity','suggested match',{score:m.score,shared:m.shared,color:m.color,style:m.style}));
        }
      }
      const order=new Map([['representation',0],['authored',1],['compatible',2],['dependency',3],['similarity',4],['unknown',5],['incompatible',6]]);
      const priority=(a,b)=>(order.get(a.type)-order.get(b.type))||compare(a.key,b.key);
      const direct=[...(adj.get(root)||[]),...dynamic].filter(e=>active.has(e.type)).sort(priority);
      const selected=new Map([[root,0]]),frontier=[];
      const add=(e,origin,ring)=>{
        const k=e.from===origin?e.to:e.from;if(selected.has(k)||selected.size>=limit)return;
        selected.set(k,ring);if(nodes.get(k)?.available)frontier.push(k);
      };
      // Round-robin relationship groups prevents a large composition from
      // consuming every visible node before semantic or compatible neighbors.
      const buckets=new Map();for(const e of direct){if(!buckets.has(e.type))buckets.set(e.type,[]);buckets.get(e.type).push(e);}
      while(selected.size<limit&&[...buckets.values()].some(b=>b.length)){
        for(const b of buckets.values()){if(b.length)add(b.shift(),root,1);}
      }
      if(depth===2)for(const k of [...frontier]){
        for(const e of (adj.get(k)||[]).filter(e=>active.has(e.type)).sort(priority)){if(selected.size>=limit)break;add(e,k,2);}
        if(selected.size>=limit)break;
      }
      const edges=new Map();
      for(const k of selected.keys())for(const e of adj.get(k)||[])if(active.has(e.type)&&selected.has(e.from)&&selected.has(e.to))edges.set(e.key,e);
      for(const e of dynamic)if(selected.has(e.from)&&selected.has(e.to)&&active.has(e.type))edges.set(e.key,e);
      const output=[...edges.values()].sort(priority);
      const allDirect=new Set(direct.map(e=>e.from===root?e.to:e.from).filter(k=>k!==root));
      return structuredClone({root,nodes:[...selected].map(([k,ring])=>({...nodes.get(k),ring})),edges:output.slice(0,160),omitted_edges:Math.max(0,output.length-160),omitted_neighbors:[...allDirect].filter(k=>!selected.has(k)).length,counts,errors});
    }
    return Object.freeze({focus});
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
    validateConcepts(concepts,assets);
    validateRepresentations(concepts,assets);
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
    validateRepresentations(definitions,chosen);
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
  return Object.freeze({createRelationshipExplorer,validateDiscoveryOffers,createDiscoveryIndex,createArchiveDiscoveryIndex,validateMaterialProfiles,rankRelated,safePath,join,resolveCollection,dependencyClosure,writeSelection,equivalent,sameAsset,sameBytes,validateConcepts,validateRepresentations,conceptGraph,projectStates,selectRepresentation,planConceptAction,resolveDefaults,validateRuleRegistry,resolveContributors,MAX_PACKS,MAX_ASSETS,MAX_TEXTURES});
});
