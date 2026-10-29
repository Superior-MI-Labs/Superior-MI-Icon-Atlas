"use strict";
/* Universal versioned compatibility contracts, slot selection, presets. Pure UMD module. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.VisualAtlasSlots=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
 const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
 const validName=s=>typeof s==='string'&&s.length>0&&s.length<=160;
 const numeric=v=>typeof v==='number'&&Number.isFinite(v);
 function accepts(def,value){return def?.type==='boolean'?typeof value==='boolean':def?.type==='number'?numeric(value)&&(def.min===undefined||value>=def.min)&&(def.max===undefined||value<=def.max):def?.type==='enum'?typeof value==='string'&&Array.isArray(def.values)&&def.values.includes(value):false;}
 function validate(pack){
  const errors=[],ids=new Map((pack.assets||[]).map(a=>[a.id,a])),contracts=pack.interfaces||{};
  if(typeof contracts!=='object'||Array.isArray(contracts)||!contracts)return ['interfaces must be an object'];
  if(Object.keys(contracts).length>256)errors.push('too many interfaces');
  function size(id,stack=new Set()){
    if(stack.has(id))throw Error('size reference cycle '+id);
    const a=ids.get(id);if(!a)throw Error('missing asset '+id);
    const next=new Set(stack);next.add(id);
    if(a.kind==='region')return a.logical_size_px||a.rect_px.slice(2,4);
    if(a.kind==='composition')return a.size_px;
    if(a.kind==='sequence')return size(a.frames[0].asset,next);
    if(a.kind==='state_set')return size(a.states[a.default_state],next);
    throw Error('invalid asset kind '+id);
  }
  for(const [id,contract] of Object.entries(contracts)){
    if(!validName(id)||!id.endsWith('/1')||!contract||!Array.isArray(contract.size_px)||contract.size_px.length!==2||!contract.size_px.every(n=>Number.isInteger(n)&&n>0)||typeof contract.allow_scale!=='boolean')errors.push('invalid versioned interface '+id);
  }
  for(const a of ids.values()){
    for(const id of a.implements||[]){
      if(!own(contracts,id))errors.push(a.id+': undeclared interface '+id);
      else try {const s=size(a.id),c=contracts[id];if(!c.allow_scale&&(s[0]!==c.size_px[0]||s[1]!==c.size_px[1]))errors.push(a.id+': incompatible size for '+id);}catch(err){errors.push(a.id+': '+err.message);}
    }
    if(a.kind!=='composition')continue;
    const slots=a.slots||{},presets=a.presets||{};
    if(Object.keys(slots).length>64||Object.keys(presets).length>100)errors.push(a.id+': too many slots or presets');
    const used=new Set();
    for(const layer of a.layers||[]){
      if(layer.slot!==undefined){
        if(!validName(layer.slot)||!own(slots,layer.slot))errors.push(a.id+': unknown layer slot '+layer.slot);
        else used.add(layer.slot);
      }
    }
    for(const [key,slot] of Object.entries(slots)){
      if(!validName(key)||!slot||!validName(slot.accepts)||!own(contracts,slot.accepts)||!Array.isArray(slot.options)||!slot.options.length||slot.options.length>128||!slot.options.includes(slot.default)||new Set(slot.options).size!==slot.options.length){errors.push(a.id+': invalid slot '+key);continue;}
      if(!used.has(key))errors.push(a.id+': unused slot '+key);
      for(const id of slot.options){
        const option=ids.get(id);
        if(!option)errors.push(a.id+': unknown slot option '+id);
        else if(!Array.isArray(option.implements)||!option.implements.includes(slot.accepts))errors.push(a.id+': '+id+' does not implement '+slot.accepts);
      }
    }
    for(const [name,preset] of Object.entries(presets)){
      if(!validName(name)||!preset||typeof preset!=='object'){errors.push(a.id+': invalid preset '+name);continue;}
      for(const [key,value] of Object.entries(preset.slots||{}))if(!own(slots,key)||!slots[key].options.includes(value))errors.push(a.id+': invalid option '+key+' in preset '+name);
      for(const [key,value] of Object.entries(preset.inputs||{}))if(!own(a.inputs||{},key)||!accepts(a.inputs[key],value))errors.push(a.id+': invalid input '+key+' in preset '+name);
    }
    if(a.default_preset!==undefined&&!own(presets,a.default_preset))errors.push(a.id+': unknown default_preset');
  }
  return errors;
 }
 function resolve(asset,presetName=null,overrides={}){
   const slots=asset.slots||{},presets=asset.presets||{};
   const name=presetName||asset.default_preset||null;
   if(name&&!own(presets,name))throw Error('Unknown preset '+name);
   const preset=name?presets[name]:{};
   const selection=Object.fromEntries(Object.entries(slots).map(([key,def])=>[key,def.default]));
   for(const [key,id] of Object.entries(preset.slots||{}))selection[key]=id;
   for(const [key,id] of Object.entries(overrides||{})){
     if(!own(slots,key)||!slots[key].options.includes(id))throw Error('Incompatible slot selection '+key+' → '+id);
     selection[key]=id;
   }
   const inputs={...Object.fromEntries(Object.entries(asset.inputs||{}).map(([k,d])=>[k,d.default])),...(preset.inputs||{})};
   return {preset:name,slots:selection,inputs};
 }
 function refs(asset){return asset.kind==='sequence'?(asset.frames||[]).map(f=>f.asset):asset.kind==='state_set'?Object.values(asset.states||{}):asset.kind==='composition'?[...(asset.layers||[]).filter(l=>l.asset).map(l=>l.asset),...Object.values(asset.slots||{}).flatMap(s=>s.options||[])]:[];}
 return Object.freeze({validate,resolve,refs,accepts});
});
