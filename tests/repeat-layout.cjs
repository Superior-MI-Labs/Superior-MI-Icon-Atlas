"use strict";
const assert=require('node:assert/strict');
const {create}=require('../web/asset-renderer.js');
const P='fixture.';
const levels=['empty','quarter','half','three_quarter','full'];
const assets=new Map(levels.map((state,i)=>[P+'heart.'+state,{
  id:P+'heart.'+state,kind:'region',rect_px:[i*72,0,72,72],texture:'sheet'}]));
assets.set(P+'heart.states',{id:P+'heart.states',kind:'state_set',states:Object.fromEntries(levels.map(x=>[x,P+'heart.'+x])),default_state:'full'});
assets.set(P+'hearts',{id:P+'hearts',kind:'composition',size_px:[738,150],
  inputs:{max:{type:'number',min:1,max:20,default:4},columns:{type:'number',min:1,max:20,default:10},value:{type:'number',min:0,max:80,default:12}},
  layers:[{id:'hearts',asset:P+'heart.states',repeat:{
    count_input:'max',columns_input:'columns',value_input:'value',levels,gap_px:[2,6]}}]});
assets.set(P+'static',{id:P+'static',kind:'composition',size_px:[72,72],layers:[{id:'single',asset:P+'heart.full'}]});
const logs=[];
const ctx={save(){},restore(){},translate(){},scale(){},beginPath(){},rect(){},clip(){},fillRect(){},drawImage(_img,sx,sy,sw,sh,dx,dy,w,h){logs.push({state:levels[sx/72],x:dx,y:dy,w,h})},globalAlpha:1,globalCompositeOperation:'source-over'};
const renderer=create({getAsset:id=>assets.get(id),getImage:async()=>({}),slots:{resolve:()=>({inputs:{},slots:{}})},timeline:{layerAt:l=>l},visualCore:{unitValue:()=>0}});
const size=v=>renderer.sizeFor(P+'hearts',new Set(),v);
assert.deepEqual(size({max:1,columns:10,value:3}),[72,72]);
assert.deepEqual(size({max:4,columns:10,value:12}),[294,72]);
assert.deepEqual(size({max:20,columns:10,value:63}),[738,150]);
assert.deepEqual(size({max:20,columns:5,value:63}),[368,306]);
assert.deepEqual(size({max:20,columns:1,value:0}),[72,1554]);
assert.deepEqual(renderer.sizeFor(P+'static'),[72,72]);
(async()=>{
  let values={max:1,columns:10,value:3};
  await renderer.drawAsset(P+'hearts',ctx,0,0,...size(values),0,values);
  assert.deepEqual(logs.map(x=>x.state),['three_quarter']);
  logs.length=0;
  values={max:20,columns:10,value:63};
  await renderer.drawAsset(P+'hearts',ctx,0,0,...size(values),0,values);
  assert.equal(logs.length,20);
  assert.equal(logs.filter(x=>x.state==='full').length,15);
  assert.equal(logs.filter(x=>x.state==='three_quarter').length,1);
  assert.equal(logs.filter(x=>x.state==='empty').length,4);
  assert.deepEqual([logs[0].x,logs[0].y],[0,0]);
  assert.deepEqual([logs[9].x,logs[9].y],[666,0]);
  assert.deepEqual([logs[10].x,logs[10].y],[0,78]);
  logs.length=0;
  values={max:20,columns:5,value:999};
  await renderer.drawAsset(P+'hearts',ctx,0,0,...size(values),0,values);
  assert.equal(logs.length,20);
  assert.ok(logs.every(x=>x.state==='full'),'Value must clamp to 20 hearts, not overflow');
  assert.equal(logs.at(-1).y,234);
  logs.length=0;
  await renderer.drawAsset(P+'static',ctx,0,0,72,72,0);
  assert.equal(logs.length,1,'Existing compositions remain unchanged');
  console.log('Adaptive state-family layout, quarter fill, max capacity and wrapped rows: PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
