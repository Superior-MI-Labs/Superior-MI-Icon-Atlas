"use strict";
/* Declarative visual input normalization. Shared by preview renderer and Node QA. */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  root.VisualAtlasVisualCore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  function unitValue(asset, values, key){
    const spec=asset?.inputs?.[key];
    const numeric=Number(values?.[key]);
    if(!Number.isFinite(numeric)) return 0;
    if(spec?.type==='number' && Number.isFinite(spec.min) && Number.isFinite(spec.max)){
      if(spec.max<=spec.min) return 0; // invalid range handled by manifest QA
      return Math.min(1,Math.max(0,(numeric-spec.min)/(spec.max-spec.min)));
    }
    return Math.min(1,Math.max(0,numeric));
  }
  return Object.freeze({unitValue});
});
