'use strict';
/* Pure search/ranking for published assets, tested independently of DOM. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;root.VisualAtlasSearch=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
  const clean=s=>String(s??'').normalize('NFKD').toLowerCase().replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();
  const tokens=s=>clean(s).split(/\s+/).filter(Boolean);
  function variants(term){const out=new Set([term]);if(term.endsWith('s')&&term.length>3)out.add(term.slice(0,-1));else out.add(term+'s');
    const related={healthbar:['health','meter'],health:['hp'],hp:['health'],bar:['meter'],meters:['meter'],slider:['slide'],heart:['life'],mana:['mp']};
    for(const v of related[term]||[])out.add(v);
    return out;
  }
  function score(a,query){const terms=tokens(query);if(!terms.length)return 1;
    const fields=[[a.name,55],[a.id,40],[(a.aliases||[]).join(' '),42],[(a.tags||[]).join(' '),28],[(a.subjects||[]).join(' '),20],[a.category,5],[a.style,8]];
    let total=0;
    for(const term of terms){let best=0;for(const [value,weight] of fields){const words=new Set(tokens(value));if(words.has(term)||[...variants(term)].some(v=>words.has(v)))best=Math.max(best,weight);else if([...words].some(w=>w.startsWith(term)&&term.length>2))best=Math.max(best,Math.round(weight*.65));}if(!best)return 0;total+=best;}
    if(clean(a.name)===clean(query))total+=150;
    return total;
  }
  function rank(a,query){return score(a,query)+(a.kind==='composition'?120:a.kind==='sequence'?65:a.kind==='state_set'?36:0)-(a.legacy?180:0);}
  function results(entries,{query='',kind='',pack='',sort='recommended'}={}){
    const ranked=entries.filter(a=>(!kind||a.kind===kind)&&(!pack||a.pack===pack)&&(!a.legacy||Boolean(query.trim())||pack==='legacy-icons')).map(a=>({a,score:score(a,query)})).filter(x=>x.score>0);
    ranked.sort((x,y)=>sort==='name'?x.a.name.localeCompare(y.a.name):sort==='newest'?y.a.published.localeCompare(x.a.published)||rank(y.a,query)-rank(x.a,query)||x.a.id.localeCompare(y.a.id):rank(y.a,query)-rank(x.a,query)||y.a.published.localeCompare(x.a.published)||x.a.id.localeCompare(y.a.id));
    return ranked.map(x=>x.a);
  }
  return Object.freeze({tokens,score,rank,results});
});