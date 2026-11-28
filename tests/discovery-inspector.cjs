'use strict';
// Exercise the exact fragment inserted into the public app; this is a DOM shim,
// not browser or host qualification. Existing full browser gates still apply.
const assert=require('node:assert/strict'),test=require('node:test'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {webcrypto,createHash}=require('node:crypto'),C=require('../web/collection-core.js');
const app=fs.readFileSync(path.join(__dirname,'../web/app.js'),'utf8');
const source=app.match(/\/\/ BEGIN capability discovery inspector[\s\S]*?\/\/ END capability discovery inspector/)?.[0];
assert.ok(source,'Missing real app discovery block');
const h=x=>x.repeat(64),pack=(id,n)=>({id,zip:`demo/${id}.zip`,archive_sha256:h(n),immutable_zip:`archives/sha256/${h(n)}.zip`});
const sword={id:'test.sword',pack:'weapon',name:'Sword',capabilities:['enchantable']};
const enchant={id:'test.dark',pack:'effects',name:'Dark',discovery_offers:{apply:{role:'enhancement',requirements:[{scope:'concept',op:'capability.has',key:'enchantable'},{scope:'representation',op:'interface.has',key:'blade/1'}]}}};
const data=()=>({schema:'smi-public-catalog/1',packs:[pack('weapon','a'),pack('effects','b'),{id:'legacy-icons',archived:true}],concepts:[structuredClone(sword),structuredClone(enchant)],assets:[{id:'sword.world',name:'Sword world',pack:'weapon',concept_id:sword.id,interfaces:['blade/1']},{id:'sword.icon',name:'Sword icon',pack:'weapon',concept_id:sword.id},{id:'dark.icon',name:'Dark icon',pack:'effects',concept_id:enchant.id},{id:'legacy.icon',name:'Legacy',pack:'legacy-icons',legacy:true},{id:'hidden',name:'Hidden',pack:'weapon',concept_id:sword.id,discovery:'hidden'}]});
class Element{
 constructor(tag){this.tagName=tag;this.textContent='';this.children=[];this.dataset={};this.events=new Map();this.open=false;}
 append(...nodes){this.children.push(...nodes)}
 addEventListener(event,fn){this.events.set(event,fn)}
 fire(event){this.events.get(event)?.()}
}
const all=(node,fn)=>[...(fn(node)?[node]:[]),...node.children.flatMap(n=>all(n,fn))];
const txt=node=>[node.textContent,...node.children.map(txt)].join(' ');
async function harness(catalog=data(),crypto=webcrypto){
 const entryById=new Map(catalog.assets.map(a=>[a.id,a])),conceptIndex=new Map(catalog.concepts.map(c=>[c.id,c])),collections=new Map(catalog.packs.map(p=>[p.id,p])),opened=[],queries=[],builds=[];
 const bytes=new TextEncoder().encode(JSON.stringify(catalog));
 const Collections={createDiscoveryIndex(index,options){builds.push(options);const original=C.createDiscoveryIndex(index,options);return {query(q){queries.push(q);return original.query(q)}}}};
 const env=vm.createContext({Collections,entryById,conceptIndex,collections,crypto,document:{createElement:tag=>new Element(tag)},human:v=>String(v),openDetail:a=>opened.push(a.id)});
 vm.runInContext(source+'\nthis.api={prepareCapabilityDiscovery,appendCapabilityDiscovery,discoveryTarget};',env);
 await env.api.prepareCapabilityDiscovery(catalog,bytes);
 function render(id){const root=new Element('div');env.api.appendCapabilityDiscovery(entryById.get(id),root);return root;}
 return {env,render,opened,queries,builds,bytes,collections};
}
test('index constructed once from actual response-byte fingerprint; forward link and evidence',async()=>{
 const h=await harness();assert.equal(h.builds.length,1);assert.equal(h.builds[0].catalog_sha256,createHash('sha256').update(h.bytes).digest('hex'));
 const root=h.render('sword.world');assert.equal(h.queries.length,1);assert.match(txt(root),/Declared requirements matched \(1\)/);assert.match(txt(root),/not verification/);
 const button=all(root,n=>n.tagName==='button')[0];assert.match(button.textContent,/Dark/);button.onclick();assert.deepEqual(h.opened,['dark.icon']);
 h.render('sword.world');assert.equal(h.builds.length,1);
});
test('mechanical eligibility does not promote missing representation evidence',async()=>{
 const h=await harness(),root=h.render('sword.icon');assert.match(txt(root),/Incomplete evidence \(1\)/);assert.doesNotMatch(txt(root),/Declared requirements matched/);
 assert.equal(all(root,n=>n.dataset.discoveryGroup==='unknown')[0].open,false);assert.match(txt(root),/representation · interface.has · blade\/1: unknown/);
});
test('reverse queries are lazy and use the exact offer owner; no duplicate evaluation',async()=>{
 const h=await harness(),root=h.render('dark.icon');const offer=all(root,n=>n.dataset.discoveryOffer==='apply')[0];assert.ok(offer);
 assert.equal(h.queries.length,1);offer.fire('toggle');assert.equal(h.queries.length,1);offer.open=true;offer.fire('toggle');assert.equal(h.queries.length,2);
 const q=h.queries[1];assert.equal(q.direction,'offer');assert.equal(q.ref.offer_id,'apply');assert.equal(q.ref.archive_sha256,'b'.repeat(64));
 assert.match(txt(offer),/Sword world/);assert.match(txt(offer),/Incomplete evidence/);offer.fire('toggle');assert.equal(h.queries.length,2);
});
test('wrong archive identities never redirect to current content',async()=>{
 const h=await harness(),good=h.env.api.discoveryTarget({kind:'concept',id:'test.dark',archive_sha256:'b'.repeat(64)});assert.equal(good.entry.id,'dark.icon');
 assert.equal(h.env.api.discoveryTarget({kind:'concept',id:'test.dark',archive_sha256:'c'.repeat(64)}).entry,null);
 assert.equal(h.env.api.discoveryTarget({kind:'asset',id:'hidden',archive_sha256:'a'.repeat(64)}).entry,null);
});
test('legacy and hidden assets stay available to ordinary browsing without discovery queries',async()=>{
 const h=await harness();assert.equal(h.render('legacy.icon').children.length,0);assert.equal(h.render('hidden').children.length,0);assert.equal(h.queries.length,0);
});
test('old catalog without offers needs no index or crypto; unavailable crypto is nonfatal',async()=>{
 const c=data();delete c.concepts[1].discovery_offers;const old=await harness(c,null);assert.equal(old.builds.length,0);assert.equal(old.render('sword.world').children.length,0);
 const bad=await harness(data(),null);assert.match(txt(bad.render('sword.world')),/Capability discovery unavailable/);assert.equal(bad.queries.length,0);
});
test('malformed optional projection disables only discovery and does not issue queries',async()=>{
 const c=data();c.packs[1].archive_sha256='wrong';const h=await harness(c);assert.match(txt(h.render('sword.world')),/Capability discovery unavailable/);assert.equal(h.queries.length,0);
});
