'use strict';
/* Unified public browser. The manifest is authoritative; this is a derived read-only index. */
(()=>{
  const $=id=>document.getElementById(id);
  const {VisualAtlasRenderer:Renderer,VisualAtlasSlots:Slots,VisualAtlasTimeline:Timeline,VisualAtlasVisualCore:VisualCore,VisualAtlasInteraction:Interactions,VisualAtlasInputs:Inputs,VisualAtlasCollections:Collections}=window;
  const legacyAssets=new Map(),collections=new Map(),conceptIndex=new Map(),pending=new Map(),loaded=new Map();
  const entryById=new Map();
  let entries=[],matches=[],shown=0,current=null,clock=0,playing=true,previous=0;
  let preset=null,chosenState=null,controls={},slotChoices={};
  let activePreview=0,cardObserver,detailRendering=false,lastDetailSignature=null;
  let synonyms={},styleLabels={},taxonomy={dimensions:{},families:{}},view='discover';
  const FACETS=['kind','pack','domain','style','subject','status','review','license','animated','experience','capability','interface','category_path','perspective','theme','medium','family'];
  const legacyImageCache=new Map();
  const PAGE=24;
  function contextFor(assets){return {assets,renderer:Renderer.create({getAsset:id=>assets.get(id),getImage:imageFor,slots:Slots,timeline:Timeline,visualCore:VisualCore})};}
  const legacyContext=contextFor(legacyAssets);
  const context=pack=>pack==='legacy-icons'?legacyContext:loaded.get(pack);
  const assetFor=entry=>context(entry.pack)?.assets.get(entry.id);
  const notify=message=>{const box=$('notice');box.textContent=message;box.hidden=false;clearTimeout(notify.timer);notify.timer=setTimeout(()=>box.hidden=true,3200);};
  const human=value=>String(value).replace(/[._-]+/g,' ').replace(/\b\w/g,m=>m.toUpperCase());
  function filterValues(){return Object.fromEntries(FACETS.map(id=>[id,$(id).value]));}
  function facetLabel(key,value){
    if(key==='pack')return collections.get(value)?.name||value;
    if(key==='family')return taxonomy.families[value]||human(value);
    if(taxonomy.dimensions[key]){const values=taxonomy.dimensions[key].values;return key==='category_path'?value.split('.').map((_,i,parts)=>values[parts.slice(0,i+1).join('.')]||human(parts[i])).join(' › '):values[value]||human(value);}
    if(key==='style')return styleLabels[value]?.label||human(value);
    if(key==='animated')return value==='yes'?'Animated':'Static';
    if(key==='status')return value==='archive'?'Legacy archive':'Published';
    if(key==='review')return ({reviewed:'Archive: semantics reviewed',unreviewed:'Archive: review pending','visual-reviewed':'Published: visual QA reviewed','visual-pending':'Published: visual QA pending'})[value]||human(value);
    if(key==='kind')return value==='state_set'?'State variants':human(value);
    if(key==='experience')return value==='playable'?'Playable demos':human(value);
    if(key==='subject')return value.split('.').map(human).join(' › ');
    if(key==='interface')return value;
    return human(value);
  }
  function refreshFacets(counts){
    for(const key of FACETS){
      const control=$(key),selected=control.value;
      const empty=control.options[0]?.textContent?.replace(/ \(.*\)$/,'')||'All';
      control.replaceChildren(new Option(empty,''));
      const options=key==='category_path'?[...counts[key]].sort((a,b)=>a.value.localeCompare(b.value)):counts[key];
      for(const {value,count} of options)control.add(new Option(facetLabel(key,value)+' ('+count+')',value));
      if(selected&&!counts[key].some(item=>item.value===selected))control.add(new Option(facetLabel(key,selected)+' (0)',selected));
      control.value=selected;
    }
    return counts;
  }
  function activeChips(){
    const box=$('active-filters');box.replaceChildren();
    for(const key of FACETS){
      const value=$(key).value;if(!value)continue;
      const button=document.createElement('button');button.type='button';
      button.textContent=facetLabel(key,value)+' ×';
      button.setAttribute('aria-label','Remove '+facetLabel(key,value)+' filter');
      button.onclick=()=>{$(key).value='';update()};box.append(button);
    }
  }
  async function loadCollection(id){
    if(id==='legacy-icons')return null;
    if(loaded.has(id))return loaded.get(id);
    if(pending.has(id))return pending.get(id);
    const loader=(async()=>{
      const pack=collections.get(id);if(!pack)throw Error('Unknown collection '+id);
      const blob=await VisualAtlasZip.fetchVerifiedArchive(VisualAtlasZip.packLocator(pack),{base:location.href});
      const {zip,resolved}=await VisualAtlasZip.read(blob,{JSZip,Collections,name:pack.name});
      const merged=resolved.pack;
      if(Slots.validate(merged).length)throw Error('Invalid compatibility definitions in '+pack.name);
      const textureMap=new Map(),assets=new Map();
      for(const a of merged.assets){
        assets.set(a.id,{...a,pack:id,...(a.kind==='region'?{texture:id+'::'+a.texture}:{})});
      }
      for(const [key,t] of Object.entries(merged.textures)){
        const member=zip.file(t.path);if(!member)throw Error('Missing source texture: '+t.path);
        textureMap.set(key,{info:t,file:member});
      }
      const manifests=[merged];
      const cache={zip,textureMap,images:new Map(),manifests,...contextFor(assets)};loaded.set(id,cache);return cache;
    })();pending.set(id,loader);try{return await loader;}finally{pending.delete(id);}
  }
  async function imageFor(key){const [packId,textureKey]=key.split('::');
    if(packId==='legacy-icons'){
      if(!legacyImageCache.has(textureKey))legacyImageCache.set(textureKey,new Promise((resolve,reject)=>{
        const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(Error('Legacy texture unavailable'));
        img.src=textureKey;
      }));
      return legacyImageCache.get(textureKey);
    }
    const data=await loadCollection(packId);const t=data.textureMap.get(textureKey);if(!t)throw Error('Missing texture '+key);
    if(!data.images.has(key)){data.images.set(key,(async()=>{
      const raw=await t.file.async('blob'),url=URL.createObjectURL(raw);
      try{return await new Promise((res,rej)=>{const img=new Image();img.onload=()=>res(img);img.onerror=()=>rej(Error('Texture decode failed'));img.src=url;});}
      finally{URL.revokeObjectURL(url);}
    })());}return data.images.get(key);}
  async function ready(id){return id==='legacy-icons'?legacyContext:loadCollection(id);}
  async function paint(canvas,entry,time=0,options={}){
    const {assets,renderer}=await ready(entry.pack);
    const asset=assets.get(entry.id);
    const values=Inputs.reconcile(asset,options.controls||{},Slots.resolve(asset,options.preset).inputs);
    const size=renderer.sizeFor(entry.id,new Set(),values,options.preset,options.slots),width=Math.max(1,size[0]),height=Math.max(1,size[1]);
    const maxW=options.card?200:520,maxH=options.card?124:255;
    const scale=Math.min(1,maxW/width,maxH/height);
    canvas.width=Math.max(1,Math.round(width*scale));canvas.height=Math.max(1,Math.round(height*scale));
    const ctx=canvas.getContext('2d');ctx.clearRect(0,0,canvas.width,canvas.height);
    await renderer.drawAsset(entry.id,ctx,0,0,canvas.width,canvas.height,time,values,options.state||null,new Set(),options.slots||null,options.preset||null);
    if(entry.legacy&&!options.card&&$('tint-enabled').checked){
      ctx.globalCompositeOperation='source-in';ctx.fillStyle=$('tint-color').value;
      ctx.fillRect(0,0,canvas.width,canvas.height);ctx.globalCompositeOperation='source-over';
    }
  }
  function browseURL(nextView,filters={}){
    const p=new URLSearchParams();if(nextView!=='discover')p.set('view',nextView);
    for(const [k,v] of Object.entries(filters))if(v)p.set(k,v);
    return '?'+p.toString();
  }
  function setControl(id,value){
    const el=$(id);if(el.tagName==='SELECT'&&value&&!Array.from(el.options).some(o=>o.value===value))el.add(new Option(facetLabel(id,value),value));
    el.value=value;
  }
  function navigate(nextView,filters={},push=true){
    view=nextView;
    $('search').value=filters.query||'';$('scope').value=filters.scope||'';$('sort').value=filters.sort||'recommended';
    for(const key of FACETS)setControl(key,filters[key]||'');
    if(push)history.pushState(null,'',browseURL(view,filters));
    update();
    if(push){closeNavigation();window.scrollTo({top:0,behavior:'instant'});}
  }
  function readRoute(){
    const p=new URLSearchParams(location.search),v=p.get('view');
    const filters=Object.fromEntries(['query','scope','sort',...FACETS].filter(k=>p.has(k)).map(k=>[k,p.get(k)]));
    navigate(v==='collections'?'collections':v==='assets'||Object.keys(filters).length?'assets':'discover',filters,false);
  }
  function syncRoute(params){
    const url=new URL(location.href);
    for(const key of ['view','query','scope','sort',...FACETS])url.searchParams.delete(key);
    if(view!=='discover')url.searchParams.set('view',view);
    for(const key of ['query','scope','sort',...FACETS])if(params[key]&&!(key==='sort'&&params[key]==='recommended'))url.searchParams.set(key,params[key]);
    history.replaceState(null,'',url);
  }
  const compactNav=window.matchMedia('(max-width:900px)'),compactFilters=window.matchMedia('(max-width:760px)');
  function setNavigation(open,restoreFocus=false){
    const enabled=compactNav.matches&&open;
    document.body.classList.toggle('nav-open',enabled);
    $('nav-toggle').setAttribute('aria-expanded',String(enabled));
    $('app-sidebar').inert=compactNav.matches&&!enabled;
    if(restoreFocus&&compactNav.matches)$('nav-toggle').focus();
  }
  function closeNavigation(){setNavigation(false,$('app-sidebar').contains(document.activeElement));}
  function setFilters(open){
    const visible=!compactFilters.matches||open;
    if(!visible&&$('facet-panel').contains(document.activeElement))$('filter-toggle').focus();
    $('facet-panel').hidden=!visible;
    $('filter-toggle').setAttribute('aria-expanded',String(visible));
    $('filter-toggle').textContent=visible?'Hide filters':'Show filters';
  }
  function renderView(){
    $('discover-hero').hidden=view!=='discover';$('discovery').hidden=view!=='discover';$('collection-directory').hidden=view!=='collections';
    $('browse-toolbar').hidden=view==='collections';$('browse-scope-toolbar').hidden=view==='collections';
    $('workspace-title').textContent=({discover:'Discover',assets:'Asset library',collections:'Collections'})[view];
    document.querySelector('.browse-layout').hidden=view==='collections';
    document.querySelectorAll('.browse-nav [data-view]').forEach(a=>{if(a.dataset.view===view)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')});
  }
  function directoryLink(label,count,filters,unit='assets'){
    const a=document.createElement('a');a.href=browseURL('assets',filters);a.className='directory-link';
    const title=document.createElement('strong');title.textContent=label;
    const meta=document.createElement('span');meta.className='muted';meta.textContent=count.toLocaleString()+' '+unit;
    a.append(title,meta);a.onclick=e=>{if(e.button||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;e.preventDefault();navigate('assets',filters)};
    return a;
  }
  function coverImage(entry){
    const img=document.createElement('img');img.src=entry.thumbnail;img.alt='';img.loading='lazy';img.decoding='async';img.className='directory-cover';img.onerror=()=>img.remove();return img;
  }
  function addCover(node,entry){
    if(entry?.thumbnail)node.prepend(coverImage(entry));
  }
  function builderURL(pack,id){
    return 'builder.html?example='+encodeURIComponent(pack.zip.split('/').at(-1))+'&asset='+encodeURIComponent(id);
  }
  function previewStrip(entries){
    const strip=document.createElement('div');strip.className='collection-covers';strip.setAttribute('aria-hidden','true');
    const sources=[...new Map(entries.filter(a=>a?.thumbnail).map(a=>[a.thumbnail,a])).values()].slice(0,3);
    for(const entry of sources)strip.append(coverImage(entry));
    if(!sources.length){const empty=document.createElement('span');empty.textContent='Open to explore';strip.append(empty);}
    return strip;
  }
  function collectionCard(pack,summary){
    const node=document.createElement('article');node.className='collection-card';node.dataset.pack=pack.id;
    const {standalone,components,previews}=summary||{standalone:0,components:0,previews:[]};
    const scope=standalone?'':'components',count=standalone||components;
    const link=directoryLink(pack.name,count,{pack:pack.id,scope},standalone?'standalone assets':'components');
    link.prepend(previewStrip([entryById.get(pack.cover_asset),...previews]));node.append(link);
    const meta=document.createElement('p');meta.className='collection-meta muted';
    meta.textContent=[pack.published,...(pack.license||[]),pack.visual_qa==='pending'?'Visual review pending':pack.visual_qa==='reviewed'?'Visual QA reviewed':'Visual review unspecified'].filter(Boolean).join(' · ');node.append(meta);
    if(standalone&&components){
      const componentLink=directoryLink('Reusable components',components,{pack:pack.id,scope:'components'},'components');
      componentLink.classList.add('collection-components');node.append(componentLink);
    }
    const actions=document.createElement('div');actions.className='collection-actions';
    const open=document.createElement('a');open.href=builderURL(pack,pack.entry);open.textContent='Open in Builder';
    const download=document.createElement('a');download.href=pack.zip;download.download='';download.textContent='Download ZIP';actions.append(open,download);node.append(actions);return node;
  }
  function renderDirectory(){
    const counts=VisualAtlasSearch.directory(entries,{});
    const cats=$('category-directory'),side=$('sidebar-categories'),hero=$('hero-art');cats.replaceChildren();side.replaceChildren();hero.replaceChildren();
    const top=counts.category_path.filter(x=>!x.value.includes('.'));
    const coverFor=value=>entries.find(a=>!a.legacy&&a.thumbnail&&a.discovery==='standalone'&&a.category_path?.includes(value))||entries.find(a=>!a.legacy&&a.thumbnail&&a.category_path?.includes(value));
    for(const {value,count} of top){
      const filters={category_path:value,status:'published'},label=facetLabel('category_path',value),cover=coverFor(value);
      const link=directoryLink(label,count,filters);addCover(link,cover);cats.append(link);
      const nav=directoryLink(label,count,filters);nav.dataset.category=value;side.append(nav);
    }
    // The hero is a collage of real, published previews, not invented scene artwork.
    for(const value of ['world','gui','items','characters','effects','icons']){
      const entry=coverFor(value);if(!entry?.thumbnail)continue;
      const img=document.createElement('img');img.src=entry.thumbnail;img.alt='';img.decoding='async';hero.append(img);
    }
    const perspectives=$('perspective-directory');perspectives.replaceChildren();
    for(const {value,count} of counts.perspective)perspectives.append(directoryLink(facetLabel('perspective',value),count,{perspective:value,status:'published'}));
    for(const [key,id] of [['medium','medium-directory'],['theme','theme-directory']]){
      const target=$(id);target.replaceChildren();
      for(const {value,count} of counts[key])target.append(directoryLink(facetLabel(key,value),count,{[key]:value,status:'published'}));
    }
    const archive=$('archive-directory');archive.replaceChildren(directoryLink('Legacy icon archive — rights review required',entries.filter(a=>a.legacy).length,{status:'archive'}));
    const published=[...collections.values()].filter(p=>p.zip).sort((a,b)=>String(b.published).localeCompare(String(a.published))||a.name.localeCompare(b.name));
    $('library-totals').textContent=(counts.status.find(x=>x.value==='published')?.count||0).toLocaleString()+' standalone assets · '+published.length+' collections';
    // Summarize actual public entries once, rather than scanning the catalog per card.
    const summaries=new Map(),familyPreviews=new Map();
    for(const a of entries){
      if(a.legacy||a.discovery==='hidden')continue;
      if(!summaries.has(a.pack))summaries.set(a.pack,{standalone:0,components:0,previews:[]});
      const summary=summaries.get(a.pack),component=a.discovery==='component';
      summary[component?'components':'standalone']++;
      if(!component&&a.thumbnail){
        if(summary.previews.length<3&&!summary.previews.some(x=>x.thumbnail===a.thumbnail))summary.previews.push(a);
        if(a.family){
          if(!familyPreviews.has(a.family))familyPreviews.set(a.family,[]);
          const candidates=familyPreviews.get(a.family);
          if(candidates.length<3&&!candidates.some(x=>x.pack===a.pack||x.thumbnail===a.thumbnail))candidates.push(a);
        }
      }
    }
    const makeCard=p=>collectionCard(p,summaries.get(p.id));
    const recent=$('recent-collections');recent.replaceChildren(...published.slice(0,6).map(makeCard));
    const families=new Map();for(const p of published){const key=p.family||'';if(!families.has(key))families.set(key,[]);families.get(key).push(p)}
    const familyDirectory=$('collection-family-directory');familyDirectory.replaceChildren();
    for(const {value,count} of counts.family){
      const link=directoryLink(facetLabel('family',value),count,{family:value,status:'published'},'standalone assets');
      link.classList.add('family-card');link.prepend(previewStrip(familyPreviews.get(value)||[]));
      familyDirectory.append(link);
    }
    $('hero-totals').textContent=$('library-totals').textContent;
    const directory=$('family-directory');directory.replaceChildren();
    for(const [key,packs] of families){const section=document.createElement('section'),heading=document.createElement('h4');heading.textContent=taxonomy.families[key]||'Other collections';section.append(heading);const grid=document.createElement('div');grid.className='directory-grid';grid.append(...packs.map(makeCard));section.append(grid);directory.append(section)}
  }
  function renderSubcategories(params,counts){
    const parent=params.category_path||'';
    const node=$('category-children');node.replaceChildren();if(!parent)return;
    const depth=parent.split('.').length+1;
    for(const {value,count} of counts.filter(x=>x.value.startsWith(parent+'.')&&x.value.split('.').length===depth)){
      const a=directoryLink(taxonomy.dimensions.category_path.values[value],count,{...filterValues(),query:params.query,scope:params.scope,sort:params.sort,category_path:value});node.append(a);
    }
    if(parent.includes('.')){const up=document.createElement('button');up.type='button';up.textContent='← Parent category';up.onclick=()=>{setControl('category_path',parent.slice(0,parent.lastIndexOf('.')));update()};node.prepend(up)}
  }
  function update(){
    const query=$('search').value,params={...filterValues(),query,synonyms,scope:$('scope').value,sort:$('sort').value};
    const {results,facets}=VisualAtlasSearch.browse(entries,params);
    refreshFacets(facets);activeChips();renderView();renderSubcategories(params,facets.category_path);syncRoute(params);
    document.querySelectorAll('#sidebar-categories [data-category]').forEach(el=>{if(params.category_path===el.dataset.category||params.category_path.startsWith(el.dataset.category+'.'))el.setAttribute('aria-current','true');else el.removeAttribute('aria-current')});
    matches=results;shown=0;if(cardObserver)for(const node of $('gallery').querySelectorAll('.asset-tile'))cardObserver.unobserve(node);$('gallery').replaceChildren();
    $('count').textContent=matches.length.toLocaleString()+' matches';
    const refining=Boolean(query.trim()||params.scope||FACETS.some(key=>params[key]));
    $('browse-title').textContent=query?'Search results':params.category_path?facetLabel('category_path',params.category_path):params.pack?facetLabel('pack',params.pack):refining?'Filtered assets':'Explore assets';
    $('browse-subtitle').textContent=refining?'Refine by perspective, theme, style, format and capabilities.':'Recommended assets. Browse categories or collections above to discover more.';
    if(!matches.length){$('gallery').textContent='No matching assets. Remove a filter or try another keyword.';$('shown-count').textContent='';$('more').hidden=true;return;}
    more();
  }
  async function paintCard(canvas,entry){
    if(entry.thumbnail){
      try{
        const img=new Image();img.src=entry.thumbnail;await img.decode();
        canvas.width=img.naturalWidth;canvas.height=img.naturalHeight;
        canvas.getContext('2d').drawImage(img,0,0);canvas.dataset.preview='thumbnail';return;
      }catch(_err){/* A missing cached preview must not break asset browsing. */}
    }
    await paint(canvas,entry,0,{card:true});canvas.dataset.preview='renderer';
  }
  function card(a){
    const node=document.createElement('button');node.type='button';node.className='asset-tile';node.dataset.assetId=a.id;
    const demos=a.showcases||[];
    const art=document.createElement('div');art.className='art checker';
    const canvas=document.createElement('canvas');canvas.width=190;canvas.height=108;canvas.setAttribute('aria-hidden','true');art.append(canvas);
    const body=document.createElement('div');body.className='tile-details';
    const kind=document.createElement('span');kind.className='chip';
    kind.textContent=demos.length?'Interactive demo':a.legacy?'Legacy · Review':a.discovery==='component'?'Component':a.kind==='composition'?'Ready-to-use':a.kind==='region'?'Sprite / image':facetLabel('kind',a.kind);
    const name=document.createElement('strong');name.textContent=a.name;name.title=a.name;
    const meta=document.createElement('div');meta.className='tile-meta';
    const label=document.createElement('span');label.textContent=demos.length?'Playable preview':a.style?facetLabel('style',a.style):'Visual asset';
    const source=document.createElement('span');source.textContent=collections.get(a.pack)?.name||a.pack;
    meta.append(label,source);body.append(kind,name,meta);node.append(art,body);
    node.onclick=()=>openDetail(a);
    if(cardObserver)cardObserver.observe(node);
    else paintCard(canvas,a).catch(()=>art.textContent='Preview unavailable');
    if(!demos.length)return node;
    // Sibling links avoid interactive elements nested inside a button.
    const wrapper=document.createElement('div');wrapper.className='showcase-card';wrapper.append(node);
    const actions=document.createElement('div');actions.className='showcase-actions';
    for(const demo of demos){
      const link=document.createElement('a');link.href=demo.page;link.className='showcase-link';
      link.textContent=demo.label;actions.append(link);
    }
    wrapper.append(actions);return wrapper;
  }
  function more(){const frag=document.createDocumentFragment();for(const a of matches.slice(shown,shown+PAGE))frag.append(card(a));shown=Math.min(matches.length,shown+PAGE);$('gallery').append(frag);$('shown-count').textContent=shown.toLocaleString()+' of '+matches.length.toLocaleString()+' shown';$('more').hidden=shown>=matches.length;}
  function controlsFor(a){const area=$('controls');area.replaceChildren();
    if(a.material){
      const m=a.material,p=a.visual_profile;
      const info=document.createElement('p');info.textContent='Surface profile: '+m.role.replaceAll('_',' ')+' · base color only · repeat '+m.repeat_intent.join(' / ')+' · seam '+(m.seam_screen?.screening||'not screened')+(m.suggested_coverage_m?' · suggested '+m.suggested_coverage_m.join(' × ')+' m (not calibrated)':'');area.append(info);
      if(p?.palette?.length){const colors=document.createElement('div');colors.setAttribute('aria-label','Measured color palette');colors.style.cssText='display:flex;flex-wrap:wrap;gap:4px';for(const c of p.palette){const chip=document.createElement('span');chip.title=c.hex+' · '+(c.weight_bp/100).toFixed(2)+'%';chip.setAttribute('aria-label',chip.title);chip.style.cssText='width:25px;height:25px;border:1px solid currentColor;border-radius:4px;background:'+c.hex;colors.append(chip);}area.append(colors);}
      const label=document.createElement('p');label.textContent='2 × 2 repeat preview (appearance only; inspect seams)';area.append(label);
      const repeated=document.createElement('canvas');repeated.dataset.materialRepeat='true';repeated.width=512;repeated.height=512;repeated.style.cssText='width:100%;max-width:320px;aspect-ratio:1;display:block';repeated.setAttribute('aria-label','Repeated material preview');area.append(repeated);
    }

    if(a.kind==='state_set'){
      const lab=document.createElement('label');lab.textContent='Appearance';
      const sel=document.createElement('select'),keys=Object.keys(a.states||{});
      for(const key of keys)sel.add(new Option(key,key));sel.value=chosenState||a.default_state;
      const slider=document.createElement('input');slider.type='range';slider.min=0;slider.max=keys.length-1;slider.step=1;slider.value=keys.indexOf(sel.value);
      const readout=document.createElement('output');readout.textContent=(Number(slider.value)+1)+' / '+keys.length;
      const apply=key=>{chosenState=key;sel.value=key;slider.value=keys.indexOf(key);readout.textContent=(Number(slider.value)+1)+' / '+keys.length;clock=0;};
      sel.onchange=()=>apply(sel.value);slider.oninput=()=>apply(keys[Number(slider.value)]);
      lab.append(sel,slider,readout);area.append(lab);
    }
    if(a.kind==='composition'&&a.presets){const lab=document.createElement('label');lab.textContent='Preset';const sel=document.createElement('select');sel.add(new Option('Default',''));for(const name of Object.keys(a.presets))sel.add(new Option(name,name));sel.value=preset||'';sel.onchange=()=>{preset=sel.value||null;controls={};clock=0;controlsFor(a)};lab.append(sel);area.append(lab);}
    if(a.kind==='composition'&&a.slots){const selected=Slots.resolve(a,preset,slotChoices).slots;for(const [slotName,slot] of Object.entries(a.slots)){
      const lab=document.createElement('label');lab.textContent=slot.label||slotName;const sel=document.createElement('select');for(const id of slot.options)sel.add(new Option(context(a.pack)?.assets.get(id)?.name||id,id));sel.value=selected[slotName];sel.onchange=()=>{slotChoices[slotName]=sel.value};lab.append(sel);area.append(lab);
    }}
    const defaultValues=Inputs.reconcile(a,controls,Slots.resolve(a,preset).inputs);
    for(const [key,def] of Object.entries(a.inputs||{})){
      const lab=document.createElement('label');lab.textContent=key;let elem;
      if(def.type==='boolean'){elem=document.createElement('input');elem.type='checkbox';elem.checked=controls[key]??defaultValues[key];elem.onchange=()=>{controls[key]=elem.checked;};}
      else if(def.type==='number'){
        const limits=Inputs.bounds(a,key,defaultValues);
        elem=document.createElement('input');elem.type='range';elem.dataset.inputKey=key;
        elem.min=limits.min;elem.max=limits.max;elem.step=limits.step;elem.value=defaultValues[key];
        const info=document.createElement('output');info.textContent=elem.value+' / '+elem.max;
        elem.oninput=()=>{
          controls=Inputs.reconcile(a,{...controls,[key]:Number(elem.value)},Slots.resolve(a,preset).inputs);
          // Update existing range elements; never replace a slider mid-drag.
          for(const item of area.querySelectorAll('input[data-input-key]')){
            const limit=Inputs.bounds(a,item.dataset.inputKey,controls);
            item.min=limit.min;item.max=limit.max;item.step=limit.step;
            item.value=controls[item.dataset.inputKey];
            item.parentElement.querySelector('output').textContent=item.value+' / '+limit.max;
          }
        };
        lab.append(info);
      }
      else{elem=document.createElement('select');for(const item of def.values||[])elem.add(new Option(item,item));elem.value=controls[key]??defaultValues[key];elem.onchange=()=>{controls[key]=elem.value;};}
      elem.dataset.inputKey=key;lab.append(elem);area.append(lab);
    }
    for(const event of Object.keys(a.behavior?.on||{})){
      const button=document.createElement('button');button.textContent='Send '+event;button.onclick=()=>{try{const r=Interactions.dispatch(a,{...defaultValues,...controls},event);controls=r.values;controlsFor(a);notify(r.events.map(e=>e.name).join(', ')||'Event handled')}catch(e){notify(e.message)}};area.append(button);
    }
  }
  function syncDetailInputs(a){
    const normalized=Inputs.reconcile(a,controls,Slots.resolve(a,preset).inputs);controls=normalized;
    for(const elem of $('controls').querySelectorAll('[data-input-key]')){
      const key=elem.dataset.inputKey,def=a.inputs?.[key];if(!def)continue;
      if(def.type==='number'){
        const bound=Inputs.bounds(a,key,normalized);elem.min=bound.min;elem.max=bound.max;elem.step=bound.step;elem.value=normalized[key];
        const output=elem.parentElement.querySelector('output');if(output)output.textContent=elem.value+' / '+bound.max;
      }else if(def.type==='boolean')elem.checked=normalized[key];else elem.value=normalized[key];
    }
  }
  function directPointer(e,drag){
    if(!current)return false;
    const a=assetFor(current),renderer=context(current.pack)?.renderer;if(!renderer||!Interactions.canPoint(a))return false;
    const canvas=$('detail-canvas'),rect=canvas.getBoundingClientRect();if(!rect.width||!rect.height)return false;
    const geometry=renderer.geometryFor(a.id,new Set(),Inputs.reconcile(a,controls,Slots.resolve(a,preset).inputs),preset,slotChoices);
    const point={x:(e.clientX-rect.left)/rect.width*geometry.width+geometry.minX,y:(e.clientY-rect.top)/rect.height*geometry.height+geometry.minY};
    const action=Interactions.pointerTarget(a,point,id=>renderer.sizeFor(id),drag);if(!action)return false;
    const result=Interactions.dispatch(a,Inputs.reconcile(a,controls,Slots.resolve(a,preset).inputs),action.event,action.payload);
    controls=result.values;syncDetailInputs(a);
    if(result.events.length)notify(result.events.map(item=>item.name).join(', '));
    return true;
  }
  // BEGIN capability discovery inspector
  // Browse the current published catalog only. This is a read-only presentation
  // of the collection core's evidence, never another matching or loading engine.
  let capabilityDiscovery=null,capabilityDiscoveryError=null;
  async function prepareCapabilityDiscovery(index,bytes){
    capabilityDiscovery=null;capabilityDiscoveryError=null;
    if(!(index.concepts||[]).some(c=>Object.keys(c.discovery_offers||{}).length))return;
    try{
      if(!globalThis.crypto?.subtle)throw Error('Catalog fingerprint unavailable in this context');
      const digest=[...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
      const resolver=Collections.createDiscoveryIndex(index,{catalog_sha256:digest});
      const representatives=new Map();
      // Use existing public entries and an exact same-owner, visible representation.
      // Stable ordering, no fabricated representation and no archive fetch.
      for(const entry of index.assets){
        const owner=conceptIndex.get(entry.concept_id);
        if(!owner||owner.pack!==entry.pack||entry.legacy||entry.discovery==='hidden')continue;
        const previous=representatives.get(owner.id);
        if(!previous||entry.id<previous.id)representatives.set(owner.id,entry);
      }
      capabilityDiscovery={resolver,representatives};
    }catch(error){
      // Old browsers, malformed optional metadata or an unavailable crypto API
      // must not prevent ordinary browsing, downloads or rendering.
      capabilityDiscoveryError='Capability discovery unavailable: '+error.message;
    }
  }
  function discoveryRef(kind,id,packId){
    const pack=collections.get(packId);
    return pack&&!pack.archived&&pack.zip&&/^[a-f0-9]{64}$/.test(pack.archive_sha256||'')?{kind,id,archive_sha256:pack.archive_sha256}:null;
  }
  function discoveryElement(tag,text){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;return node;}
  function discoveryTarget(ref){
    // Navigation is allowed only if the visible entry belongs to the exact
    // archive selected by the resolver. A pinned result is never redirected.
    const concept=ref.kind==='concept'?conceptIndex.get(ref.id):null;
    const entry=ref.kind==='asset'?entryById.get(ref.id):capabilityDiscovery?.representatives.get(ref.id);
    const owner=concept?.pack??entry?.pack;
    const current=discoveryRef(ref.kind,ref.id,owner);
    const valid=current&&current.archive_sha256===ref.archive_sha256;
    return {name:valid?(concept?.name||entry?.name||ref.id):ref.id,entry:valid&&entry&&!entry.legacy&&entry.discovery!=='hidden'&&entry.pack===owner?entry:null};
  }
  function discoveryEvidenceText(row){
    const r=row.requirement,found=row.evidence;
    const value=v=>v?.kind==='quantity'?`${v.value} ${v.unit}`:v&&typeof v==='object'&&Object.hasOwn(v,'value')?String(v.value):String(v);
    let expected=r.op==='quantity.range'?` ${r.min}–${r.max} ${r.unit}`:r.op==='fact.equals'?` = ${value(r.expected)}`:'';
    return `${r.scope} · ${r.op} · ${r.key}${expected}: ${row.status}${found?' (declared '+value(found.value)+', '+found.source.path+')':' (missing evidence)'}`;
  }
  function appendDiscoveryMatch(parent,match,direction){
    const ref=direction==='subject'?match.offer:match.subject,{name,entry}=discoveryTarget(ref);
    const row=discoveryElement('div');row.dataset.discoveryStatus=match.status;
    const label=direction==='subject'?`${human(match.role)} · ${name} · ${human(ref.offer_id)}`:`${name}`;
    const link=discoveryElement(entry?'button':'span',label);
    if(entry){link.type='button';link.onclick=()=>openDetail(entry);}
    row.append(link);
    const evidence=discoveryElement('details');
    evidence.append(discoveryElement('summary','Requirements and evidence'));
    for(const scope of ['concept','representation','context'])evidence.append(discoveryElement('p',`${human(scope)}: ${match.scopes[scope]}`));
    const facts=discoveryElement('ul');for(const item of match.evidence)facts.append(discoveryElement('li',discoveryEvidenceText(item)));evidence.append(facts);
    evidence.append(discoveryElement('small','Derived from declared metadata; not verification of artistic, rendering or host support.'));
    row.append(evidence);parent.append(row);
  }
  function appendDiscoveryResult(parent,result,direction){
    const labels={compatible:'Declared requirements matched',unknown:'Incomplete evidence',incompatible:'Requirements contradicted'};
    for(const status of ['compatible','unknown','incompatible']){
      const group=result.groups[status];if(!group.total)continue;
      const details=discoveryElement('details');details.dataset.discoveryGroup=status;details.open=status==='compatible';
      details.append(discoveryElement('summary',`${labels[status]} (${group.total})`));
      for(const match of group.matches)appendDiscoveryMatch(details,match,direction);
      if(group.total>group.matches.length)details.append(discoveryElement('p',`Showing ${group.matches.length} of ${group.total}; bounded preview.`));
      parent.append(details);
    }
  }
  function appendCapabilityDiscovery(a,list){
    if(a.legacy||a.discovery==='hidden')return;
    if(capabilityDiscoveryError){list.append(discoveryElement('small',capabilityDiscoveryError));return;}
    if(!capabilityDiscovery)return;
    const ref=discoveryRef('asset',a.id,a.pack);if(!ref)return;
    const {resolver}=capabilityDiscovery;
    // No host context is guessed by the public browser.
    let result;try{result=resolver.query({direction:'subject',ref,limit:8});}catch(error){list.append(discoveryElement('small','Capability discovery unavailable: '+error.message));return;}
    const panel=discoveryElement('section');panel.dataset.discoverySection='true';
    panel.append(discoveryElement('strong','Capability relationships'));
    panel.append(discoveryElement('p','Current catalog metadata. Options are not activated, attached or host-qualified. Context-dependent requirements remain unknown.'));
    appendDiscoveryResult(panel,result,'subject');
    const concept=conceptIndex.get(a.concept_id);
    if(concept?.pack===a.pack){
      const owner=discoveryRef('concept',concept.id,concept.pack);
      if(owner)for(const [offer_id,offer] of Object.entries(concept.discovery_offers||{}).sort(([a],[b])=>a<b?-1:a>b?1:0)){
        const details=discoveryElement('details');details.dataset.discoveryOffer=offer_id;
        details.append(discoveryElement('summary',`Find targets · ${human(offer.role)} · ${human(offer_id)}`));
        let evaluated=false;
        details.addEventListener('toggle',()=>{
          if(!details.open||evaluated)return;evaluated=true;
          try{const reverse=resolver.query({direction:'offer',ref:{...owner,offer_id},target_kind:'asset',limit:8});
            if(Object.values(reverse.groups).every(g=>!g.total))details.append(discoveryElement('p','No other eligible catalog entries to evaluate.'));
            else appendDiscoveryResult(details,reverse,'offer');
          }catch(error){details.append(discoveryElement('p','Unable to evaluate this offer: '+error.message));}
        });
        panel.append(details);
      }
    }
    if(Object.values(result.groups).some(g=>g.total)||panel.children.length>2)list.append(panel);
  }
  // END capability discovery inspector
  function relatedAssets(a){
    const panel=$('detail-components'),list=$('detail-related');list.replaceChildren();panel.open=false;
    const assets=context(a.pack).assets,root=assets.get(a.id);
    const children=root?[...Collections.dependencyClosure([a.id],id=>assets.get(id),Slots.refs)].filter(id=>id!==a.id):[];
    const parents=[...assets.values()].filter(x=>x.pack===a.pack&&Slots.refs(x).includes(a.id)).map(x=>x.id);
    const entryMap=new Map(entries.map(x=>[x.id,x]));
    for(const [label,ids] of [['Uses',children],['Used by',parents]]){
      if(!ids.length)continue;
      const title=document.createElement('strong');title.textContent=label+' ('+ids.length+')';list.append(title);
      for(const id of ids){const entry=entryMap.get(id);if(!entry)continue;
        const link=document.createElement('button');link.type='button';link.textContent=entry.name;
        link.title=id;link.onclick=()=>openDetail(entry);list.append(link);
      }
    }
    if(a.material){
      const picks=Collections.rankRelated(a,entries,{limit:8,categoryPrefixes:['textures','world.terrain','world.vegetation','world.props']});
      if(picks.length){const title=document.createElement('strong');title.textContent='Suggested matches (not verified compatibility)';list.append(title);for(const result of picks){const entry=entryMap.get(result.id);if(!entry)continue;const button=document.createElement('button');button.type='button';button.textContent=entry.name;button.title='Shared: '+result.shared.join(', ')+(result.color===null?' · color not measured':' · palette similarity '+Math.round(result.color*100)+'%');button.onclick=()=>openDetail(entry);list.append(button);}}
    }
    // Concept associations are discovery links, not required render dependencies.
    const concept=conceptIndex.get(a.concept_id);
    if(concept&&!a.legacy){
      const alternatives=entries.filter(x=>!x.legacy&&x.id!==a.id&&x.concept_id===concept.id);
      const associations=(concept.relationships||[]).filter(e=>!e.target.archive_sha256);
      const related=new Map(alternatives.map(x=>[x.id,{entry:x,label:'Representation'}]));
      for(const relation of associations){
        if(relation.target.kind==='asset'){
          const entry=entryMap.get(relation.target.id);
          if(entry&&entry.id!==a.id&&!entry.legacy)related.set(entry.id,{entry,label:relation.kind});
        }else{
          for(const entry of entries.filter(x=>!x.legacy&&x.concept_id===relation.target.id&&x.discovery!=='hidden').slice(0,8))
            if(entry.id!==a.id&&!related.has(entry.id))related.set(entry.id,{entry,label:relation.kind});
        }
      }
      if(related.size){
        const title=document.createElement('strong');title.textContent='Concept associations ('+related.size+')';list.append(title);
        for(const {entry,label} of [...related.values()].slice(0,40)){
          const link=document.createElement('button');link.type='button';link.textContent=label+' · '+entry.name;link.title=entry.id;link.onclick=()=>openDetail(entry);list.append(link);
        }
      }
    }
    appendCapabilityDiscovery(a,list);
    panel.hidden=!list.children.length;
  }
  async function openDetail(a){
    const token=++activePreview;current=null;clock=0;playing=true;preset=null;chosenState=null;controls={};slotChoices={};
    lastDetailSignature=null;$('play').textContent='Pause';$('time-value').textContent='0.0s';
    const canvas=$('detail-canvas');canvas.getContext('2d').clearRect(0,0,canvas.width,canvas.height);canvas.dataset.interactive='false';
    $('controls').replaceChildren();$('detail-related').replaceChildren();$('detail-components').hidden=true;
    for(const id of ['download-png','download-asset','copy-id','copy-link'])$(id).disabled=true;
    $('detail-title').textContent=a.name;$('detail-type').textContent=a.kind.replace('_',' ').toUpperCase();$('detail-id').textContent=a.id;
    $('detail-pack').textContent=collections.get(a.pack)?.name||a.pack;
    $('download-pack').hidden=Boolean(a.legacy);
    $('open-builder').hidden=Boolean(a.legacy);
    if(!a.legacy){$('download-pack').href=collections.get(a.pack).zip;
      $('open-builder').href=builderURL(collections.get(a.pack),a.id);}
    $('detail-meta').textContent=[a.category,facetLabel('style',a.style||''),a.license,
      a.review_status&&facetLabel('review',a.review_status),
      a.legacy?'Archive candidate · rights review pending':'',a.visual_qa==='pending'?'Visual QA pending':a.visual_qa==='reviewed'?'Visual QA reviewed':''].filter(Boolean).join(' · ');
    const classification=$('detail-classification');classification.replaceChildren();
    for(const key of ['category_path','perspective','theme','medium','family']){
      let values=Array.isArray(a[key])?a[key]:a[key]?[a[key]]:[];
      if(key==='category_path')values=values.filter(v=>!values.some(other=>other.startsWith(v+'.')));
      if(!values.length)continue;
      const dt=document.createElement('dt'),dd=document.createElement('dd');
      dt.textContent=key==='family'?'Collection family':taxonomy.dimensions[key]?.label||human(key);
      dd.textContent=values.map(v=>facetLabel(key,v)).join(' · ');classification.append(dt,dd);
    }
    const concept=!a.legacy&&conceptIndex.get(a.concept_id);
    if(concept){
      for(const [label,value] of [['Concept',concept.name],['Declared functions',(concept.capabilities||[]).join(' · ')],['Ruleset defaults',(concept.rulesets||[]).join(' · ')],['State axes',(concept.state_axes||[]).join(' · ')],['Representation',a.representation?.role]]){
        if(!value)continue;
        const dt=document.createElement('dt'),dd=document.createElement('dd');
        dt.textContent=label;dd.textContent=value;classification.append(dt,dd);
      }
    }
    const tags=$('detail-tags');tags.replaceChildren();
    for(const tag of [...new Set([...(a.subjects||[]),...(a.tags||[])])].slice(0,18)){
      const label=document.createElement('span');label.textContent=tag;tags.append(label);
    }
    const demos=$('detail-showcases');demos.replaceChildren();
    for(const demo of a.showcases||[]){
      const link=document.createElement('a');link.href=demo.page;link.className='showcase-link';
      link.textContent=demo.label;demos.append(link);
    }
    demos.hidden=!demos.children.length;
    $('tint-options').hidden=!a.legacy;$('tint-enabled').checked=false;
    try{
      await ready(a.pack);if(token!==activePreview)return;
      current=a;controlsFor(assetFor(a));relatedAssets(a);$('detail-canvas').dataset.interactive=String(Interactions.canPoint(assetFor(a)));if(!$('detail').open)$('detail').showModal();
      for(const id of ['download-asset','copy-id','copy-link'])$(id).disabled=false;
      const url=new URL(location.href);url.searchParams.set('asset',a.id);
      history.replaceState(null,'',url);
    }catch(e){if(token===activePreview){current=null;if($('detail').open)$('detail').close();notify('Preview failed: '+e.message);}}
  }
  async function downloadAsset(){if(!current)return;
    if(current.legacy){
      // One icon, one real cropped texture; no unrelated sheet cells in the ZIP.
      const entry=current,asset=assetFor(entry),src=await imageFor(asset.texture);
      const [x,y,w,h]=asset.rect_px,c=document.createElement('canvas');c.width=w;c.height=h;
      c.getContext('2d').drawImage(src,x,y,w,h,0,0,w,h);
      const png=await new Promise((resolve,reject)=>c.toBlob(b=>b?resolve(b):reject(Error('PNG encoding failed')),'image/png'));
      const zip=new JSZip();zip.file('textures/icon.png',png);
      const clean={...asset,texture:'icon'};for(const field of ['pack','legacy','rights_reviewed','review_status','category','published','previewable','animated','aliases','category_path','perspective','theme','medium','family'])delete clean[field];
      zip.file('manifest.json',JSON.stringify({schema:'smi-visual-pack/1',pack_id:'smi.legacy.icon.selection',version:'1.0.0',license:asset.license,description:'Historical icon export: verify rights before commercial redistribution',textures:{icon:{path:'textures/icon.png',width_px:w,height_px:h}},assets:[{...clean,rect_px:[0,0,w,h]}]},null,2)+'\n');
      zip.file('SOURCE-NOTICES.txt','Historical icon candidate. Rights review is pending. Original ID: '+asset.id+'\n');
      save(await zip.generateAsync({type:'blob',compression:'DEFLATE'}),entry.id+'.zip');return;
    }
    const {id:rootId,pack}=current;
    const data=await ready(pack),assets=data.assets;
    const closure=Collections.dependencyClosure([rootId],id=>assets.get(id),Slots.refs);
    const main=data.manifests[0],zip=new JSZip();
    await Collections.writeSelection(zip,{
      assets:[...closure].map(id=>assets.get(id)),rootId,packId:main.pack_id+'.selection',version:main.version,
      getInterfaces:()=>main.interfaces,previewProfiles:main.preview_profiles,statProfiles:main.stat_profiles,concepts:main.concepts,
      getTexture:async key=>{const t=data.textureMap.get(key.split('::')[1]);if(!t)throw Error('Missing texture '+key);return {...t.info,blob:await t.file.async('blob')};},
      sourceNotices:await Promise.all(Object.values(data.zip.files).filter(e=>!e.dir&&e._data?.uncompressedSize<=24*1024*1024&&(/(?:^|\/)(?:LICENSE[^/]*|NOTICE[^/]*|SOURCE-NOTICES[^/]*)$/i.test(e.name)||/(?:^|\/)LICENSES\//i.test(e.name))).map(async e=>({path:e.name,blob:await e.async('blob')}))),
      licenseText:async()=>{const response=await fetch('LICENSE');return response.ok?response.text():null;}
    });
    const out=await zip.generateAsync({type:'blob',compression:'DEFLATE',compressionOptions:{level:6}});
    save(out,rootId+'.zip');
  }
  function save(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),15000);}
  function tick(ts){if(!previous)previous=ts;const dt=Math.min(80,ts-previous);previous=ts;if(playing)clock+=dt;
    const a=current;if(a&&$('detail').open&&!detailRendering){
      const data=context(a.pack);
      if(data){
        if(!data.motion)data.motion=new Map();
        if(!data.motion.has(a.id)){
          const ids=Collections.dependencyClosure([a.id],id=>data.assets.get(id),Slots.refs);
          data.motion.set(a.id,[...ids].some(id=>{const x=data.assets.get(id);return x.kind==='sequence'||Boolean(x.duration_ms);}));
        }
        const animated=data.motion.get(a.id),signature=JSON.stringify([activePreview,a.id,controls,chosenState,preset,slotChoices,$('tint-enabled').checked,$('tint-color').value,animated?clock:0]);
        if(signature!==lastDetailSignature){
          const token=activePreview;detailRendering=true;
          // Render offscreen so a slow previous selection cannot overwrite the new one.
          const canvas=document.createElement('canvas');
          paint(canvas,a,clock,{controls:{...controls},state:chosenState,preset,slots:{...slotChoices}}).then(()=>{
            if(token!==activePreview||current?.id!==a.id)return;
            const target=$('detail-canvas');target.width=canvas.width;target.height=canvas.height;
            target.getContext('2d').drawImage(canvas,0,0);lastDetailSignature=signature;$('download-png').disabled=false;
            const repeat=$('controls').querySelector('canvas[data-material-repeat]');if(repeat){const ctx=repeat.getContext('2d'),w=repeat.width/2,h=repeat.height/2;ctx.clearRect(0,0,repeat.width,repeat.height);for(let y=0;y<2;y++)for(let x=0;x<2;x++)ctx.drawImage(canvas,x*w,y*h,w,h);}
          }).catch(e=>{if(token===activePreview){lastDetailSignature=signature;notify(e.message);}}).finally(()=>{detailRendering=false});
        }
      }
      $('time-value').textContent=(clock/1000).toFixed(1)+'s';
    }
    requestAnimationFrame(tick);
  }
  async function init(){
    const response=await fetch('public-catalog.json');if(!response.ok)throw Error('Public catalog unavailable');const bytes=await response.arrayBuffer();const index=JSON.parse(new TextDecoder().decode(bytes));if(index.schema!=='smi-public-catalog/1')throw Error('Unsupported public catalog');
    entries=index.assets;if(!Array.isArray(entries)||!entries.length)throw Error('No assets in catalog');for(const entry of entries)entryById.set(entry.id,entry);for(const pack of index.packs)collections.set(pack.id,pack);for(const concept of index.concepts||[])conceptIndex.set(concept.id,concept);
    await prepareCapabilityDiscovery(index,bytes);
    synonyms=index.synonyms||{};styleLabels=index.styles||{};taxonomy=index.browse||taxonomy;
    renderDirectory();
    for(const pack of index.packs.filter(p=>p.zip)){
      const group=document.createElement('div'),browse=document.createElement('button'),download=document.createElement('a');
      browse.type='button';browse.textContent=pack.name; browse.onclick=()=>{
        navigate('assets',{pack:pack.id});$('pack-directory').open=false;
      };
      download.href=pack.zip;download.download='';download.textContent='Download ZIP';group.append(browse,download);$('pack-links').append(group);
    }
    for(const a of entries.filter(a=>a.legacy))legacyAssets.set(a.id,{...a,texture:'legacy-icons::'+a.texture});
    $('count').title=`${index.discoverable_count??index.approved_count} standalone listings; ${index.approved_count||0} addressable published assets; ${index.legacy_count||0} legacy icons`;

    cardObserver=new IntersectionObserver(es=>{for(const e of es)if(e.isIntersecting){cardObserver.unobserve(e.target);const a=entryById.get(e.target.dataset.assetId);if(a)paintCard(e.target.querySelector('canvas'),a).catch(()=>{e.target.querySelector('.art').textContent='Preview unavailable'});}}, {rootMargin:'260px'});
    readRoute();
    const requested=new URLSearchParams(location.search).get('asset')||new URLSearchParams(location.search).get('icon');
    const found=requested&&entries.find(a=>a.id===requested);
    if(found)openDetail(found);
  }
  const previewCanvas=$('detail-canvas');let detailPointer=null;
  previewCanvas.addEventListener('pointerdown',e=>{try{if(directPointer(e,false)){e.preventDefault();detailPointer=e.pointerId;previewCanvas.setPointerCapture(e.pointerId);}}catch(err){notify(err.message)}});
  previewCanvas.addEventListener('pointermove',e=>{if(detailPointer!==e.pointerId)return;try{directPointer(e,true)}catch(err){notify(err.message)}});
  for(const event of ['pointerup','pointercancel','lostpointercapture'])previewCanvas.addEventListener(event,e=>{if(detailPointer===e.pointerId)detailPointer=null;});
  $('nav-toggle').onclick=()=>{
    const open=!document.body.classList.contains('nav-open');
    setNavigation(open);
    if(open)$('app-sidebar').querySelector('a').focus();
  };
  compactNav.addEventListener('change',()=>setNavigation(false));
  compactFilters.addEventListener('change',()=>setFilters(false));
  $('filter-toggle').onclick=()=>setFilters($('facet-panel').hidden);
  setNavigation(false);setFilters(false);
  document.addEventListener('pointerdown',e=>{
    if(document.body.classList.contains('nav-open')&&!$('app-sidebar').contains(e.target)&&!$('nav-toggle').contains(e.target))closeNavigation();
  });
  $('sidebar-archive').onclick=e=>{if(e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;e.preventDefault();navigate('assets',{status:'archive'})};
  document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();closeNavigation();$('search').focus()}if(e.key==='Escape'&&!$('detail').open)closeNavigation()});
  $('more').onclick=more;for(const id of ['search','sort','scope',...FACETS])$(id).addEventListener('input',()=>{view='assets';update()});
  document.querySelectorAll('[data-view]').forEach(a=>a.addEventListener('click',e=>{if(e.button||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;e.preventDefault();if(entries.length)navigate(a.dataset.view);else location.href=a.href}));
  window.addEventListener('popstate',()=>{if(entries.length)readRoute()});
  $('clear-filters').onclick=()=>navigate('discover',{},false);
  $('copy-id').onclick=()=>{if(current)navigator.clipboard.writeText(current.id).then(()=>notify('Asset ID copied')).catch(()=>notify('Clipboard unavailable'))};
  $('copy-link').onclick=()=>{if(current){const url=new URL(location.href);url.searchParams.set('asset',current.id);navigator.clipboard.writeText(url.href).then(()=>notify('Asset link copied')).catch(()=>notify('Clipboard unavailable'))}};
  $('close').onclick=()=>$('detail').close();$('detail').addEventListener('close',()=>{
    current=null;activePreview++;
    const url=new URL(location.href);url.searchParams.delete('asset');url.searchParams.delete('icon');history.replaceState(null,'',url);
  });
  $('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play'};
  $('step').onclick=()=>{clock+=1000/12;playing=false;$('play').textContent='Play'};
  $('download-png').onclick=()=>{if(!current)return;const id=current.id,canvas=$('detail-canvas');canvas.toBlob(b=>b?save(b,id+'.png'):notify('PNG unavailable'),'image/png')};
  $('download-asset').onclick=()=>downloadAsset().catch(e=>notify('ZIP unavailable: '+e.message));
  requestAnimationFrame(tick);init().catch(e=>{$('browse-error').textContent=e.message;$('browse-error').hidden=false;$('count').textContent='Catalog unavailable';});
})();