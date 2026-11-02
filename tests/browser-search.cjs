"use strict";
// The derived browser index must preserve the existing icon archive and search semantics.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const data=JSON.parse(fs.readFileSync(path.join(root,'site','public-catalog.json'),'utf8'));
const Search=require('../web/public-search.js');
const params={synonyms:data.synonyms};
assert.equal(data.schema,'smi-public-catalog/1');
assert.equal(data.assets.length,2143);
assert.equal(data.approved_count,70);
assert.equal(data.legacy_count,2073);
assert.deepEqual(new Set(data.packs.map(x=>x.id)),new Set(['fantasy-rpg-hud-wave1','legacy-icons']));
assert.ok(data.synonyms.flame.includes('fire'),'Root manifest synonyms must survive projection');
assert.ok(data.styles['white-geometric-monoline'],'Style registry must survive projection');
const archive=data.assets.filter(a=>a.legacy);
assert.equal(archive.length,2073);
assert.ok(archive.every(a=>a.domain&&a.style&&a.review_status),'Original icon facets must be preserved');
assert.ok(archive.some(a=>a.concept_id),'Visual concept IDs must survive projection');
for(const [query,token] of [['slider','Slider'],['sliders','Slider'],['healthbar','Meter'],['health','Health'],['heart','Heart'],['mana','Mana']]){
  const matches=Search.results(data.assets,{...params,query});
  assert.ok(matches.length>0,query+' must return results');
  assert.ok(matches.some(a=>a.name.includes(token)),query+' must include the requested asset');
}
const defaults=Search.results(data.assets,params);
assert.equal(defaults[0].kind,'composition','Finished compositions lead the default gallery');
assert.ok(defaults.every(a=>!a.legacy),'Archive icons must not flood default landing view');
assert.equal(Search.results(data.assets,{...params,pack:'legacy-icons'}).length,2073);
assert.ok(Search.results(data.assets,{...params,query:'fire'}).some(a=>a.legacy));
assert.ok(Search.results(data.assets,{...params,query:'folder'}).some(a=>a.legacy));
assert.ok(Search.results(data.assets,{...params,query:'health'}).some(a=>!a.legacy));
assert.equal(Search.results(data.assets,{...params,kind:'sequence'}).length,0);
assert.equal(Search.results(data.assets,{...params,status:'archive'}).length,2073);
assert.equal(Search.results(data.assets,{...params,status:'published'}).length,70);
assert.ok(Search.results(data.assets,{...params,review:'reviewed'}).length>0);
assert.ok(Search.results(data.assets,{...params,review:'unreviewed'}).length>0);
const sample=archive.find(a=>a.tags.length&&a.subjects.length);
assert.ok(sample);
const subjectMatches=Search.results(data.assets,{...params,subject:sample.subjects[0],domain:sample.domain});
assert.ok(subjectMatches.some(a=>a.id===sample.id),'Conjunctive filters must preserve a known icon');
assert.ok(subjectMatches.every(a=>a.subjects.includes(sample.subjects[0])&&a.domain===sample.domain));
for(const search of ['flame','fire','blaze']){
  const matches=Search.results(data.assets,{...params,query:search});
  assert.ok(matches.length,'Canonical or synonym search must return candidates: '+search);
}
const exact=Search.results(data.assets,{...params,query:sample.id});
assert.equal(exact[0].id,sample.id,'Exact ID must outrank generic featured results');
const facets=Search.facets(data.assets,params);
assert.ok(facets.domain.some(x=>x.value==='programming'));
assert.ok(facets.style.some(x=>x.value==='white-geometric-monoline'));
assert.ok(facets.subject.length>=100);
assert.ok(facets.review.some(x=>x.value==='reviewed'));
assert.deepEqual(new Set(facets.status.map(x=>x.value)),new Set(['published','archive']));
const filteredFacets=Search.facets(data.assets,{...params,domain:'programming'});
assert.ok(filteredFacets.subject.every(x=>x.count<=2073));
console.log('Manifest-derived unified catalog, archive search and facets: PASS');
