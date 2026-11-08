'use strict';
const assert=require('node:assert/strict');
const I=require('../web/interaction-core.js'), Inputs=require('../web/input-core.js');
const slider={id:'test.slider',kind:'composition',size_px:[328,56],inputs:{value:{type:'number',min:0,max:100,step:1,default:50}},
  behavior:{role:'slider',outputs:{value:{from_input:'value'}},on:{set_value:[{op:'set',input:'value',source:'event.value'}]}},
  layers:[{id:'thumb',asset:'test.thumb',offset_px:[0,0],position_from_input:{input:'value',axis:'x',from_px:0,to_px:276}}]};
const size=()=>[52,56];
assert.equal(I.canPoint(slider),true);
for(const [x,value] of [[26,0],[164,50],[302,100],[1000,100]]) {
  const a=I.pointerTarget(slider,{x,y:28},size,x===1000);
  assert.equal(a?.event,'set_value');
  assert.equal(I.dispatch(slider,{},a.event,a.payload).values.value,value);
}
assert.equal(I.pointerTarget(slider,{x:164,y:300},size),null,'off-track press must not activate');
assert.equal(I.pointerTarget(slider,{x:164,y:300},size,true).payload.value,50,'captured drag continues outside track');
const vertical={...slider,layers:[{asset:'test.thumb',position_from_input:{input:'value',axis:'y',from_px:276,to_px:0}}]};
assert.equal(I.pointerTarget(vertical,{x:26,y:26},size).payload.value,100);
assert.equal(I.pointerTarget(vertical,{x:26,y:304},size).payload.value,0);
const toggle={kind:'composition',size_px:[100,40],behavior:{role:'toggle',on:{activate:[{op:'toggle',input:'enabled'}]}},inputs:{enabled:{type:'boolean',default:false}}};
assert.equal(I.dispatch(toggle,{},I.pointerTarget(toggle,{x:30,y:20}).event).values.enabled,true);
assert.equal(I.pointerTarget(toggle,{x:101,y:20}),null);
assert.equal(I.canPoint({kind:'region'}),false);
const states={kind:'state_set',default_state:'idle',states:{idle:'a',walk:'b',run:'c'}};
assert.deepEqual(I.previewStep(states,'idle','next'),{input:'_state',value:'walk'});
assert.equal(I.previewStep(states,'idle','previous').value,'run');
assert.equal(I.previewStep(states,'run','reset').value,'idle');
const actor={kind:'composition',behavior:{role:'actor'},inputs:{animation:{type:'enum',default:'idle',values:['idle','block']}},layers:[{state_from_input:'animation',asset:'state_set'}]};
assert.deepEqual(I.previewStep(actor,'idle','next'),{input:'animation',value:'block'});
assert.equal(I.previewStep({kind:'region'},'','next'),null);
assert.equal(Inputs.reconcile(slider,I.dispatch(slider,{},'set_value',{value:25}).values).value,25);
console.log('Direct preview pointer geometry, drag capture, typed dispatch and state audition: PASS');
