"use strict";
/* Typed, declarative interaction contract. No eval, scripts, network or DOM. */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.VisualAtlasInteraction=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  const MAX_EVENTS=32,MAX_ACTIONS=12;
  const name=s=>typeof s==='string'&&/^[a-z][a-z0-9_]{0,63}$/.test(s);
  const has=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
  function accepts(def,value){
    if(!def)return false;
    if(def.type==='boolean')return typeof value==='boolean';
    if(def.type==='number')return typeof value==='number'&&Number.isFinite(value)&&(def.min===undefined||value>=def.min)&&(def.max===undefined||value<=def.max);
    if(def.type==='enum')return typeof value==='string'&&Array.isArray(def.values)&&def.values.includes(value);
    return false;
  }
  function check(asset){
    const errors=[];const b=asset?.behavior;if(b===undefined)return errors;
    if(!b||typeof b!=='object'||Array.isArray(b))return ['behavior must be an object'];
    if(!['generic','button','toggle','slider','meter','actor','select'].includes(b.role||'generic'))errors.push('invalid interaction role');
    const inputs=asset.inputs||{};
    if(typeof inputs!=='object'||Array.isArray(inputs))return ['inputs must be an object'];
    const outputs=b.outputs||{};
    if(typeof outputs!=='object'||Array.isArray(outputs)||Object.keys(outputs).length>24)errors.push('invalid outputs');
    else for(const [key,ref] of Object.entries(outputs)){
      if(!name(key)||!ref||!name(ref.from_input)||!has(inputs,ref.from_input))errors.push('invalid output '+key);
    }
    const on=b.on||{};
    if(typeof on!=='object'||Array.isArray(on)||Object.keys(on).length>MAX_EVENTS)errors.push('invalid event map');
    else for(const [event,actions] of Object.entries(on)){
      if(!name(event)||!Array.isArray(actions)||!actions.length||actions.length>MAX_ACTIONS){errors.push('invalid handler '+event);continue;}
      for(const action of actions){
        if(!action||!['toggle','set','emit'].includes(action.op)){errors.push('unknown action '+event);continue;}
        if(action.op==='emit'){
          if(!name(action.event))errors.push('invalid emitted event '+event);
        }else{
          const def=inputs[action.input];
          if(!name(action.input)||!def)errors.push('unknown input '+event);
          else if(action.op==='toggle'&&def.type!=='boolean')errors.push('toggle requires boolean '+event);
          else if(action.op==='set'&&action.source!=='event.value'&&!accepts(def,action.value))errors.push('invalid set value '+event);
          else if(action.op==='set'&&action.source==='event.value'&&action.value!==undefined)errors.push('ambiguous event assignment '+event);
        }
      }
    }
    return errors;
  }
  function initial(asset){return Object.fromEntries(Object.entries(asset.inputs||{}).map(([k,d])=>[k,d.default]));}
  function outputValues(asset,values){
    return Object.fromEntries(Object.entries(asset.behavior?.outputs||{}).map(([k,ref])=>[k,values[ref.from_input]]));
  }
  function dispatch(asset,values,event,payload={}){
    const errors=check(asset);
    if(errors.length)throw Error(errors[0]);
    if(!name(event))throw Error('Invalid event');
    const inputs=asset.inputs||{};const next={...initial(asset),...values};
    const emitted=[];
    for(const action of asset.behavior?.on?.[event]||[]){
      if(action.op==='emit'){emitted.push({name:action.event,values:outputValues(asset,next)});continue;}
      const def=inputs[action.input];
      const target=action.op==='toggle'?!next[action.input]:(action.source==='event.value'?payload.value:action.value);
      if(!accepts(def,target))throw Error('Event '+event+' supplied invalid '+action.input);
      next[action.input]=target;
    }
    return {values:next,outputs:outputValues(asset,next),events:emitted};
  }
  return Object.freeze({check,initial,dispatch,outputValues});
});
