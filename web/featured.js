'use strict';
// Public pack metadata is generated from the ZIPs; never another authored registry.
(()=>{
  const root=document.getElementById('featured-list'), search=document.getElementById('featured-search');
  if(!root||!search)return;
  let packs=[];
  function update(){
    const tokens=search.value.toLowerCase().split(/\s+/).filter(Boolean);
    const selected=packs.filter(p=>tokens.every(token=>[p.title,p.description,...p.kinds,...p.tags].join(' ').toLowerCase().includes(token)));
    root.replaceChildren();
    for(const p of selected){
      const article=document.createElement('article');article.className='featured-card';
      const heading=document.createElement('h3');heading.textContent=p.title;
      const detail=document.createElement('p');detail.textContent=p.description||'Validated manifest-driven visual asset example.';
      const meta=document.createElement('p');meta.className='muted';meta.textContent=`${p.assets} assets · ${p.manifests} manifest(s) · ${p.kinds.join(', ')}`;
      const links=document.createElement('div');links.className='featured-actions';
      const preview=document.createElement('a');preview.href='builder.html?example='+encodeURIComponent(p.filename);preview.textContent='Open in Builder';
      const download=document.createElement('a');download.href='demo/'+encodeURIComponent(p.filename);download.download=p.filename;download.textContent='Download ZIP';
      links.append(preview,download);article.append(heading,detail,meta,links);root.append(article);
    }
    document.getElementById('featured-count').textContent=selected.length+' template packs';
  }
  search.addEventListener('input',update);
  fetch('featured-packs.json').then(r=>{if(!r.ok)throw Error('catalog unavailable');return r.json()}).then(d=>{
    if(d.schema!=='smi-featured-packs/1'||!Array.isArray(d.packs))throw Error('invalid catalog');
    packs=d.packs;update();
  }).catch(()=>{document.getElementById('featured-count').textContent='Example packs unavailable; browse icons below.';});
})();
