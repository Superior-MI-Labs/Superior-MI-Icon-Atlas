'use strict';
/* Shared bounded archive reader for the public preview, private Builder and host engines. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;root.VisualAtlasZip=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
  const MAX_BYTES=120*1024*1024,MAX_ENTRY=24*1024*1024;
  async function read(file,{JSZip,Collections,name='Imported assets'}){
    if(!JSZip||!Collections)throw Error('Missing ZIP or collection resolver');
    if(!file||!Number.isSafeInteger(file.size)||file.size>MAX_BYTES)throw Error('ZIP exceeds 120 MB import limit');
    const zip=await JSZip.loadAsync(file,{checkCRC32:false});
    const entries=Object.values(zip.files).filter(e=>!e.dir);
    if(entries.length>4000)throw Error('Too many ZIP entries');
    let expanded=0;const names=new Set();
    for(const e of entries){
      if(!Collections.safePath(e.name)||names.has(e.name)||(e.unsafeOriginalName!==undefined&&e.unsafeOriginalName!==e.name))throw Error('Unsafe or duplicate ZIP path: '+e.name);
      names.add(e.name);
      const bytes=e._data?.uncompressedSize;
      if(!Number.isSafeInteger(bytes)||bytes<0||bytes>MAX_ENTRY)throw Error('Invalid or oversized ZIP member: '+e.name);
      expanded+=bytes;if(expanded>MAX_BYTES)throw Error('ZIP exceeds 120 MB expanded-size limit');
    }
    await JSZip.loadAsync(file,{checkCRC32:true});
    const manifests=[];let index=null,indexDir='';
    for(const e of entries.filter(e=>/\.json$/i.test(e.name))){
      let parsed;try{parsed=JSON.parse(await e.async('string'));}catch{continue;}
      if(parsed?.schema==='smi-visual-pack/1')manifests.push({path:e.name,pack:parsed});
      if(parsed?.schema==='smi-visual-collection/1'){
        if(index)throw Error('Archive has multiple collection indexes');
        index=parsed;indexDir=e.name.includes('/')?e.name.slice(0,e.name.lastIndexOf('/')):'';
      }
    }
    if(!manifests.length)throw Error('No smi-visual-pack/1 manifest found');
    if(index)index={...index,packs:index.packs.map(p=>({...p,manifest:Collections.join(indexDir,p.manifest)}))};
    const resolved=Collections.resolveCollection(index,manifests,name);
    for(const t of Object.values(resolved.pack.textures))if(!zip.file(t.path))throw Error('Missing source texture: '+t.path);
    return {zip,entries,resolved};
  }
  return Object.freeze({read,MAX_BYTES,MAX_ENTRY});
});
