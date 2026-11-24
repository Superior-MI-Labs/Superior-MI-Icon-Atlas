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
const logs=[],translates=[];
const ctx={save(){},restore(){},translate(x,y){translates.push([x,y])},scale(){},beginPath(){},rect(){},clip(){},fillRect(){},drawImage(_img,sx,sy,sw,sh,dx,dy,w,h){logs.push({state:levels[sx/72],x:dx,y:dy,w,h})},globalAlpha:1,globalCompositeOperation:'source-over'};
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
  // One content-sized composition may contain several repeat and static layers.
  // Negative offsets and ornaments outside the first repeater must be preserved.
  assets.set(P+'corner',{id:P+'corner',kind:'region',rect_px:[0,0,40,20],texture:'sheet'});
  assets.set(P+'ornamented',{id:P+'ornamented',kind:'composition',size_px:[738,150],
    inputs:assets.get(P+'hearts').inputs,
    layers:[
      {...assets.get(P+'hearts').layers[0]},
      {id:'left',asset:P+'corner',offset_px:[-8,-3],size_px:[40,20]},
      {id:'right',asset:P+'corner',offset_px:[765,0],size_px:[40,20]}
    ]});
  const g=renderer.geometryFor(P+'ornamented',new Set(),{max:20,columns:10,value:63});
  assert.deepEqual(g,{width:813,height:153,minX:-8,minY:-3});
  assert.deepEqual(renderer.sizeFor(P+'ornamented',new Set(),{max:20,columns:10,value:63}),[813,153]);
  translates.length=0;
  await renderer.drawAsset(P+'ornamented',ctx,0,0,813,153,0,{max:20,columns:10,value:63});
  assert.ok(translates.some(([x,y])=>x===8&&y===3),'Negative content origin must be translated into canvas');
  console.log('Adaptive state-family layout, quarter fill, max capacity and wrapped rows: PASS');
})().catch(e=>{console.error(e);process.exitCode=1});

/* Every Royal Forge compatibility ID must retain its geometry and render the
 * exact selected slots; multiple instances may bind distinct parent inputs. */
(async()=>{
  const fs=require('node:fs'),path=require('node:path');
  const pack=JSON.parse(fs.readFileSync(path.join(__dirname,'../examples/royal-forge-hud-resources/manifest.json'),'utf8'));
  const map=new Map(pack.assets.map(a=>[a.id,a])),Slots=require('../web/slot-core.js');
  const Visual=require('../web/visual-core.js');
  assert.deepEqual(Slots.validate(pack),[]);
  const clips=[],draws=[];
  const ctx={save(){},restore(){},translate(){},scale(){},beginPath(){},rect(...args){clips.push(args)},clip(){},drawImage(_img,...args){draws.push(args)},globalAlpha:1};
  const render=create({getAsset:id=>map.get(id),getImage:async()=>({}),slots:Slots,timeline:{layerAt:l=>l},visualCore:Visual});
  const template=map.get('smi.hud.royalforge02.widget.resource-meter'),bars=pack.assets.filter(a=>/\.widget\.bar\.[^.]+\.[^.]+$/.test(a.id));
  assert.equal(bars.length,50);assert.equal(Object.keys(template.presets).length,50);
  for(const bar of bars){
    const values={value:50};clips.length=0;draws.length=0;
    await render.drawAsset(bar.id,ctx,0,0,...bar.size_px,0,values);
    assert.equal(draws.length,4,bar.id);assert.equal(clips[0][2],153,bar.id);
    const choices=template.presets[bar.layers[0].preset].slots;
    assert.deepEqual(draws.map(d=>d.slice(0,4)),['base','fill','rim','emblem'].map(k=>map.get(choices[k]).rect_px));
  }
  clips.length=0;
  const hud=map.get('smi.hud.royalforge02.hud.adventurer');
  await render.drawAsset(hud.id,ctx,0,0,...hud.size_px,0,{health:0,mana:100,stamina:25,shield:75,experience:50,boss_health:20,charges:2});
  assert.deepEqual(clips.slice(1,6).map(c=>c[2]),[0,306,76.5,229.5,153]);
  const invalid=JSON.parse(JSON.stringify(pack));invalid.assets.find(a=>a.id===hud.id).layers[1].input_bindings.value='unknown';
  assert.ok(Slots.validate(invalid).some(e=>e.includes('incompatible child input binding')));
  console.log('50 shared meter variants and independent HUD bindings: PASS');
})().catch(e=>{console.error(e);process.exitCode=1;});

/* Real authored control panel: six independent slot bindings and host-owned
 * cooldown masking. Locked and active modes must never display cooldown. */
(async()=>{
  const fs=require('node:fs'),path=require('node:path');
  const pack=JSON.parse(fs.readFileSync(path.join(__dirname,'../examples/royal-forge-controls/manifest.json'),'utf8'));
  const map=new Map(pack.assets.map(a=>[a.id,a])),Slots=require('../web/slot-core.js'),Visual=require('../web/visual-core.js');
  assert.deepEqual(Slots.validate(pack),[]);
  const clips=[],draws=[];
  const ctx={save(){},restore(){},translate(){},scale(){},beginPath(){},rect(...r){clips.push(r)},clip(){},drawImage(_img,...args){draws.push(args.slice(0,4))},globalAlpha:1};
  const render=create({getAsset:id=>map.get(id),getImage:async()=>({}),slots:Slots,timeline:{layerAt:l=>l},visualCore:Visual});
  const panel=map.get('smi.ui.fantasy01.wave2.widget.action-inventory-hud'),values=Object.fromEntries(Object.entries(panel.inputs).map(([k,d])=>[k,d.default]));
  for(const [i,mode,cooldown] of [[1,'ready',25],[2,'ready',75],[3,'locked',100],[4,'active',100],[5,'ready',0],[6,'ready',100]]){
    values['ability_'+i+'_mode']=mode;values['ability_'+i+'_cooldown']=cooldown;
  }
  values.inventory_1='epic';values.status_1='warning';
  await render.drawAsset(panel.id,ctx,0,0,...panel.size_px,0,values);
  assert.deepEqual(clips.map(r=>r[3]),[22,66,0,88]);
  assert.deepEqual(draws.slice(0,6),['ready','cooldown','ready','cooldown','locked','active'].map(k=>map.get('smi.ui.fantasy01.wave2.hotbar.square.'+k).rect_px));
  assert.deepEqual(draws[10],map.get('smi.ui.fantasy01.wave2.inventory.square.epic').rect_px);
  assert.deepEqual(draws[16],map.get('smi.ui.fantasy01.wave2.indicator.pip.warning').rect_px);
  console.log('Independent hotbar cooldowns, inventory and status: PASS');
})().catch(e=>{console.error(e);process.exitCode=1;});

/* Nested adaptive layout must measure the selected preset before drawing. */
(()=>{
  const Slots=require('../web/slot-core.js');
  const hearts={...assets.get(P+'hearts'),presets:{Small:{inputs:{max:2,columns:2,value:4}}}};
  const parent={id:P+'nested',kind:'composition',size_px:[400,400],layers:[{id:'child',asset:hearts.id,preset:'Small'}]};
  const map=new Map(assets);map.set(hearts.id,hearts);map.set(parent.id,parent);
  const r=create({getAsset:id=>map.get(id),getImage:async()=>({}),slots:Slots,timeline:{layerAt:l=>l},visualCore:{unitValue:()=>0}});
  assert.deepEqual(r.sizeFor(hearts.id,new Set(),{},'Small'),[146,72]);
  console.log('Nested preset geometry: PASS');
})();
