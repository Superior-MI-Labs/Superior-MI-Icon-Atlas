'use strict';
const assert=require('node:assert/strict'),Slots=require('../web/slot-core.js');
const root={id:'root',kind:'state_set',states:{closed:'c0',open:'o0'},default_state:'closed',spatial:{views:{elevation_deg:35.264,assets:['root','v1','v2','v3','v4','v5']}}};
assert.deepEqual(Slots.viewOptions(root).map(v=>v.yaw),[0,60,120,180,240,300]);
assert.equal(Slots.viewId(root,0),'root');assert.equal(Slots.viewId(root,-1),'v5');assert.equal(Slots.viewId(root,6),'root');
assert.equal(Slots.viewId(root,NaN),'root');assert.equal(Slots.viewId({id:'static'},3),'static');assert.equal(Slots.viewId(null),undefined);
for(const n of [4,8]){const a={...root,spatial:{views:{elevation_deg:45,assets:Array.from({length:n},(_,i)=>i?'v'+i:'root')}}};assert.equal(Slots.viewOptions(a).length,n);assert.equal(Slots.viewOptions(a).at(-1).yaw,360-360/n);}
const a={...root,concept_id:'chest',variant:'wood'},b={id:'iron',kind:'state_set',concept_id:'chest',variant:'iron'};
assert.deepEqual(Slots.variantOptions(a,[a,b,{...b,id:'hidden',discovery:'hidden'},{...b,id:'different',kind:'region'},{...b,id:'other',concept_id:'barrel'},{...b,id:'v1'}]).map(v=>v.id),['iron','root']);
assert.deepEqual(Slots.variantOptions(a,[a]),[]);assert.deepEqual(Slots.variantOptions(root,[b]),[]);
assert.deepEqual(Slots.spatialRefs(root),['v1','v2','v3','v4','v5']);
assert.equal(root.states.open,'o0');assert.equal(root.spatial.views.assets[0],'root');
console.log('Authored direction and explicit variants: PASS');
