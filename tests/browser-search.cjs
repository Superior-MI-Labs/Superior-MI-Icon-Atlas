"use strict";
// The derived browser index must preserve the existing icon archive and search semantics.
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const data=JSON.parse(fs.readFileSync(path.join(root,'site','public-catalog.json'),'utf8'));
const Search=require('../web/public-search.js');
const params={synonyms:data.synonyms};
assert.equal(data.schema,'smi-public-catalog/1');
const approved=JSON.parse(fs.readFileSync(path.join(root,'publications.json'),'utf8')).collections;
const approvedCount=approved.reduce((sum,p)=>sum+p.expected_assets,0);
assert.ok(approved.every(p=>Number.isInteger(p.expected_assets)&&p.expected_assets>0),'Every published pack needs an explicit asset count');
assert.equal(data.assets.length,2073+approvedCount);
assert.equal(data.approved_count,approvedCount);
assert.equal(data.legacy_count,2073);
assert.deepEqual(new Set(data.packs.map(x=>x.id)),new Set([...approved.map(p=>p.path.split('/').at(-1)),'legacy-icons']));
assert.ok(data.synonyms.flame.includes('fire'),'Root manifest synonyms must survive projection');
assert.ok(data.styles['white-geometric-monoline'],'Style registry must survive projection');
// Discovery metadata must come from the approved source manifests. Avoid
// a second authored search index or manually maintained public count.
const published=data.assets.filter(a=>!a.legacy);
assert.ok(published.every(a=>a.name&&a.style&&a.tags?.length&&a.subjects?.length),
  'Every published asset needs discoverable names, tags, and subjects');
const wolfcat=published.filter(a=>a.pack.startsWith('wolfcat-items-'));
assert.equal(wolfcat.length,3445,'Preserve all 3392 Wolfcat cells and 53 sheet previews');
const wolfcatCells=wolfcat.filter(a=>!a.id.endsWith('.sheet'));
assert.equal(wolfcatCells.length,3392);
assert.ok(wolfcatCells.every(a=>!a.name.startsWith('Uncatalogued sheet')&&a.tags.length>6),
  'Wolfcat artwork needs a visible subject name and non-generic category tags');
for(const q of ['bow','sword','helmet','potion','dice','rope','scroll','voucher','armor']){
  assert.ok(Search.results(data.assets,{...params,query:q}).some(a=>a.pack.startsWith('wolfcat-items-')),
    'Visually grounded Wolfcat search missing: '+q);
}
assert.ok(Search.results(data.assets,{...params,query:'missing image'}).some(a=>a.id.endsWith('.broken_image')),
  'StoryForge alternative search names must find the broken-image icon');
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
const playable=data.assets.filter(a=>a.showcases?.length);
assert.equal(playable.length,1,'Sky state set should be the single playable showcase candidate');
assert.equal(playable[0].id,'smi.sky.proto.actor.states');
assert.deepEqual(playable[0].showcases,[{page:'sky-prototype.html',label:'Play Sky interactive prototype'}]);
assert.ok(Search.results(data.assets,{...params,query:'playable interactive demo'})[0].id===playable[0].id);
assert.deepEqual(Search.results(data.assets,{...params,experience:'playable'}).map(a=>a.id),[playable[0].id]);
assert.ok(Search.facets(data.assets,params).experience.some(x=>x.value==='playable'&&x.count===1));
assert.ok(Search.results(data.assets,params)[0].kind==='composition','Playable demos do not displace finished default compositions');

// Expected sequence IDs come from the same approved source manifests as the catalog.
const expectedSequences=new Set();
for(const publication of approved){
  const dir=path.join(root,publication.path);
  const collection=JSON.parse(fs.readFileSync(path.join(dir,'collection.json'),'utf8'));
  for(const entry of collection.packs){
    const manifest=JSON.parse(fs.readFileSync(path.join(dir,entry.manifest),'utf8'));
    for(const asset of manifest.assets)if(asset.kind==='sequence')expectedSequences.add(asset.id);
  }
}
const foundSequences=Search.results(data.assets,{...params,kind:'sequence'});
assert.ok(expectedSequences.size>=4,'Previously published animation sequences must remain present');
assert.deepEqual(new Set(foundSequences.map(a=>a.id)),expectedSequences,'All published animations must remain discoverable by kind');
assert.equal(Search.results(data.assets,{...params,status:'archive'}).length,2073);
assert.equal(Search.results(data.assets,{...params,status:'published'}).length,approvedCount);
assert.ok(Search.results(data.assets,{...params,review:'reviewed'}).length>0);
for(const [pack,count] of [['royal-forge-controls',214],['royal-forge-hud-resources',360]]){
  const matches=Search.results(data.assets,{...params,pack});
  assert.equal(matches.length,count,pack+' must remain entirely discoverable and downloadable');
  assert.ok(matches.some(a=>a.kind==='composition'),pack+' must expose assembled interactive widgets');
}
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
