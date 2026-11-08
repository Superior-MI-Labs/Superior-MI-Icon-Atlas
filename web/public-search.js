'use strict';
/* One pure query/facet engine for generated icon and visual-pack records. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;root.VisualAtlasSearch=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
  const clean=value=>String(value??'').normalize('NFKD').toLowerCase().replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
  const tokens=value=>clean(value).split(/\s+/).filter(Boolean);
  const FILTERS=['kind','pack','domain','style','subject','review','status','license','animated'];
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
      [asset.subjects,35],[asset.concept_id,35],[asset.domain,12],
      [asset.style,10],[asset.category,9],[asset.variant,7]
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
  const property=(a,key)=>key==='subject'?a.subjects||[]:
    key==='review'?a.review_status||'':
    key==='status'?(a.legacy?'archive':'published'):
    key==='animated'?(a.animated?'yes':'no'):
    key==='license'?a.license||'':
    a[key]||'';
  function matches(a,params,ignore=''){
    for(const key of FILTERS){
      if(key===ignore||!params[key])continue;
      const actual=property(a,key),wanted=params[key];
      if(Array.isArray(actual)?!actual.includes(wanted):actual!==wanted)return false;
    }
    return !params.query||score(a,params.query,params.synonyms)>0;
  }
  function rank(a,query,synonyms={}){
    const relevance=score(a,query,synonyms);
    if(query.trim())return relevance+(a.kind==='composition'?14:0)+(a.legacy?0:12);
    return relevance+(a.legacy?0:250)+(a.kind==='composition'?120:a.kind==='sequence'?60:a.kind==='state_set'?35:0);
  }
  function results(entries,params={}){
    const p={query:'',sort:'recommended',...params},hasDiscovery=Boolean(p.query.trim()||FILTERS.some(k=>p[k]));
    const ranked=entries.filter(a=>matches(a,p)&&(!a.legacy||hasDiscovery)).map(a=>({a,score:rank(a,p.query,p.synonyms)}));
    ranked.sort((x,y)=>p.sort==='name'?String(x.a.name||x.a.id).localeCompare(String(y.a.name||y.a.id))||x.a.id.localeCompare(y.a.id):
      p.sort==='newest'?String(y.a.published).localeCompare(String(x.a.published))||y.score-x.score||x.a.id.localeCompare(y.a.id):
      y.score-x.score||String(y.a.published).localeCompare(String(x.a.published))||x.a.id.localeCompare(y.a.id));
    return ranked.map(x=>x.a);
  }
  function facets(entries,params={}){
    const counts={};
    const queryMatches=entries.filter(a=>!params.query||score(a,params.query,params.synonyms)>0);
    for(const key of FILTERS){
      const histogram=new Map();
      for(const a of queryMatches){
        if(!matches(a,{...params,query:''},key))continue;
        const values=Array.isArray(property(a,key))?property(a,key):[property(a,key)];
        for(const value of values){if(value)histogram.set(value,(histogram.get(value)||0)+1);}
      }
      counts[key]=[...histogram].map(([value,count])=>({value,count})).sort((a,b)=>b.count-a.count||a.value.localeCompare(b.value));
    }
    return counts;
  }
  return Object.freeze({tokens,score,rank,results,facets});
});
