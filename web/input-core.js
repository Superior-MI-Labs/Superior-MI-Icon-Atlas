'use strict';
/* Pure numeric/input contract shared by catalog and private builder.
 * The manifest owns defaults and ranges; dynamic repeat capacity is derived.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  root.VisualAtlasInputs=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  const clamp=(n,min,max)=>Math.max(min,Math.min(max,n));
  function defaults(asset,presetInputs={}){
    return {...Object.fromEntries(Object.entries(asset.inputs||{}).map(([key,def])=>[key,def.default])),...presetInputs};
  }
  function bounds(asset,key,values={}){
    const def=asset.inputs?.[key];
    if(!def||def.type!=='number')return null;
    const min=def.min??0;
    let max=def.max??1;
    for(const layer of asset.layers||[]){
      const repeat=layer.repeat;
      if(!repeat)continue;
      if(repeat.value_input!==key&&repeat.columns_input!==key)continue;
      const countDef=asset.inputs?.[repeat.count_input];
      const raw=Number(values[repeat.count_input]??countDef?.default);
      const count=Number.isFinite(raw)?Math.max(1,Math.floor(clamp(raw,countDef?.min??1,countDef?.max??256))):1;
      const cap=repeat.value_input===key?count*(repeat.levels.length-1):count;
      max=Math.min(max,cap);
    }
    return {min,max:Math.max(min,max),step:def.step??1};
  }
  function reconcile(asset,values={},presetInputs={}){
    const merged={...defaults(asset,presetInputs),...values};
    // First clamp author-declared ranges, then derive repeat-dependent limits.
    for(const [key,def] of Object.entries(asset.inputs||{})){
      if(def.type==='number'){
        const value=Number(merged[key]);
        merged[key]=clamp(Number.isFinite(value)?value:def.default,def.min??0,def.max??1);
      }else if(def.type==='boolean'){
        if(typeof merged[key]!=='boolean')merged[key]=def.default;
      }else if(def.type==='enum'&&!def.values?.includes(merged[key])){
        merged[key]=def.default;
      }
    }
    for(const [key,def] of Object.entries(asset.inputs||{})){
      if(def.type==='number'){
        const limit=bounds(asset,key,merged);
        merged[key]=clamp(merged[key],limit.min,limit.max);
      }
    }
    return merged;
  }
  return Object.freeze({defaults,bounds,reconcile});
});
