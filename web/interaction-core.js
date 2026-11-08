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

  // Pointer actions derive from the authored visual position and typed
  // interaction event. No new manifest vocabulary or parallel value store.
  function pointerTarget(asset,point,sizeOf,drag=false){
    if(asset?.kind!=='composition'||!asset.behavior||!Number.isFinite(point?.x)||!Number.isFinite(point?.y))return null;
    const on=asset.behavior.on||{};
    if((asset.behavior.role==='toggle'||asset.behavior.role==='button')&&on.activate){
      const [w,h]=asset.size_px||[0,0];
      if(point.x>=0&&point.y>=0&&point.x<=w&&point.y<=h)return {event:'activate',payload:{}};
    }
    if(asset.behavior.role!=='slider'||typeof sizeOf!=='function')return null;
    for(const layer of asset.layers||[]){
      const bind=layer.position_from_input,def=asset.inputs?.[bind?.input];
      if(!bind||def?.type!=='number')continue;
      const event=Object.keys(on).find(key=>on[key].some(action=>action.op==='set'&&action.source==='event.value'&&action.input===bind.input));
      if(!event)continue;
      const dimensions=layer.size_px||(layer.asset?sizeOf(layer.asset):null);
      if(!Array.isArray(dimensions)||dimensions.length!==2||dimensions.some(n=>!Number.isFinite(n)||n<=0))continue;
      const axis=bind.axis==='y'?1:0,crossAxis=1-axis,coord=axis?point.y:point.x,cross=axis?point.x:point.y;
      const extent=dimensions[axis],crossExtent=dimensions[crossAxis],offset=layer.offset_px||[0,0];
      const from=offset[axis]+bind.from_px+extent/2,to=offset[axis]+bind.to_px+extent/2;
      if(from===to)continue;
      if(!drag&&(Math.abs(cross-(offset[crossAxis]+crossExtent/2))>Math.max(18,crossExtent/2+12)||
        coord<Math.min(from,to)-extent/2||coord>Math.max(from,to)+extent/2))continue;
      const fraction=Math.max(0,Math.min(1,(coord-from)/(to-from)));
      const min=def.min??0,max=def.max??1,step=def.step??1;
      const raw=min+fraction*(max-min);
      const value=Number(Math.max(min,Math.min(max,min+Math.round((raw-min)/step)*step)).toFixed(8));
      return {event,payload:{value}};
    }
    return null;
  }
  function canPoint(asset){
    if(asset?.kind!=='composition')return false;
    if(['button','toggle'].includes(asset.behavior?.role))return Boolean(asset.behavior.on?.activate);
    return asset.behavior?.role==='slider'&&(asset.layers||[]).some(l=>l.position_from_input&&
      Object.values(asset.behavior.on||{}).some(actions=>actions.some(a=>a.op==='set'&&a.source==='event.value'&&a.input===l.position_from_input.input)));
  }
  // Editor-only audition of declared states, not host movement or combat logic.
  function previewStates(asset){
    if(asset?.kind==='state_set')return {input:'_state',values:Object.keys(asset.states),initial:asset.default_state};
    if(asset?.kind==='composition'&&asset.behavior?.role==='actor'){
      const key=(asset.layers||[]).map(l=>l.state_from_input).find(input=>asset.inputs?.[input]?.type==='enum');
      if(key)return {input:key,values:asset.inputs[key].values,initial:asset.inputs[key].default};
    }
    return null;
  }
  function previewStep(asset,current,command){
    const profile=previewStates(asset);
    if(!profile||!profile.values?.length||!['previous','next','reset'].includes(command))return null;
    const index=profile.values.indexOf(current);
    const value=command==='reset'?profile.initial:profile.values[(index<0?0:index+(command==='next'?1:-1)+profile.values.length)%profile.values.length];
    return {input:profile.input,value};
  }
  return Object.freeze({check,initial,dispatch,outputValues,pointerTarget,canPoint,previewStates,previewStep});
});
