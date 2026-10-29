"use strict";
/* Optional, explicitly selected local-only persistence. No cloud or network access. */
(function(root,factory){
  const api=factory(root);
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.VisualAtlasBagStore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(host){
  const DB_NAME='smi-visual-atlas-bag-v1', STORE='archives';
  function open(){return new Promise((resolve,reject)=>{
    if(!host.indexedDB)return reject(Error('IndexedDB is unavailable in this browser'));
    const request=host.indexedDB.open(DB_NAME,1);
    request.onupgradeneeded=()=>{const db=request.result;if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE,{keyPath:'id'});};
    request.onsuccess=()=>resolve(request.result);
    request.onerror=()=>reject(request.error||Error('Could not open local bag storage'));
  });}
  async function execute(mode,operation){
    const db=await open();
    try{return await new Promise((resolve,reject)=>{
      const tx=db.transaction(STORE,mode),store=tx.objectStore(STORE),req=operation(store);
      let answer;
      req.onsuccess=()=>{answer=req.result;};req.onerror=()=>reject(req.error||Error('Local bag storage operation failed'));
      tx.oncomplete=()=>resolve(answer);
      tx.onerror=()=>reject(tx.error||Error('Local bag storage transaction failed'));
      tx.onabort=()=>reject(tx.error||Error('Local bag storage transaction aborted'));
    });}finally{db.close();}
  }
  return Object.freeze({
    put:({id,name,file})=>execute('readwrite',store=>store.put({id,name,file,savedAt:Date.now()})),
    list:()=>execute('readonly',store=>store.getAll()),
    remove:id=>execute('readwrite',store=>store.delete(id)),
    clear:()=>execute('readwrite',store=>store.clear())
  });
});
