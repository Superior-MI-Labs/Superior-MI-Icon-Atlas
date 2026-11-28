'use strict';
const assert=require('node:assert/strict');
const C=require('../web/collection-core.js');
const potion=require('./fixtures/concept-potion.json');
const copy=()=>structuredClone(potion);
const pack=(id,concepts,linked=true)=>({schema:'smi-visual-pack/1',pack_id:id,version:'1',license:'CC0-1.0',textures:{t:{path:'image.png',width_px:1,height_px:1}},assets:[{id:id+'.icon',kind:'region',texture:'t',rect_px:[0,0,1,1],...(linked?{concept_id:potion.id}:{})}],...(concepts===undefined?{}:{concepts})});
const defs=[{path:'a/manifest.json',pack:pack('a',[potion])},{path:'b/manifest.json',pack:pack('b')}];
assert.deepEqual(C.resolveCollection(null,defs).pack.concepts,[potion]);
assert.equal(C.resolveCollection(null,[defs[1]]).pack.concepts,undefined);
assert.throws(()=>C.resolveCollection(null,[{path:'a/manifest.json',pack:pack('a',[potion],false)}]),/Unreferenced concept/);
assert.throws(()=>C.resolveCollection(null,[defs[0],{path:'b/manifest.json',pack:pack('b',[potion])}]),/Duplicate concept/);
for(const modify of [p=>p.physical.height_m=-1,p=>p.physical.width_ft=2,p=>p.defaults['unversioned']={},p=>p.defaults['smi.rules.d20/1']['health.restore'].count=0,p=>p.defaults['smi.rules.d20/1']['health.restore'].modifier=0.5,p=>p.defaults['smi.rules.flat/1']['health.restore'].value=Infinity,p=>p.defaults['smi.rules.inventory/1']['consume.return_container'].value='true',p=>p.script='alert(1)']){
  const p=copy();modify(p);assert.throws(()=>C.validateConcepts([p]));
}
const d20='smi.rules.d20/1',flat='smi.rules.flat/1',actions='smi.rules.action-economy/1',inv='smi.rules.inventory/1';
assert.deepEqual(C.resolveDefaults(potion,[d20,actions]),{...potion.defaults[d20],...potion.defaults[actions]});
assert.deepEqual(C.resolveDefaults(potion,[]),{});
assert.throws(()=>C.resolveDefaults(potion,[d20,flat]),/Conflicting/);
assert.throws(()=>C.resolveDefaults(potion,['unknown/1']),/Unknown ruleset/);
assert.throws(()=>C.resolveDefaults(potion,[d20,d20]),/Invalid ruleset/);
assert.throws(()=>C.resolveDefaults(potion,[d20],{'health.restore':{kind:'quantity',value:8,unit:'kg'}}),/Incompatible override/);
assert.throws(()=>C.resolveDefaults(potion,[d20],{'missing':{kind:'quantity',value:8,unit:'hp'}}),/Unknown override/);
const overridden=C.resolveDefaults(potion,[d20,inv],{'health.restore':{kind:'quantity',value:8,unit:'hp'},'consume.return_container':{kind:'boolean',value:false}});
assert.equal(overridden['health.restore'].value,8);
assert.equal(overridden['consume.return_container'].value,false);
assert.equal(potion.defaults[d20]['health.restore'].count,2);
(async()=>{
  const files=new Map(),zip={file:(k,v)=>files.set(k,v)};
  const resolved=C.resolveCollection(null,defs).pack;
  const asset=resolved.assets[1];
  const manifest=await C.writeSelection(zip,{assets:[asset],rootId:asset.id,packId:'selection',getTexture:async()=>({blob:new Blob(['png']),width_px:1,height_px:1,path:'x.png'}),getInterfaces:()=>({}),concepts:[{...potion,ownerBag:'private'}]});
  assert.deepEqual(manifest.concepts,[potion]);
  assert.match(files.get('SOURCE-NOTICES.txt'),/smi.item.potion.health.basic : CC0-1.0/);
  assert.deepEqual(C.resolveCollection(null,[{path:'manifest.json',pack:JSON.parse(files.get('manifest.json'))}]).pack.concepts,[potion]);
  const unlinked={...asset};delete unlinked.concept_id;
  const minimal=await C.writeSelection(zip,{assets:[unlinked],rootId:unlinked.id,packId:'selection2',getTexture:async()=>({blob:new Blob(['png']),width_px:1,height_px:1}),getInterfaces:()=>({}),concepts:[potion]});
  assert.equal(minimal.concepts,undefined);
  console.log('Concept defaults, conflict rejection, and selected export round-trip PASS');
})().catch(e=>{console.error(e);process.exitCode=1;});
