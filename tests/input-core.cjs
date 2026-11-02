'use strict';
const assert=require('node:assert/strict');
const Inputs=require('../web/input-core.js');
const levels=['empty','quarter','half','three_quarter','full'];
const asset={
  kind:'composition',
  inputs:{
    max:{type:'number',min:1,max:20,step:1,default:4},
    columns:{type:'number',min:1,max:20,step:1,default:10},
    value:{type:'number',min:0,max:80,step:1,default:12},
    color:{type:'enum',values:['ruby','amber'],default:'ruby'},
    active:{type:'boolean',default:false}
  },
  layers:[{asset:'test.hearts',repeat:{
    count_input:'max',columns_input:'columns',value_input:'value',levels,gap_px:[2,6]}}]
};
assert.deepEqual(Inputs.bounds(asset,'value',{max:4}),{min:0,max:16,step:1});
assert.deepEqual(Inputs.bounds(asset,'columns',{max:4}),{min:1,max:4,step:1});
const first=Inputs.reconcile(asset);
assert.equal(first.max,4);
assert.equal(first.columns,4);
assert.equal(first.value,12);
const large=Inputs.reconcile(asset,{max:20,columns:10,value:63});
assert.equal(large.max,20);
assert.equal(large.columns,10);
assert.equal(large.value,63);
const small=Inputs.reconcile(asset,{...large,max:1});
assert.equal(small.value,4);
assert.equal(small.columns,1);
assert.equal(small.max,1);
assert.equal(large.value,63,'Input reconciliation must not mutate prior state');
const invalid=Inputs.reconcile(asset,{max:999,columns:0,value:-9,color:'unknown',active:'yes'});
assert.equal(invalid.max,20);
assert.equal(invalid.columns,1);
assert.equal(invalid.value,0);
assert.equal(invalid.color,'ruby');
assert.equal(invalid.active,false);
const preset=Inputs.reconcile(asset,{}, {value:8,color:'amber',active:true});
assert.equal(preset.value,8);
assert.equal(preset.color,'amber');
assert.equal(preset.active,true);
const free={inputs:{value:{type:'number',min:10,max:100,default:30,step:0.5}}};
assert.equal(Inputs.reconcile(free,{value:120}).value,100);
assert.equal(Inputs.reconcile(free,{value:8}).value,10);
assert.deepEqual(Inputs.bounds(free,'value',{}),{min:10,max:100,step:0.5});
console.log('Shared input defaults, presets, capacity, columns and numeric bounds: PASS');
