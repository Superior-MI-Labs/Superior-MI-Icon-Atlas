"use strict";
const assert=require('node:assert/strict');
const {create}=require('../web/asset-renderer.js');
const assets=new Map([
 ['hero.legacy',{id:'hero.legacy',kind:'region',texture:'atlas',rect_px:[0,0,30,80],logical_size_px:[100,120]}],
 ['hero.trimmed.a',{id:'hero.trimmed.a',kind:'region',texture:'atlas',rect_px:[0,0,50,80],logical_size_px:[100,120],trim_offset_px:[20,15],pivot:[0.5,1]}],
 ['hero.trimmed.b',{id:'hero.trimmed.b',kind:'region',texture:'atlas',rect_px:[50,0,60,90],logical_size_px:[100,120],trim_offset_px:[10,10],pivot:[0.25,1]}],
 ['hero.idle',{id:'hero.idle',kind:'sequence',frames:[{asset:'hero.trimmed.a'},{asset:'hero.trimmed.b'}],default_fps:16,playback:'loop'}],
 ['hero.no-pivot',{id:'hero.no-pivot',kind:'region',texture:'atlas',rect_px:[0,0,20,20]}],
 ['hero.bad-extent',{id:'hero.bad-extent',kind:'region',texture:'atlas',rect_px:[0,0,80,80],logical_size_px:[100,100],trim_offset_px:[30,30],pivot:[.5,1]}],
 ['hero.bad-missing',{id:'hero.bad-missing',kind:'region',texture:'atlas',rect_px:[0,0,20,20],trim_offset_px:[2,3]}],
 ['hero.bad-negative',{id:'hero.bad-negative',kind:'region',texture:'atlas',rect_px:[0,0,20,20],logical_size_px:[40,40],trim_offset_px:[-1,0]}],
 ['hero.bad-nine',{id:'hero.bad-nine',kind:'region',texture:'atlas',rect_px:[0,0,20,20],logical_size_px:[40,40],trim_offset_px:[2,3],nine_slice_px:[5,5,5,5]}]
]);
const calls=[];
const ctx={drawImage(_image,...args){calls.push(args)}};
const renderer=create({getAsset:id=>assets.get(id),getImage:async()=>({}),slots:{resolve:()=>({slots:{},inputs:{}})},timeline:{layerAt:l=>l},visualCore:{unitValue:()=>0}});
(async()=>{
  // This must be unchanged for the existing approved packs: logical_size_px
  // without trim_offset_px is legacy full-rectangle scaling.
  await renderer.drawAsset('hero.legacy',ctx,200,260,200,240,0);
  assert.deepEqual(calls.pop(),[0,0,30,80,200,260,200,240]);
  // Crop at logical (20,15) with dimensions (50,80) within a 100x120 pose.
  await renderer.drawAsset('hero.trimmed.a',ctx,200,260,200,240,0);
  assert.deepEqual(calls.pop(),[0,0,50,80,240,290,100,160]);
  // Pivot is feet-center of logical pose, not crop center; placing the same
  // character at world anchor (300,500) always preserves the foot baseline.
  await renderer.drawAssetAtPivot('hero.trimmed.a',ctx,300,500,200,240,0);
  assert.deepEqual(calls.pop(),[0,0,50,80,240,290,100,160]);
  assert.deepEqual(renderer.pivotFor('hero.idle',0),[.5,1]);
  assert.deepEqual(renderer.pivotFor('hero.idle',70),[.25,1]);
  await renderer.drawAssetAtPivot('hero.idle',ctx,300,500,200,240,70);
  assert.deepEqual(calls.pop(),[50,0,60,90,270,280,120,180]);
  assert.deepEqual(renderer.pivotFor('hero.idle',125),[.5,1],'Loop must select first pose again');
  assert.throws(()=>renderer.regionRect(assets.get('hero.bad-extent'),0,0,100,100),/outside logical canvas/);
  assert.throws(()=>renderer.regionRect(assets.get('hero.bad-missing'),0,0,100,100),/requires logical_size_px/);
  assert.throws(()=>renderer.regionRect(assets.get('hero.bad-negative'),0,0,100,100),/outside logical canvas/);
  await assert.rejects(()=>renderer.drawAsset('hero.bad-nine',ctx,0,0,40,40,0),/Trimmed nine-slice/);
  await assert.rejects(()=>renderer.drawAssetAtPivot('hero.no-pivot',ctx,10,20,20,20,0),/Missing authored pivot/);
  console.log('Trimmed animation regions: logical canvas, world-foot pivots, per-frame anchors and compatibility PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
