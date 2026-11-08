"use strict";
/* Bounded, deterministic, declarative statistics. No eval, timers or DOM. */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.VisualAtlasStats=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  const name=s=>typeof s==='string'&&/^[a-z][a-z0-9_]{0,63}$/.test(s);
  const idName=s=>typeof s==='string'&&/^[a-z][a-z0-9_.-]{0,127}$/.test(s);
  const has=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
  const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
  const finite=v=>typeof v==='number'&&Number.isFinite(v);
  const clamp=(v,min,max)=>Math.min(max,Math.max(min,v));
  const rounded=v=>Number(v.toFixed(8));
  function validate(profiles,getAsset){
    if(profiles===undefined)return [];
    if(!Array.isArray(profiles)||profiles.length>32)return ['Invalid stat profile collection'];
    const errors=[],seen=new Set();
    for(const p of profiles){
      if(!object(p)||p.schema!=='smi-stat-profile/1'||!idName(p.id)||seen.has(p.id)){
        errors.push('Invalid or duplicate stat profile '+p?.id);continue;
      }
      seen.add(p.id);
      const asset=getAsset(p.asset);
      if(!asset||asset.kind!=='composition'){
        errors.push(p.id+': stat target must be a composition');continue;
      }
      if(!object(p.stats)||!Object.keys(p.stats).length||Object.keys(p.stats).length>32){
        errors.push(p.id+': invalid stats');continue;
      }
      for(const [key,d] of Object.entries(p.stats)){
        if(!name(key)||!object(d)||!finite(d.min)||!finite(d.max)||!finite(d.initial)||
           d.max<=d.min||d.initial<d.min||d.initial>d.max||Math.max(Math.abs(d.min),Math.abs(d.max))>1e9)
          errors.push(p.id+': invalid stat '+key);
      }
      if(!object(p.actions)||!Object.keys(p.actions).length||Object.keys(p.actions).length>32){
        errors.push(p.id+': invalid actions');continue;
      }
      for(const [key,action] of Object.entries(p.actions)){
        if(!name(key)||!object(action)){errors.push(p.id+': invalid action '+key);continue;}
        if(!Object.keys(action.costs||{}).length&&!Object.keys(action.deltas||{}).length&&!action.emit)
          errors.push(p.id+': empty action '+key);
        for(const [stat,cost] of Object.entries(action.costs||{}))
          if(!has(p.stats,stat)||!finite(cost)||cost<=0||cost>1e9)errors.push(p.id+': invalid cost '+key+'/'+stat);
        for(const [stat,delta] of Object.entries(action.deltas||{}))
          if(!has(p.stats,stat)||!finite(delta)||delta===0||Math.abs(delta)>1e9)errors.push(p.id+': invalid delta '+key+'/'+stat);
        if(action.emit!==undefined&&(!name(action.emit)||!has(asset.behavior?.on||{},action.emit)))
          errors.push(p.id+': unknown visual event '+key+'/'+action.emit);
      }
      if(!Array.isArray(p.bindings)||!p.bindings.length||p.bindings.length>32){
        errors.push(p.id+': invalid stat bindings');continue;
      }
      const used=new Set(),boundStats=new Set();
      for(const bind of p.bindings){
        const def=asset.inputs?.[bind?.input],stat=p.stats[bind?.stat];
        if(!stat||def?.type!=='number'||used.has(bind.input)||stat.min<(def.min??0)||stat.max>(def.max??1))
          errors.push(p.id+': invalid stat-to-visual binding '+bind?.stat+'/'+bind?.input);
        used.add(bind?.input);boundStats.add(bind?.stat);
      }
    }
    return errors;
  }
  function create(profile){
    const initial=()=>Object.fromEntries(Object.entries(profile.stats).map(([key,d])=>[key,d.initial]));
    let values=initial();
    const snapshot=()=>({...values});
    function set(stat,value){
      const d=profile.stats[stat];
      if(!d||!finite(value))throw Error('Invalid stat value '+stat);
      values={...values,[stat]:rounded(clamp(value,d.min,d.max))};
      return snapshot();
    }
    function apply(action){
      const effect=profile.actions[action];
      if(!effect)throw Error('Unknown stat action '+action);
      for(const [stat,cost] of Object.entries(effect.costs||{}))
        if(values[stat]+1e-8<profile.stats[stat].min+cost)
          return {ok:false,reason:'Insufficient '+stat,values:snapshot(),events:[]};
      const next={...values};
      for(const [stat,cost] of Object.entries(effect.costs||{}))next[stat]-=cost;
      for(const [stat,delta] of Object.entries(effect.deltas||{}))next[stat]+=delta;
      for(const [stat,d] of Object.entries(profile.stats))next[stat]=rounded(clamp(next[stat],d.min,d.max));
      values=next;
      return {ok:true,values:snapshot(),events:[{type:'stat_action',name:action,values:snapshot()},...(effect.emit?[{type:'visual_event',name:effect.emit}]:[])]};
    }
    function reset(){values=initial();return snapshot();}
    return Object.freeze({snapshot,set,apply,reset});
  }
  return Object.freeze({validate,create});
});
