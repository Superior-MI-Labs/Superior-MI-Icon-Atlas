const assert=require('node:assert/strict');
const Z=require('../web/zip-core.js');
const C=require('../web/collection-core.js');
const JSZip=require('../web/vendor/jszip.min.js');
(async()=>{
  const pack={schema:'smi-visual-pack/1',pack_id:'test.pack',version:'1',license:'CC0-1.0',textures:{t:{path:'textures/a.png',width_px:1,height_px:1}},assets:[{id:'a',kind:'region',texture:'t',rect_px:[0,0,1,1]}]};
  const make=async({missing=false,traversal=false}={})=>{const z=new JSZip();z.file('nested/manifest.json',JSON.stringify(pack));if(!missing)z.file('nested/textures/a.png','fixture');z.file('collection.json',JSON.stringify({schema:'smi-visual-collection/1',collection_id:'test',packs:[{manifest:'nested/manifest.json'}],entry_asset:'a'}));if(traversal)z.file('../escape.txt','bad',{createFolders:false});const bytes=await z.generateAsync({type:'nodebuffer'});return {size:bytes.length,bytes};};
  // Node JSZip accepts buffers; the browser reader's Blob-size contract is preserved.
  const loader={loadAsync:(file,opts)=>JSZip.loadAsync(file.bytes,opts)};
  const options={JSZip:loader,Collections:C};
  const r=await Z.read(await make(),options);assert.equal(r.resolved.pack.textures.p0_t.path,'nested/textures/a.png');
  await assert.rejects(()=>make({missing:true}).then(f=>Z.read(f,options)),/Missing source texture/);
  await assert.rejects(()=>make({traversal:true}).then(f=>Z.read(f,options)),/Unsafe/);
  await assert.rejects(()=>Z.read({size:Z.MAX_BYTES+1},options),/limit/);
  console.log('Shared ZIP resolution and bounds PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
