'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const Stats=require('../web/stat-core.js'),I=require('../web/interaction-core.js'),Collection=require('../web/collection-core.js');
const read=p=>JSON.parse(fs.readFileSync(path.join(__dirname,'..',p),'utf8'));
const hud=read('examples/interactive-hud/manifest.json'),robot=read('examples/character-animations/manifest.json');
for(const pack of [hud,robot]){
  assert.deepEqual(Stats.validate(pack.stat_profiles,id=>pack.assets.find(a=>a.id===id)),[]);
  const combined=Collection.resolveCollection(null,[{path:'manifest.json',pack}],'stat pack');
  assert.deepEqual(combined.pack.stat_profiles,pack.stat_profiles,'collection retains authored profiles');
}
const energy=hud.stat_profiles[0],lab=Stats.create(energy);
assert.deepEqual(lab.snapshot(),{energy:72,speed:5});
assert.equal(lab.apply('dash').values.energy,52);
assert.equal(lab.apply('dash').values.energy,32);
assert.equal(lab.apply('dash').values.energy,12);
const before=lab.snapshot(),denied=lab.apply('dash');
assert.equal(denied.ok,false);assert.match(denied.reason,/Insufficient energy/);
assert.deepEqual(denied.values,before);assert.deepEqual(denied.events,[]);
assert.equal(lab.apply('restore').values.energy,27);
assert.equal(lab.apply('hit').values.energy,0,'damage clamped to min');
lab.set('energy',98);assert.equal(lab.apply('restore').values.energy,100,'restore clamped to max');
lab.set('speed',100);assert.equal(lab.snapshot().speed,10);
assert.throws(()=>lab.set('speed',NaN),/Invalid stat/);
assert.throws(()=>lab.apply('missing'),/Unknown stat action/);
assert.deepEqual(lab.reset(),{energy:72,speed:5});
assert.deepEqual(Stats.create(energy).snapshot(),{energy:72,speed:5},'no shared runtime state');
const p=robot.stat_profiles[0],sim=Stats.create(p),actor=robot.assets.find(a=>a.id===p.asset);
let visual={animation:'idle',stamina:60};
for(const action of ['dash','recover']){
  const result=sim.apply(action);
  assert.equal(result.ok,true);
  const e=result.events.find(e=>e.type==='visual_event');
  visual=I.dispatch(actor,visual,e.name).values;
  for(const b of p.bindings)visual[b.input]=result.values[b.stat];
  assert.equal(visual.animation,action==='dash'?'walk':'idle');
  assert.equal(visual.stamina,action==='dash'?40:65);
}
assert.ok(Stats.validate([{...energy,actions:{dash:{costs:{unknown:3}}}}],id=>hud.assets.find(a=>a.id===id)).length);
assert.ok(Stats.validate([{...energy,bindings:[{stat:'energy',input:'unknown'}]}],id=>hud.assets.find(a=>a.id===id)).length);
assert.ok(Stats.validate([{...energy,stats:{energy:{min:0,max:100,initial:150}}}],id=>hud.assets.find(a=>a.id===id)).length);
assert.ok(Stats.validate([{...p,actions:{dash:{emit:'not_declared'}}}],id=>robot.assets.find(a=>a.id===id)).length);
assert.ok(Stats.validate([energy,energy],id=>hud.assets.find(a=>a.id===id)).length);
console.log('Stat core/collection round-trip + event integration PASS');
