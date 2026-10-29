'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');
const JSZip=require('../web/vendor/jszip.min.js');
const C=require('../web/collection-core.js');const Slots=require('../web/slot-core.js');
async function run(){
 const buffer=fs.readFileSync(path.join(__dirname,'../web/demo/potions-collection.zip'));
 const z=await JSZip.loadAsync(buffer,{checkCRC32:true});
 const index=JSON.parse(await z.file('collection.json').async('string'));
 const defs=[];
 for(const item of index.packs)defs.push({path:item.manifest,pack:JSON.parse(await z.file(item.manifest).async('string'))});
 const resolved=C.resolveCollection(index,defs);
 assert.equal(resolved.bag.groups.length,2);
 assert.equal(resolved.bag.entry,'smi.potion.bottle');
 assert.deepEqual(Slots.validate(resolved.pack),[]);
 const a=resolved.pack.assets.find(x=>x.id==='smi.potion.bottle');
 assert.equal(Slots.resolve(a).slots.fluid,'smi.fluid.green');
 assert.equal(Slots.resolve(a,'Mana').slots.fluid,'smi.fluid.mana');
 assert.equal(Slots.resolve(a,'Poison').slots.fluid,'smi.fluid.poison');
 assert.equal(Slots.resolve(a,'Mana',{fluid:'smi.fluid.green'}).slots.fluid,'smi.fluid.green');
 assert.throws(()=>Slots.resolve(a,'Mana',{fluid:'smi.unknown'}),/Incompatible slot/);
 assert.equal(Slots.refs(a).length,5); // base, glass, 3 permitted fluids
 assert.ok(Slots.refs(a).includes('smi.fluid.mana'));
 const copy=()=>JSON.parse(JSON.stringify(resolved.pack));
 const bad=copy();bad.assets.find(x=>x.id==='smi.potion.bottle').slots.fluid.options.push('smi.potion.base');
 assert.match(Slots.validate(bad).join('\n'),/does not implement/);
 const noContract=copy();delete noContract.interfaces['smi.slot.potion.fluid.96x96/1'];
 assert.match(Slots.validate(noContract).join('\n'),/undeclared interface|unknown interface/);
 const incompatible=copy();incompatible.assets.find(x=>x.id==='smi.fluid.green').rect_px=[0,0,60,60];
 assert.match(Slots.validate(incompatible).join('\n'),/incompatible size/);
 const badPreset=copy();badPreset.assets.find(x=>x.id==='smi.potion.bottle').presets.Mana.slots.fluid='smi.unknown';
 assert.match(Slots.validate(badPreset).join('\n'),/invalid option/);
 const badVersion=copy();const def=badVersion.interfaces['smi.slot.potion.fluid.96x96/1'];delete badVersion.interfaces['smi.slot.potion.fluid.96x96/1'];badVersion.interfaces['smi.slot.potion.fluid.96x96/2']=def;
 assert.match(Slots.validate(badVersion).join('\n'),/undeclared interface|unknown interface/);
 // Presets never change base image identity or manifest dependencies.
 for(const preset of ['Health','Mana','Poison'])assert.equal(a.layers.find(x=>x.id==='base').asset,'smi.potion.base');
 console.log('Compatibility slots / presets: PASS; two manifests, static+animated compatible fluid options, invalid substitutions rejected');
}
run().catch(e=>{console.error(e);process.exit(1)});
