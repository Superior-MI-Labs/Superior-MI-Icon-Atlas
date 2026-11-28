'use strict';
const assert=require('node:assert/strict'),test=require('node:test');
const C=require('../web/collection-core.js');
const hash='a'.repeat(64),historical='b'.repeat(64);
const ref=(kind,id,digest=hash)=>({kind,id,archive_sha256:digest});
const catalog={schema:'smi-public-catalog/1',packs:[{id:'p',zip:'demo/p.zip',archive_sha256:hash},{id:'legacy',archived:true}],concepts:[
 {id:'test.sword',name:'Sword',pack:'p',capabilities:['enchantable'],relationships:[{kind:'requires',target:{kind:'asset',id:'sword.icon',archive_sha256:historical}},{kind:'compatible_with',target:{kind:'concept',id:'test.dark'}}]},
 {id:'test.dark',name:'Dark',pack:'p',discovery_offers:{apply:{role:'enhancement',requirements:[{scope:'concept',op:'capability.has',key:'enchantable'},{scope:'representation',op:'interface.has',key:'blade/1'}]}},relationships:[{kind:'compatible_with',target:{kind:'concept',id:'test.sword'}}]}
],assets:[{id:'sword.icon',name:'Sword icon',pack:'p',concept_id:'test.sword'},{id:'sword.world',name:'Sword world',pack:'p',concept_id:'test.sword',interfaces:['blade/1'],render_refs:['sword.icon','hidden.part']},{id:'dark.icon',name:'Dark icon',pack:'p',concept_id:'test.dark'},{id:'hidden.part',name:'Hidden',pack:'p',discovery:'hidden'},{id:'legacy',pack:'legacy',legacy:true}]};
const index=()=>C.createRelationshipExplorer(catalog,C.createDiscoveryIndex(catalog,{catalog_sha256:'1'.repeat(64)}));
test('unified graph distinguishes declared compatibility, authored semantics and render refs',()=>{
 const g=index().focus(ref('asset','sword.world'),{depth:2});
 assert.ok(g.edges.some(e=>e.type==='compatible'&&e.evidence.offer_id==='apply'));
 assert.ok(g.edges.some(e=>e.type==='dependency'&&e.evidence.source_archive_sha256===hash));
 assert.ok(g.edges.some(e=>e.type==='authored'));
 assert.ok(g.edges.some(e=>e.type==='representation'));
 assert.ok(g.nodes.some(n=>n.hidden));
 assert.ok(!g.nodes.some(n=>n.ref.id==='legacy'));
 const old=g.nodes.find(n=>n.ref.archive_sha256===historical);assert.ok(old&&!old.available);
 assert.ok(g.nodes.some(n=>n.ref.id==='sword.icon'&&n.ref.archive_sha256===hash&&n.available));
});
test('filters and reverse discovery preserve evidence and exact owner',()=>{
 const i=index(),g=i.focus(ref('asset','dark.icon'),{types:['compatible']});
 assert.ok(g.edges.some(e=>e.type==='compatible'&&e.evidence.offer.id==='test.dark'&&e.evidence.subject.id==='sword.world'));
 assert.ok(g.edges.every(e=>e.type==='compatible'));
 const unknown=i.focus(ref('asset','sword.icon'),{types:['unknown']});
 assert.ok(unknown.edges.some(e=>e.type==='unknown'));
 assert.equal(i.focus(ref('asset','sword.icon'),{types:['compatible']}).edges.length,0);
 assert.throws(()=>i.focus(ref('asset','sword.icon',historical)),/Unavailable/);
});
test('bounded deterministic graph, legal semantic cycles and isolated output',()=>{
 const i=index(),opts={depth:2,limit:4},r=ref('concept','test.sword'),before=JSON.stringify(catalog);
 const a=i.focus(r,opts);assert.ok(a.nodes.length<=4);assert.ok(a.edges.every(e=>a.nodes.some(n=>n.key===e.from)&&a.nodes.some(n=>n.key===e.to)));
 assert.deepEqual(i.focus(r,opts),a);a.nodes[0].name='changed';assert.notEqual(i.focus(r,opts).nodes[0].name,'changed');
 assert.equal(JSON.stringify(catalog),before);
 assert.throws(()=>i.focus(r,{depth:3}),/Invalid/);
 assert.throws(()=>i.focus(r,{limit:41}),/Invalid/);
});
test('older catalogs and cross-owner hints do not invent concept links',()=>{
 const c=structuredClone(catalog);c.packs.push({id:'other',zip:'demo/other.zip',archive_sha256:historical});
 c.assets.push({id:'cross',pack:'other',concept_id:'test.sword'});
 const i=C.createRelationshipExplorer(c);
 assert.equal(i.focus(ref('asset','cross',historical)).edges.length,0);
 assert.equal(i.focus(ref('asset','dark.icon'),{types:['dependency']}).edges.length,0);
});
