'use strict';
// Integration test: run against the actual reconciled collection resolver.
// This is not part of the isolated harness; native repo CI is required.
const assert=require('node:assert/strict');
const C=require('../web/collection-core.js');
const concept={schema:'smi-concept/1',id:'test.dark',name:'Dark enhancement',license:'CC0-1.0',discovery_offers:{apply:{role:'enhancement',requirements:[{scope:'concept',op:'capability.has',key:'enchantable'}]}}};
const asset={id:'test.dark.icon',concept_id:concept.id,kind:'region',texture:'t',rect_px:[0,0,1,1]};
const pack={schema:'smi-visual-pack/1',pack_id:'test.discovery',version:'1.0.0',license:'CC0-1.0',textures:{t:{path:'sheet.png',width_px:1,height_px:1}},assets:[asset],concepts:[concept]};
(async()=>{
 const resolved=C.resolveCollection(null,[{path:'manifest.json',pack}]).pack;
 assert.deepEqual(resolved.concepts,[concept]);
 const bad=structuredClone(pack);bad.concepts[0].discovery_offers.apply.requirements[0].op='exec';
 assert.throws(()=>C.resolveCollection(null,[{path:'manifest.json',pack:bad}]),/discovery requirement/);
 const files=new Map(),zip={file:(k,v)=>files.set(k,v)};
 const selected=await C.writeSelection(zip,{assets:resolved.assets,rootId:asset.id,packId:'test.export',getTexture:async()=>({blob:new Blob(['fixture']),width_px:1,height_px:1,path:'sheet.png'}),getInterfaces:()=>({}),concepts:resolved.concepts});
 assert.deepEqual(selected.concepts,[concept]);
 assert.equal(selected.assets.length,1);
 const re=C.resolveCollection(null,[{path:'manifest.json',pack:JSON.parse(files.get('manifest.json'))}]).pack;
 assert.deepEqual(re.concepts,[concept]);
 console.log('Capability offer archive roundtrip PASS');
})().catch(e=>{console.error(e);process.exitCode=1;});
