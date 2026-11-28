'use strict';
/* One pure query/facet engine for generated icon and visual-pack records. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;root.VisualAtlasSearch=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
  const clean=value=>String(value??'').normalize('NFKD').toLowerCase().replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
  const tokens=value=>clean(value).split(/\s+/).filter(Boolean);
  const FILTERS=['kind','pack','domain','style','subject','review','status','license','animated','experience','capability','interface','category_path','perspective','theme','medium','family'];
  const synonymCache=new WeakMap();
  function thesaurus(groups={}){
    if(synonymCache.has(groups))return synonymCache.get(groups);
    const lookup=new Map();
    for(const [canonical,aliases] of Object.entries(groups)){
      const words=[canonical,...aliases].map(clean).filter(Boolean);
      for(const term of words){if(!lookup.has(term))lookup.set(term,new Set());for(const synonym of words)lookup.get(term).add(synonym);}
    }
    synonymCache.set(groups,lookup);
    return lookup;
  }
  function contains(value,term){
    const hay=' '+clean(Array.isArray(value)?value.join(' '):value)+' ';
    if(hay.includes(' '+term+' '))return 1;
    if(!term.includes(' ')&&term.length>2){
      const singular=term.endsWith('s')?term.slice(0,-1):term+'s';
      if(hay.includes(' '+singular+' '))return .9;
      if(tokens(value).some(word=>word.startsWith(term)&&word!==term))return .55;
    }
    return 0;
  }
  function score(asset,query,synonyms={}){
    const terms=tokens(query);if(!terms.length)return 1;
    const aliases=thesaurus(synonyms);
    const fields=[
      [asset.name,85],[asset.id,75],[asset.aliases,70],[asset.tags,45],[asset.description,25],
      [asset.subjects,35],[asset.concept_id,35],[asset.concept_name,30],[asset.concept_capabilities,25],[asset.concept_rulesets,12],[asset.representation?.role,15],[asset.domain,12],
      [asset.style,10],[asset.category_path,22],[asset.perspective,18],[asset.theme,15],[asset.medium,10],[asset.family,16],[asset.category,9],[asset.variant,7],[asset.capabilities,12],[asset.interfaces,12],[asset.slot_interfaces,12]
    ];
    let total=0;
    for(const term of terms){
      let best=0;
      for(const [value,weight] of fields){
        if(value==null)continue;
        const direct=contains(value,term)*weight;
        const equivalent=Math.max(0,...[...(aliases.get(term)||[])].filter(v=>v!==term).map(v=>contains(value,v)*weight*.75));
        best=Math.max(best,direct,equivalent);
      }
      if(!best)return 0;
      total+=best;
    }
    const q=clean(query);
    if([asset.id,asset.name,...(asset.aliases||[])].some(v=>clean(v)===q))total+=1200;
    return total;
  }
  const property=(a,key)=>key==='capability'?a.capabilities||[]:
    key==='interface'?[...new Set([...(a.interfaces||[]),...(a.slot_interfaces||[])])]:
    key==='subject'?a.subjects||[]:
    key==='review'?(a.legacy?a.review_status||'':a.visual_qa?'visual-'+a.visual_qa:''):
    key==='status'?(a.legacy?'archive':'published'):
    key==='animated'?(a.animated?'yes':'no'):
    key==='experience'?(a.showcases?.length?'playable':''):
    key==='license'?a.license||'':
    a[key]||'';
  function rankWithScore(a,query,relevance){
    if(query.trim())return relevance+(a.kind==='composition'?14:0)+(a.legacy?0:12)+(a.showcases?.length?140:0);
    return relevance+(a.legacy?0:250)+(a.kind==='composition'?120:a.kind==='sequence'?60:a.kind==='state_set'?35:0)+(a.showcases?.length?70:0);
  }
  function rank(a,query,synonyms={}){
    return rankWithScore(a,query,score(a,query,synonyms));
  }
  // Presentation only: direct stable IDs remain accessible.
  function visible(a,p){
    const role=a.discovery||'standalone';
    if(p.query?.trim()===a.id)return true;
    if(role==='hidden')return false;
    if(p.scope==='components')return role==='component';
    if(p.scope==='all')return true;
    return role==='standalone';
  }
  // Compute query relevance once and count self-excluding facets in the
  // same pass. Archive options stay discoverable even on the default landing.
  function evaluate(entries,params={},wantResults=true,wantFacets=true){
    const p={query:'',sort:'recommended',...params};
    const selected=FILTERS.filter(key=>p[key]);
    const hasDiscovery=Boolean(p.query.trim()||selected.length);
    const histograms=wantFacets?Object.fromEntries(FILTERS.map(key=>[key,new Map()])):null;
    const ranked=[];
    for(const a of entries){
      if(!visible(a,p))continue;
      let mismatch=null,excluded=false;
      for(const key of selected){
        const actual=property(a,key),wanted=p[key];
        if(Array.isArray(actual)?actual.includes(wanted):actual===wanted)continue;
        if(mismatch!==null||!wantFacets){excluded=true;break;}
        mismatch=key;
      }
      if(excluded)continue;
      const relevance=score(a,p.query,p.synonyms);
      if(!relevance)continue;
      if(wantResults&&mismatch===null&&(!a.legacy||hasDiscovery)){
        ranked.push({a,score:rankWithScore(a,p.query,relevance)});
      }
      if(wantFacets){
        for(const key of mismatch===null?FILTERS:[mismatch]){
          const actual=property(a,key),values=Array.isArray(actual)?actual:[actual],histogram=histograms[key];
          for(const value of values)if(value)histogram.set(value,(histogram.get(value)||0)+1);
        }
      }
    }
    ranked.sort((x,y)=>p.sort==='name'?String(x.a.name||x.a.id).localeCompare(String(y.a.name||y.a.id))||x.a.id.localeCompare(y.a.id):
      p.sort==='newest'?String(y.a.published).localeCompare(String(x.a.published))||y.score-x.score||x.a.id.localeCompare(y.a.id):
      y.score-x.score||String(y.a.published).localeCompare(String(x.a.published))||x.a.id.localeCompare(y.a.id));
    const facets=wantFacets?Object.fromEntries(FILTERS.map(key=>[key,[...histograms[key]].map(([value,count])=>({value,count})).sort((a,b)=>b.count-a.count||a.value.localeCompare(b.value))])):null;
    return {results:ranked.map(x=>x.a),facets};
  }
  const results=(entries,params={})=>evaluate(entries,params,true,false).results;
  const facets=(entries,params={})=>evaluate(entries,params,false,true).facets;
  const browse=(entries,params={})=>evaluate(entries,params);
  // Directory counts use the same visible/matches contract as the gallery.
  function directory(entries,params={}){
    return facets(entries.filter(a=>!a.legacy),params);
  }
  return Object.freeze({tokens,score,rank,results,facets,directory,browse});
});
