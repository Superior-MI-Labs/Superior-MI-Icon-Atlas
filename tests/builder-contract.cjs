'use strict';
// No external npm installs: exercises the exact JSZip shipped with the offline builder.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const JSZip=require('../web/vendor/jszip.min.js');
const root=path.resolve(__dirname,'..');
const expected=['region','sequence','composition','state_set'];
async function main(){
 const bytes=fs.readFileSync(path.join(root,'web/demo/starter-pack.zip'));
 const zip=await JSZip.loadAsync(bytes,{checkCRC32:true});
 const pack=JSON.parse(await zip.file('manifest.json').async('string'));
 assert.equal(pack.schema,'smi-visual-pack/1');
 const assetMap=new Map(pack.assets.map(a=>[a.id,a]));
 assert.equal(assetMap.size,pack.assets.length);
 for(const type of expected)assert.ok(pack.assets.some(a=>a.kind===type),'Missing demo kind: '+type);
 let cycles=0;const seen=new Set(),active=new Set();
 function visit(id){if(active.has(id)){cycles++;return;}if(seen.has(id))return;const a=assetMap.get(id);assert.ok(a,'Missing dependency '+id);active.add(id);
  const refs=a.kind==='sequence'?a.frames.map(f=>f.asset):a.kind==='composition'?a.layers.map(l=>l.asset):a.kind==='state_set'?Object.values(a.states):[];
  refs.forEach(visit);active.delete(id);seen.add(id);
 }
 for(const a of pack.assets){
  if(a.kind==='region'){const t=pack.textures[a.texture];assert.ok(t);const [x,y,w,h]=a.rect_px;assert.ok(x>=0&&y>=0&&w>0&&h>0&&x+w<=t.width_px&&y+h<=t.height_px);}
  if(a.kind==='sequence'){assert.ok(a.default_fps>0);assert.ok(a.frames.length>0);}
  if(a.kind==='state_set')assert.ok(a.states[a.default_state]);
  if(a.kind==='composition'){for(const layer of a.layers){for(const key of [layer.visible_when?.input,layer.clip?.input,layer.state_from_input,layer.position_from_input?.input].filter(Boolean))assert.ok(a.inputs?.[key],'Missing input '+key);}}
  visit(a.id);
 }
 assert.equal(cycles,0);
 for(const t of Object.values(pack.textures))assert.ok(zip.file(t.path),'Missing texture '+t.path);
 assert.ok(fs.existsSync(path.join(root,'web/vendor/JSZip-LICENSE.md')));
 const fileNames=Object.keys(zip.files).filter(x=>!zip.files[x].dir);
 assert.ok(fileNames.every(p=>!p.startsWith('/')&&!p.split('/').includes('..')));
 console.log('Visual pack ZIP contract: PASS; '+pack.assets.length+' assets, '+Object.keys(pack.textures).length+' texture(s)');
}
main().catch(e=>{console.error(e);process.exit(1)});
