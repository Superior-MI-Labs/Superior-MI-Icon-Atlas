'use strict';
const assert=require('node:assert/strict');
const test=require('node:test');
const {createHash}=require('node:crypto');
const C=require('../web/collection-core.js');
const shared=require('./fixtures/offer-validation-fixtures.json');
const h=x=>x.repeat(64);
const identity=(kind,id,n)=>({kind,id,archive_sha256:h(n)});
const owner=(id,n)=>({id,zip:`demo/${id}.zip`,archive_sha256:h(n),immutable_zip:`archives/sha256/${h(n)}.zip`});
const cap=(key,scope='concept')=>({scope,op:'capability.has',key});
const intf=key=>({scope:'representation',op:'interface.has',key});
const eq=(key,expected)=>({scope:'context',op:'fact.equals',key,expected});
const num=(key,min,max,unit)=>({scope:'concept',op:'quantity.range',key,min,max,unit});
const def=(id,pack,more={})=>({id,pack,name:id,...more});
const asset=(id,pack,concept_id,more={})=>({id,pack,concept_id,name:id,kind:'region',...more});
const sword=def('test.sword','weapons',{capabilities:['enchantable','slashing'],physical:{width_m:.8}});
const fern=def('test.fern','plants',{capabilities:['vegetation']});
const meter=def('test.meter','hud',{capabilities:['resource.display']});
const enchant=(element,pack)=>def('test.'+element,pack,{discovery_offers:{apply:{role:'enhancement',requirements:[cap('enchantable'),intf('smi.blade/1')]},mechanical:{role:'mechanical-enhancement',requirements:[cap('enchantable'),num('physical.width_m',.5,1,'m')]}}});
const fire=enchant('fire','effects'),dark=enchant('dark','dark'),light=enchant('light','light');
const snow=def('test.snow','effects',{discovery_offers:{overlay:{role:'overlay',requirements:[cap('vegetation'),intf('smi.overlay/1'),eq('season',{kind:'enum',value:'winter'})]}}});
const mana=def('test.mana','effects',{discovery_offers:{meter:{role:'resource',requirements:[cap('resource.display'),intf('smi.resource.numeric/1'),eq('resource',{kind:'enum',value:'mana'})]}}});
const conditional=def('test.conditional','effects',{discovery_offers:{apply:{role:'conditional',requirements:[cap('enchantable'),cap('enabled','context'),eq('enabled',{kind:'boolean',value:false})]}}});
const packs=[owner('weapons','a'),owner('plants','b'),owner('hud','c'),owner('effects','d'),owner('dark','e'),owner('light','f'),{id:'legacy-icons',archived:true}];
const assets=[asset('sword.world','weapons',sword.id,{interfaces:['smi.blade/1'],subjects:['iron','sword'],style:'fantasy'}),asset('sword.icon','weapons',sword.id),asset('sword.variant','weapons',sword.id,{interfaces:['smi.blade/1'],subjects:['iron','weapon'],style:'pixel'}),asset('fern.world','plants',fern.id,{interfaces:['smi.overlay/1']}),asset('meter.world','hud',meter.id,{interfaces:['smi.resource.numeric/1']}),asset('unrelated','weapons',undefined,{interfaces:['smi.blade/1'],subjects:['iron','sword'],style:'fantasy'}),asset('cross.pack.hint','plants',sword.id,{interfaces:['smi.blade/1']}),{id:'legacy.icon',pack:'legacy-icons',legacy:true},asset('hidden','weapons',sword.id,{discovery:'hidden',interfaces:['smi.blade/1']})];
const catalog=(withNew=true)=>({schema:'smi-public-catalog/1',packs:structuredClone(packs),concepts:structuredClone([sword,fern,meter,fire,snow,mana,conditional,...(withNew?[dark,light]:[])]),assets:structuredClone(assets)});
const idx=(c=catalog(),revision='1')=>C.createDiscoveryIndex(c,{catalog_sha256:h(revision)});
const request=(direction,ref,extra={})=>({direction,ref,limit:100,...extra});
const sw=identity('asset','sword.world','a'),si=identity('asset','sword.icon','a'),sc=identity('concept',sword.id,'a');
const darkOffer={...identity('concept',dark.id,'e'),offer_id:'apply'};
const hash=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
function total(r,s='compatible'){return r.groups[s].total;}
for(const fixture of shared)test('conformance: '+fixture.name,()=>fixture.valid?assert.doesNotThrow(()=>C.validateDiscoveryOffers(fixture.offers)):assert.throws(()=>C.validateDiscoveryOffers(fixture.offers)));
test('new offers propagate on unchanged content, both query directions',()=>{
 const old=catalog(false),next=catalog(true),before=hash(old.assets),r=idx(old,'1').query(request('subject',sw,{role:'enhancement'})),s=idx(next,'2').query(request('subject',sw,{role:'enhancement'}));
 assert.equal(total(r),1);assert.equal(total(s),3);assert.equal(hash(next.assets),before);assert.equal(r.catalog_sha256,h('1'));assert.equal(s.catalog_sha256,h('2'));
 const reverse=idx(next).query(request('offer',darkOffer,{target_kind:'asset'}));
 assert.deepEqual(reverse.groups.compatible.matches.map(x=>x.subject.id),['sword.variant','sword.world']);
 assert.deepEqual(reverse.groups.compatible.matches.find(x=>x.subject.id===sw.id),s.groups.compatible.matches.find(x=>x.offer.id===dark.id));
 assert.equal(reverse.groups.unknown.matches.some(x=>x.subject.id==='cross.pack.hint'),true);
 assert.equal(reverse.groups.compatible.matches.some(x=>x.subject.id==='hidden'),false);
});
test('concept mechanics and actual representation requirements remain separate',()=>{
 const i=idx(),a=i.query(request('subject',si,{role:'enhancement'})),b=i.query(request('subject',sc,{role:'mechanical-enhancement'}));
 assert.equal(total(a),0);assert.equal(total(a,'unknown'),3);assert.equal(a.groups.unknown.matches[0].scopes.concept,'compatible');assert.equal(a.groups.unknown.matches[0].scopes.representation,'unknown');
 assert.equal(total(b),3);assert.equal(b.groups.compatible.matches[0].scopes.representation,'not-required');
 assert.equal(b.groups.compatible.matches[0].evidence[1].evidence.value.unit,'m');
});
test('legacy remains valid, missing concept links do not become evidence',()=>{
 const c=catalog(),i=idx(c);assert.equal(i.summary().excluded_assets,2);
 const empty={schema:c.schema,packs:c.packs,assets:c.assets};assert.equal(idx(empty).summary().offers,0);
 const q=i.query(request('subject',identity('asset','unrelated','a'),{role:'enhancement'}));assert.equal(total(q),0);assert.equal(total(q,'unknown'),3);
});
test('same generic requirements work for seasons and resource meters',()=>{
 const i=idx();const f=identity('asset','fern.world','b'),m=identity('asset','meter.world','c');
 assert.equal(total(i.query(request('subject',f,{role:'overlay',context:{properties:{season:{kind:'enum',value:'winter'}}}}))),1);
 assert.equal(total(i.query(request('subject',f,{role:'overlay'})),'unknown'),1);
 assert.equal(total(i.query(request('subject',f,{role:'overlay',context:{properties:{season:{kind:'enum',value:'summer'}}}})),'incompatible'),1);
 assert.equal(total(i.query(request('subject',m,{role:'resource',context:{properties:{resource:{kind:'enum',value:'mana'}}}}))),1);
});
test('explicit negative context dominates missing; false is a real property',()=>{
 const i=idx(),r=i.query(request('subject',sw,{role:'conditional',context:{capabilities:{enabled:false}}}));assert.equal(total(r,'incompatible'),1);
 const s=i.query(request('subject',sw,{role:'conditional',context:{capabilities:{enabled:true},properties:{enabled:{kind:'boolean',value:false}}}}));assert.equal(total(s),1);
 assert.equal(s.groups.compatible.matches[0].evidence.at(-1).evidence.source.kind,'query-context');
});
test('preference ranking does not change eligibility, drop unranked or promote unknowns',()=>{
 const i=idx(),q=request('offer',darkOffer,{target_kind:'asset'}),normal=i.query(q),ranked=i.rankEligible(q,sw);
 assert.equal(total(ranked),total(normal));assert.deepEqual(ranked.groups.unknown,normal.groups.unknown);assert.equal(ranked.ranking_scope,'all-compatible-candidates');
 assert.deepEqual(new Set(ranked.groups.compatible.matches.map(x=>x.subject.id)),new Set(['sword.world','sword.variant']));assert.ok(ranked.groups.compatible.matches.every(x=>'preference' in x));assert.equal(ranked.groups.compatible.matches[0].subject.id,'sword.variant');assert.ok(ranked.groups.compatible.matches[0].preference.score>0);assert.equal(ranked.groups.compatible.matches[1].preference,null);assert.ok(ranked.groups.compatible.matches[0].preference.evidence_weight_fraction<=1);
 const one={...q,limit:1};assert.equal(i.query(one).groups.compatible.matches[0].subject.id,'sword.variant');assert.equal(i.rankEligible(one,identity('asset','sword.variant','a')).groups.compatible.matches[0].subject.id,'sword.world');
 assert.throws(()=>i.rankEligible(q,sw,{weights:{semantic:0,color:0,style:0}}),/weights/);
});
test('catalog identity, bounded deterministic pages and immutable outputs',()=>{
 const c=catalog(),i=idx(c),q=request('subject',sw,{role:'enhancement',limit:1}),r=i.query(q);
 assert.equal(total(r),3);assert.equal(r.groups.compatible.matches.length,1);c.concepts.reverse();c.assets.reverse();assert.deepEqual(idx(c).query(q),r);
 const out=i.query(q);out.groups.compatible.matches[0].evidence[0].evidence.value=false;out.groups.compatible.matches[0].offer.id='changed';assert.deepEqual(i.query(q),r);
 assert.throws(()=>i.query(request('subject',{...sw,archive_sha256:h('9')})),/Unknown exact/);
 assert.throws(()=>i.query(request('subject',sw,{limit:101})),/Invalid/);
 assert.throws(()=>i.query(request('offer',darkOffer)),/target kind/);
 assert.ok(!('active' in r.groups.compatible.matches[0])&&!('dependencies' in r.groups.compatible.matches[0]));
});
test('bad owner, duplicate identities and invalid immutable locators fail closed',()=>{
 let c=catalog();c.concepts.push(c.concepts[0]);assert.throws(()=>idx(c),/Duplicate/);
 c=catalog();c.assets.push(c.assets[0]);assert.throws(()=>idx(c),/Duplicate/);
 c=catalog();c.concepts[0].pack='missing';assert.throws(()=>idx(c),/Unresolved/);
 c=catalog();c.packs[0].immutable_zip='archives/sha256/'+h('9')+'.zip';assert.throws(()=>idx(c),/locator/);
});
