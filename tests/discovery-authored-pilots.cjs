'use strict';
const assert=require('node:assert/strict'),test=require('node:test');
const C=require('../web/collection-core.js');
const fern=require('../examples/painterly-fantasy-seasonal-fern/manifest.json');
const hud=require('../examples/royal-forge-hud-resources/manifest.json');
const digest='a'.repeat(64),other='b'.repeat(64);
test('actual seasonal fern selects four authored regions',()=>{
 const c=fern.concepts[0];C.validateRepresentations(fern.concepts,fern.assets);
 for(const season of ['spring','summer','autumn','winter']){
  const result=C.selectRepresentation(c,fern.assets,{role:'world',instance:{states:{season}}});
  assert.equal(result.asset,fern.assets.find(a=>a.id.endsWith('.'+season)).id);
 }
});
test('actual HUD discovery matches all authored slot options without adding any',()=>{
 const i=C.createArchiveDiscoveryIndex(hud,digest),meter=hud.assets.find(a=>a.id==='smi.hud.royalforge02.widget.resource-meter');
 const before=JSON.stringify(hud);
 for(const [offer_id,slot] of Object.entries(meter.slots)){
  const q=i.query({direction:'offer',ref:{kind:'concept',id:meter.concept_id,archive_sha256:digest,offer_id},target_kind:'asset',limit:100});
  assert.deepEqual(q.groups.compatible.matches.map(x=>x.subject.id).sort(),[...slot.options].sort());
  assert.equal(q.scope,'local-archive');assert.equal(q.archive_sha256,digest);assert.equal(q.catalog_sha256,undefined);
 }
 const subject={kind:'asset',id:'smi.hud.royalforge02.bar.fill.mana',archive_sha256:digest};
 assert.equal(i.query({direction:'subject',ref:subject,limit:8}).groups.compatible.matches[0].offer.offer_id,'fill');
 assert.throws(()=>i.query({direction:'subject',ref:{...subject,archive_sha256:other},limit:8}),/Unknown exact/);
 assert.equal(JSON.stringify(hud),before);
});
test('local projection does not become a public archive locator',()=>{
 const i=C.createArchiveDiscoveryIndex(fern,digest);
 assert.equal(i.summary().archive_sha256,digest);assert.equal(i.summary().catalog_sha256,undefined);
 assert.equal(i.summary().scope,'local-archive');
 assert.throws(()=>C.createArchiveDiscoveryIndex(fern,'invalid'),/Invalid archive/);
});
