"use strict";
/* Pure, bounded stat/action evaluator. Authored definitions are immutable; each
 * runtime owns only ephemeral values, active effects, and explicit simulation time.
 * No eval, time sources, DOM, network, or user-supplied executable functions.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  else root.VisualAtlasStats=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  const name=s=>typeof s==="string"&&/^[a-z][a-z0-9_]{0,63}$/.test(s);
  const idName=s=>typeof s==="string"&&/^[a-z][a-z0-9_.-]{0,127}$/.test(s);
  const object=v=>v!==null&&typeof v==="object"&&!Array.isArray(v);
  const finite=v=>typeof v==="number"&&Number.isFinite(v);
  const has=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
  const clamp=(v,min,max)=>Math.min(max,Math.max(min,v));
  const round=v=>Number(v.toFixed(8));
  const entries=o=>Object.entries(object(o)?o:{});
  function validate(profiles,getAsset){
    if(profiles===undefined)return [];
    if(!Array.isArray(profiles)||profiles.length>32)return ["Invalid stat profile collection"];
    const errors=[],ids=new Set();
    for(const p of profiles){
      if(!object(p)||p.schema!=="smi-stat-profile/1"||!idName(p.id)||ids.has(p.id)){
        errors.push("Invalid or duplicate stat profile "+p?.id);continue;
      }
      ids.add(p.id);
      const asset=getAsset(p.asset);
      if(!asset||asset.kind!=="composition"){
        errors.push(p.id+": stat target must be a composition");continue;
      }
      const stats=p.stats;
      if(!object(stats)||!Object.keys(stats).length||Object.keys(stats).length>32){
        errors.push(p.id+": invalid stats");continue;
      }
      for(const [key,d] of entries(stats)){
        if(!name(key)||!object(d)||!finite(d.min)||!finite(d.max)||!finite(d.initial)||
          d.max<=d.min||d.initial<d.min||d.initial>d.max||Math.max(Math.abs(d.min),Math.abs(d.max))>1e9)
          errors.push(p.id+": invalid stat "+key);
      }
      const derived=p.derived||{};
      if(!object(derived)||Object.keys(derived).length>16){
        errors.push(p.id+": invalid derived definitions");continue;
      }
      for(const [key,d] of entries(derived)){
        if(!name(key)||has(stats,key)||!object(d)||!finite(d.min)||!finite(d.max)||
           d.max<=d.min||!finite(d.offset)||Math.abs(d.offset)>1e9||
           !Array.isArray(d.terms)||!d.terms.length||d.terms.length>8){
          errors.push(p.id+": invalid derived "+key);continue;
        }
        const used=new Set();
        for(const term of d.terms){
          if(!object(term)||!has(stats,term.stat)||used.has(term.stat)||
             !finite(term.coefficient)||term.coefficient===0||Math.abs(term.coefficient)>1000)
            errors.push(p.id+": invalid derived term "+key+"/"+term?.stat);
          used.add(term?.stat);
        }
      }
      const effects=p.effects||{};
      if(!object(effects)||Object.keys(effects).length>16){
        errors.push(p.id+": invalid effects");continue;
      }
      for(const [key,d] of entries(effects)){
        if(!name(key)||!object(d)||!Number.isInteger(d.duration_ms)||d.duration_ms<1||d.duration_ms>600000||
          !Array.isArray(d.modifiers)||!d.modifiers.length||d.modifiers.length>8){
          errors.push(p.id+": invalid effect "+key);continue;
        }
        const used=new Set();
        for(const m of d.modifiers){
          if(!object(m)||!has(stats,m.stat)||used.has(m.stat)||
             (m.add===undefined&&m.multiply===undefined)||
             (m.add!==undefined&&(!finite(m.add)||Math.abs(m.add)>1e9))||
             (m.multiply!==undefined&&(!finite(m.multiply)||m.multiply<0||m.multiply>10))||
             ((m.add??0)===0&&(m.multiply??1)===1))
            errors.push(p.id+": invalid modifier "+key+"/"+m?.stat);
          used.add(m?.stat);
        }
      }
      const actions=p.actions;
      if(!object(actions)||!Object.keys(actions).length||Object.keys(actions).length>32){
        errors.push(p.id+": invalid actions");continue;
      }
      for(const [key,a] of entries(actions)){
        if(!name(key)||!object(a)){errors.push(p.id+": invalid action "+key);continue;}
        if(!entries(a.costs).length&&!entries(a.deltas).length&&!a.emit&&!a.activate&&!a.remove)
          errors.push(p.id+": empty action "+key);
        for(const [stat,cost] of entries(a.costs))
          if(!has(stats,stat)||!finite(cost)||cost<=0||cost>1e9)
            errors.push(p.id+": invalid cost "+key+"/"+stat);
        for(const [stat,delta] of entries(a.deltas))
          if(!has(stats,stat)||!finite(delta)||delta===0||Math.abs(delta)>1e9)
            errors.push(p.id+": invalid delta "+key+"/"+stat);
        if(a.emit!==undefined&&(!name(a.emit)||!has(asset.behavior?.on||{},a.emit)))
          errors.push(p.id+": unknown visual event "+key+"/"+a.emit);
        for(const field of ["activate","remove"]){
          if(a[field]!==undefined&&(!name(a[field])||!has(effects,a[field])))
            errors.push(p.id+": unknown effect "+key+"/"+a[field]);
        }
      }
      if(!Array.isArray(p.bindings)||!p.bindings.length||p.bindings.length>32){
        errors.push(p.id+": invalid stat bindings");continue;
      }
      const usedInput=new Set(),usedStat=new Set();
      for(const b of p.bindings){
        const d=stats[b?.stat]||derived[b?.stat],def=asset.inputs?.[b?.input];
        if(!d||def?.type!=="number"||usedInput.has(b.input)||usedStat.has(b.stat)||
           d.min<(def.min??0)||d.max>(def.max??1))
          errors.push(p.id+": invalid stat binding "+b?.stat+"/"+b?.input);
        usedInput.add(b?.input);usedStat.add(b?.stat);
      }
    }
    return errors;
  }

  function create(profile){
    const initial=()=>Object.fromEntries(entries(profile.stats).map(([id,d])=>[id,d.initial]));
    let values=initial(),remaining={};
    const snapshot=()=>({...values});
    function state(){
      const effective={};
      for(const [stat,def] of entries(profile.stats)){
        let add=0,multiply=1;
        // Defined ordering: additive modifiers first, then multiplicative.
        // Commutative aggregation is independent of activation order.
        for(const effectId of Object.keys(remaining).sort()){
          for(const m of profile.effects[effectId].modifiers){
            if(m.stat!==stat)continue;
            add+=m.add??0;
            multiply*=m.multiply??1;
          }
        }
        effective[stat]=round(clamp((values[stat]+add)*multiply,def.min,def.max));
      }
      const derived={};
      for(const [key,d] of entries(profile.derived)){
        const raw=(d.offset??0)+d.terms.reduce((sum,t)=>sum+effective[t.stat]*t.coefficient,0);
        derived[key]=round(clamp(raw,d.min,d.max));
      }
      return {base:snapshot(),effective,derived,
        effects:Object.keys(remaining).sort().map(id=>({id,remaining_ms:remaining[id]}))};
    }
    function set(stat,value){
      const d=profile.stats[stat];
      if(!d||!finite(value))throw Error("Invalid stat value "+stat);
      values={...values,[stat]:round(clamp(value,d.min,d.max))};
      return snapshot();
    }
    function apply(action){
      const rule=profile.actions[action];
      if(!rule)throw Error("Unknown stat action "+action);
      for(const [stat,cost] of entries(rule.costs)){
        if(values[stat]+1e-8<profile.stats[stat].min+cost)
          return {ok:false,reason:"Insufficient "+stat,values:snapshot(),events:[],state:state()};
      }
      const next={...values};
      for(const [stat,cost] of entries(rule.costs))next[stat]-=cost;
      for(const [stat,delta] of entries(rule.deltas))next[stat]+=delta;
      for(const [stat,d] of entries(profile.stats))next[stat]=round(clamp(next[stat],d.min,d.max));
      values=next;
      const events=[{type:"stat_action",name:action,values:snapshot()}];
      if(rule.remove&&has(remaining,rule.remove)){
        delete remaining[rule.remove];
        events.push({type:"effect_removed",name:rule.remove});
      }
      if(rule.activate){
        remaining[rule.activate]=profile.effects[rule.activate].duration_ms;
        events.push({type:"effect_activated",name:rule.activate});
      }
      if(rule.emit)events.push({type:"visual_event",name:rule.emit});
      return {ok:true,values:snapshot(),events,state:state()};
    }
    function advance(ms){
      if(!Number.isInteger(ms)||ms<0||ms>60000)throw Error("Simulation step must be 0..60000 ms");
      const expired=[];
      if(ms>0)for(const id of Object.keys(remaining)){
        const next=remaining[id]-ms;
        if(next<=0){delete remaining[id];expired.push(id);}
        else remaining[id]=next;
      }
      return {expired:expired.sort(),state:state()};
    }
    function reset(){values=initial();remaining={};return snapshot();}
    return Object.freeze({snapshot,state,set,apply,advance,reset});
  }
  return Object.freeze({validate,create});
});
