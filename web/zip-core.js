'use strict';
/* Shared bounded archive reader for the public preview, private Builder and host engines. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;root.VisualAtlasZip=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
  const MAX_BYTES=120*1024*1024,MAX_ENTRY=24*1024*1024;
  const digestOK=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
  const immutablePath=digest=>'archives/sha256/'+digest+'.zip';
  function packLocator(pack){
    if(!pack||typeof pack.zip!=='string'||!/^demo\/[a-zA-Z0-9_-]+\.zip$/.test(pack.zip)||!digestOK(pack.archive_sha256))throw Error('Invalid published archive locator');
    const pin=immutablePath(pack.archive_sha256);
    if(pack.immutable_zip!==undefined&&pack.immutable_zip!==pin)throw Error('Immutable archive locator mismatch');
    return {path:pack.immutable_zip??pack.zip,archive_sha256:pack.archive_sha256};
  }
  // Resolve an explicit reference, not its entire semantic neighborhood. A pin
  // may point to a retained older archive; the ID must be verified after decode.
  function referenceLocator(index,reference){
    if(index?.schema!=='smi-public-catalog/1'||!Array.isArray(index.packs)||index.packs.length>1024||!Array.isArray(index.assets)||index.assets.length>50000||index.concepts!==undefined&&(!Array.isArray(index.concepts)||index.concepts.length>50000))throw Error('Invalid public catalog');
    if(!reference||!['concept','asset'].includes(reference.kind)||typeof reference.id!=='string'||reference.id.length<1||reference.id.length>256||reference.archive_sha256!==undefined&&!digestOK(reference.archive_sha256))throw Error('Invalid content reference');
    if(reference.archive_sha256){
      const pins=index.packs.filter(p=>!p.archived&&p.archive_sha256===reference.archive_sha256&&p.zip);
      if(pins.length){
        const locators=pins.map(packLocator);
        const preferred=locators.find(x=>x.path===immutablePath(reference.archive_sha256))||locators[0];
        return {...preferred,reference:{...reference}};
      }
      // A catalog advertising the digest route permits historical requests;
      // existence is not claimed until the archive is fetched and validated.
      const retained=index.packs.some(p=>!p.archived&&p.immutable_zip!==undefined&&packLocator(p).path===immutablePath(p.archive_sha256));
      return retained?{path:immutablePath(reference.archive_sha256),archive_sha256:reference.archive_sha256,reference:{...reference}}:null;
    }
    const records=reference.kind==='concept'?index.concepts||[]:index.assets.filter(a=>!a.legacy);
    const entries=records.filter(a=>a.id===reference.id);
    if(entries.length>1)throw Error('Ambiguous content reference '+reference.id);
    if(!entries.length)return null;
    const packs=index.packs.filter(p=>p.id===entries[0].pack&&!p.archived&&p.zip);
    if(packs.length!==1)throw Error('Missing or ambiguous content owner '+reference.id);
    return {...packLocator(packs[0]),reference:{...reference}};
  }
  async function fetchVerifiedArchive(locator,{base,fetcher=fetch,hash=null}={}){
    if(!locator||!digestOK(locator.archive_sha256)||typeof locator.path!=='string'||!(locator.path===immutablePath(locator.archive_sha256)||/^demo\/[a-zA-Z0-9_-]+\.zip$/.test(locator.path)))throw Error('Unsafe archive locator');
    const origin=new URL(base);
    if(!['http:','https:'].includes(origin.protocol)||origin.username||origin.password)throw Error('Invalid content provider URL');
    const url=new URL(locator.path,origin);
    if(url.origin!==origin.origin)throw Error('Archive origin mismatch');
    const response=await fetcher(url.href,{credentials:'omit',redirect:'error'});
    if(!response.ok)throw Error('Published archive unavailable');
    const declared=response.headers?.get('content-length');
    if(declared!==null&&declared!==undefined&&(!/^\d+$/.test(declared)||Number(declared)>MAX_BYTES))throw Error('ZIP exceeds import limit');
    if(!response.body?.getReader)throw Error('Bounded archive response unavailable');
    const reader=response.body.getReader(),chunks=[];let size=0;
    try{
      for(;;){const {done,value}=await reader.read();if(done)break;
        size+=value.byteLength;if(size>MAX_BYTES)throw Error('ZIP exceeds import limit');chunks.push(value);
      }
    }catch(e){await reader.cancel();throw e;}
    if(!size)throw Error('Empty archive response');
    const blob=new Blob(chunks,{type:'application/zip'});
    const actual=hash?await hash(blob):Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await blob.arrayBuffer())),n=>n.toString(16).padStart(2,'0')).join('');
    if(actual!==locator.archive_sha256)throw Error('Atlas archive SHA-256 mismatch');
    return blob;
  }
  async function readPublishedReference(locator,options){
    const blob=await fetchVerifiedArchive(locator,options);
    const result=await read(blob,options);
    const ref=locator.reference;
    if(!ref||!['concept','asset'].includes(ref.kind))throw Error('Missing requested content reference');
    const records=ref.kind==='concept'?result.resolved.pack.concepts||[]:result.resolved.pack.assets;
    const value=records.find(v=>v.id===ref.id);
    if(!value)throw Error('Requested content missing from exact archive: '+ref.id);
    return {...result,value};
  }
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
  return Object.freeze({read,packLocator,referenceLocator,fetchVerifiedArchive,readPublishedReference,MAX_BYTES,MAX_ENTRY});
});
