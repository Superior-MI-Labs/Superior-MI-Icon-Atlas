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


// Deterministic effects and derived values share the existing stat runtime.
const h=Stats.create(energy);
assert.equal(h.state().derived.readiness,56); // 72*.5 + 5*4
const focus=h.apply('focus');
assert.equal(focus.ok,true);
assert.equal(focus.state.base.energy,62,'cost changes only base');
assert.equal(focus.state.effective.energy,72,'modifier adds 10 without altering base');
assert.equal(focus.state.derived.readiness,56,'derived uses effective values');
assert.equal(h.advance(1000).state.effects[0].remaining_ms,2000);
assert.equal(h.apply('focus').state.effects[0].remaining_ms,3000,'reapplication refreshes, does not stack');
assert.equal(h.advance(2999).state.effects[0].remaining_ms,1);
assert.deepEqual(h.advance(1).expired,['focus']);
assert.equal(h.state().effective.energy,52,'expired modifier drops without changing base');
assert.deepEqual(h.advance(1000).expired,[],'expired effect fires only once');
assert.throws(()=>h.advance(-1),/step/);
assert.throws(()=>h.advance(60001),/step/);
assert.throws(()=>h.advance(0.5),/step/);
assert.equal(h.apply('dispel_focus').ok,true,'remove inactive effect is harmless');
const activated=h.apply('focus');
assert.ok(activated.state.effects.length);
assert.ok(h.apply('dispel_focus').state.effects.length===0);
h.reset();
assert.equal(h.state().effects.length,0,'reset clears all effects');
assert.equal(h.state().derived.readiness,56);

const mobility=Stats.create(p);
assert.equal(mobility.state().derived.mobility,11);
assert.equal(mobility.apply('haste').state.effective.speed,6);
assert.equal(mobility.state().derived.mobility,14.5,'read-only formula uses effective stats');
assert.equal(mobility.state().base.speed,4,'effect does not change base speed');
assert.equal(mobility.advance(3000).state.derived.mobility,10.5);
assert.equal(mobility.state().base.stamina,50,'time advances do not regenerate resources');
assert.ok(Stats.validate([{...p,derived:{mobility:{...p.derived.mobility,terms:[{stat:'unknown',coefficient:2}]}}}],id=>actor).length);
assert.ok(Stats.validate([{...p,derived:{mobility:{...p.derived.mobility,terms:[{stat:'stamina',coefficient:2},{stat:'stamina',coefficient:1}]}}}],id=>actor).length);
assert.ok(Stats.validate([{...p,effects:{haste:{...p.effects.haste,modifiers:[{stat:'unknown',multiply:2}]}}}],id=>actor).length);
assert.ok(Stats.validate([{...p,actions:{haste:{activate:'not_defined'}}}],id=>actor).length);
assert.ok(Stats.validate([{...p,derived:{speed:p.derived.mobility}}],id=>actor).length);
assert.ok(Stats.validate([{...p,bindings:[...p.bindings,{stat:'mobility',input:'mobility'}]}],id=>actor).length);
console.log('Derived, modifier, effect expiry, refresh and semantic regression PASS');
