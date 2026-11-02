"use strict";
// Public search is a pure function: no parallel hand-maintained icon registry.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const data=JSON.parse(fs.readFileSync(path.join(root,'site','public-catalog.json'),'utf8'));
const Search=require('../web/public-search.js');
assert.equal(data.schema,'smi-public-catalog/1');
assert.equal(data.assets.length,70);
assert.deepEqual(new Set(data.packs.map(x=>x.id)),new Set(['fantasy-rpg-hud-wave1']));
for(const [query,token] of [['slider','Slider'],['sliders','Slider'],['healthbar','Meter'],['health','Health'],['heart','Heart'],['mana','Mana']]){
  const matches=Search.results(data.assets,{query});
  assert.ok(matches.length>0,query+' must return results');
  assert.ok(matches.some(a=>a.name.includes(token)),query+' must include the requested asset');
  console.log(query+': '+matches.length+' approved assets');
}
const defaults=Search.results(data.assets,{});
assert.ok(defaults[0].kind==='composition','Finished compositions must lead the default gallery');
assert.ok(defaults.every(a=>a.pack==='fantasy-rpg-hud-wave1'),'Legacy/tutorial packs must not appear');
assert.equal(Search.results(data.assets,{kind:'sequence'}).length,0,'Filters must reflect real data');
console.log('Unified public asset search and facets: PASS');