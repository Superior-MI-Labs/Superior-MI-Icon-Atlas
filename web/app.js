'use strict';
/* Unified public browser. The manifest is authoritative; this is a derived read-only index. */
(()=>{
  const $=id=>document.getElementById(id);
  const {VisualAtlasRenderer:Renderer,VisualAtlasSlots:Slots,VisualAtlasTimeline:Timeline,VisualAtlasVisualCore:VisualCore,VisualAtlasInteraction:Interactions,VisualAtlasInputs:Inputs,VisualAtlasCollections:Collections}=window;
  const assets=new Map(),collections=new Map(),pending=new Map(),loaded=new Map();
  let entries=[],matches=[],shown=0,current=null,clock=0,playing=true,previous=0;
  let preset=null,chosenState=null,controls={},slotChoices={};
  let activePreview=0,cardObserver,detailRendering=false;
  let synonyms={},styleLabels={};
  const FACETS=['kind','pack','domain','style','subject','status','review','license','animated'];
  const legacyImageCache=new Map();
  const PAGE=24;
  const renderer=Renderer.create({getAsset:id=>assets.get(id),getImage:imageFor,slots:Slots,timeline:Timeline,visualCore:VisualCore});
  const notify=message=>{const box=$('notice');box.textContent=message;box.hidden=false;clearTimeout(notify.timer);notify.timer=setTimeout(()=>box.hidden=true,3200);};
  const human=value=>String(value).replace(/[._-]+/g,' ').replace(/\\b\\w/g,m=>m.toUpperCase());
  function filterValues(){return Object.fromEntries(FACETS.map(id=>[id,$(id).value]));}
  function facetLabel(key,value){
    if(key==='pack')return collections.get(value)?.name||value;
    if(key==='style')return styleLabels[value]?.label||human(value);
    if(key==='animated')return value==='yes'?'Animated':'Static';
    if(key==='status')return value==='archive'?'Legacy archive':'Published';
    if(key==='review')return value==='reviewed'?'Semantics reviewed':'Needs visual review';
    if(key==='kind')return value==='state_set'?'State variants':human(value);
    if(key==='subject')return value.split('.').map(human).join(' › ');
    return human(value);
  }
  function refreshFacets(params){
    const counts=VisualAtlasSearch.facets(entries,params);
    for(const key of FACETS){
      const control=$(key),selected=control.value;
      const empty=control.options[0]?.textContent?.replace(/ \\(.*\\)$/,'')||'All';
      control.replaceChildren(new Option(empty,''));
      for(const {value,count} of counts[key])control.add(new Option(facetLabel(key,value)+' ('+count+')',value));
      if(selected&&!counts[key].some(item=>item.value===selected))control.add(new Option(facetLabel(key,selected)+' (0)',selected));
      control.value=selected;
    }
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
      const response=await fetch(pack.zip);if(!response.ok)throw Error('Could not retrieve '+pack.name);
      const blob=await response.blob();if(blob.size>120*1024*1024)throw Error('Oversize collection');
      const zip=await JSZip.loadAsync(blob,{checkCRC32:true});
      const definitions=[];let index=null;
      for(const file of Object.values(zip.files)){
        if(file.dir||!/\.json$/i.test(file.name)||file._data?.uncompressedSize>1024*1024)continue;
        const doc=JSON.parse(await file.async('string'));
        if(doc.schema==='smi-visual-pack/1')definitions.push({path:file.name,pack:doc});
        if(doc.schema==='smi-visual-collection/1'){
          if(index)throw Error('Multiple collection indexes');index=doc;
        }
      }
      if(!definitions.length)throw Error('No visual manifest found');
      const resolved=Collections.resolveCollection(index,definitions,pack.name);
      const merged=resolved.pack;
      if(Slots.validate(merged).length)throw Error('Invalid compatibility definitions in '+pack.name);
      const textureMap=new Map();
      for(const a of merged.assets){
        if(assets.has(a.id))throw Error('Duplicate public asset '+a.id);
        assets.set(a.id,{...a,pack:id});
      }
      for(const [key,t] of Object.entries(merged.textures)){
        const member=zip.file(t.path);if(!member)throw Error('Missing source texture: '+t.path);
        textureMap.set(key,{info:t,file:member});
      }
      const manifests=[merged];
      const cache={zip,textureMap,images:new Map(),manifests};loaded.set(id,cache);return cache;
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
  function bindTextures(packId){for(const a of assets.values())if(a.pack===packId&&a.kind==='region'&&!a.texture.includes('::'))a.texture=packId+'::'+a.texture;}
  async function ready(id){if(id==='legacy-icons')return null;const data=await loadCollection(id);bindTextures(id);return data;}
  async function paint(canvas,entry,time=0,options={}){
    await ready(entry.pack);
    const asset=assets.get(entry.id);
    const values=Inputs.reconcile(asset,options.controls||{},Slots.resolve(asset,options.preset).inputs);
    const size=renderer.sizeFor(entry.id,new Set(),values),width=Math.max(1,size[0]),height=Math.max(1,size[1]);
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
  function update(){
    const query=$('search').value,params={...filterValues(),query,synonyms,sort:$('sort').value};
    refreshFacets(params);activeChips();
    matches=VisualAtlasSearch.results(entries,params);shown=0;$('gallery').replaceChildren();
    $('count').textContent=matches.length.toLocaleString()+' matches';
    const refining=Boolean(query.trim()||FACETS.some(key=>params[key]));
    $('browse-title').textContent=query?'Search results':refining?'Filtered assets':'Explore assets';
    $('browse-subtitle').textContent=refining?'Results are ranked by matching names, synonyms and manifest metadata.':'Finished compositions first. Explore icon collections and styles with filters.';
    if(!matches.length){$('gallery').textContent='No matching assets. Remove a filter or try another keyword.';$('more').hidden=true;return;}
    more();
  }
  function card(a){const node=document.createElement('button');node.type='button';node.className='asset-tile';node.dataset.assetId=a.id;
    const art=document.createElement('div');art.className='art checker';const canvas=document.createElement('canvas');canvas.width=190;canvas.height=108;canvas.setAttribute('aria-hidden','true');art.append(canvas);
    const body=document.createElement('div');body.className='tile-details';const kind=document.createElement('span');kind.className='chip';kind.textContent=a.legacy?'Legacy · Review':a.kind==='composition'?'Ready-to-use':a.kind==='state_set'?'State variants':a.kind;
    const name=document.createElement('strong');name.textContent=a.name;const meta=document.createElement('div');meta.className='tile-meta';const label=document.createElement('span');label.textContent=a.style||'Visual asset';const src=document.createElement('span');src.textContent=collections.get(a.pack)?.name||a.pack;meta.append(label,src);body.append(kind,name,meta);node.append(art,body);
    node.onclick=()=>openDetail(a);if(cardObserver)cardObserver.observe(node);
    else paint(canvas,a,0,{card:true}).catch(()=>art.textContent='Preview unavailable');return node;}
  function more(){const frag=document.createDocumentFragment();for(const a of matches.slice(shown,shown+PAGE))frag.append(card(a));shown=Math.min(matches.length,shown+PAGE);$('gallery').append(frag);$('more').hidden=shown>=matches.length;}
  function valueCap(a,key){return Inputs.bounds(a,key,Inputs.reconcile(a,controls,Slots.resolve(a,preset).inputs))?.max??null;}
  function controlsFor(a){const area=$('controls');area.replaceChildren();
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
      const lab=document.createElement('label');lab.textContent=slot.label||slotName;const sel=document.createElement('select');for(const id of slot.options)sel.add(new Option(assets.get(id)?.name||id,id));sel.value=selected[slotName];sel.onchange=()=>{slotChoices[slotName]=sel.value};lab.append(sel);area.append(lab);
    }}
    const defaultValues=Inputs.reconcile(a,controls,Slots.resolve(a,preset).inputs);
    for(const [key,def] of Object.entries(a.inputs||{})){
      const lab=document.createElement('label');lab.textContent=key;let elem;
      if(def.type==='boolean'){elem=document.createElement('input');elem.type='checkbox';elem.checked=controls[key]??defaultValues[key];elem.onchange=()=>{controls[key]=elem.checked;};}
      else if(def.type==='number'){
        elem=document.createElement('input');elem.type='range';elem.min=def.min??0;
        elem.max=valueCap(a,key)??def.max??1;elem.step=def.step??1;
        elem.value=Math.min(Number(elem.max),controls[key]??defaultValues[key]);
        const info=document.createElement('output');info.textContent=elem.value+' / '+elem.max;
        elem.oninput=()=>{
          controls[key]=Number(elem.value);info.textContent=elem.value+' / '+elem.max;
          if((a.layers||[]).some(l=>l.repeat?.count_input===key)){
            for(const layer of a.layers.filter(l=>l.repeat?.count_input===key)){
              const valueKey=layer.repeat.value_input;
              controls[valueKey]=Math.min(valueCap(a,valueKey),controls[valueKey]??defaultValues[valueKey]);
            }
            controlsFor(a);
          }
        };
        lab.append(info);
      }
      else{elem=document.createElement('select');for(const item of def.values||[])elem.add(new Option(item,item));elem.value=controls[key]??defaultValues[key];elem.onchange=()=>{controls[key]=elem.value;};}
      lab.append(elem);area.append(lab);
    }
    for(const event of Object.keys(a.behavior?.on||{})){
      const button=document.createElement('button');button.textContent='Send '+event;button.onclick=()=>{try{const r=Interactions.dispatch(a,{...defaultValues,...controls},event);controls=r.values;controlsFor(a);notify(r.events.map(e=>e.name).join(', ')||'Event handled')}catch(e){notify(e.message)}};area.append(button);
    }
  }
  async function openDetail(a){current=a;clock=0;playing=true;preset=null;chosenState=null;controls={};slotChoices={};
    $('detail-title').textContent=a.name;$('detail-type').textContent=a.kind.replace('_',' ').toUpperCase();$('detail-id').textContent=a.id;
    $('detail-pack').textContent=collections.get(a.pack)?.name||a.pack;
    $('detail-meta').textContent=[a.category,a.style,a.license].filter(Boolean).join(' · ');
    $('download-pack').hidden=Boolean(a.legacy);
    $('open-builder').hidden=Boolean(a.legacy);
    if(!a.legacy){$('download-pack').href=collections.get(a.pack).zip;
      $('open-builder').href='builder.html?example='+encodeURIComponent(collections.get(a.pack).zip.split('/').at(-1))+'&asset='+encodeURIComponent(a.id);}
    $('detail-meta').textContent=[a.category,facetLabel('style',a.style||''),a.license,
      a.review_status&&facetLabel('review',a.review_status),
      a.legacy?'Archive candidate · rights review pending':''].filter(Boolean).join(' · ');
    const tags=$('detail-tags');tags.replaceChildren();
    for(const tag of [...new Set([...(a.subjects||[]),...(a.tags||[])])].slice(0,18)){
      const label=document.createElement('span');label.textContent=tag;tags.append(label);
    }
    $('tint-options').hidden=!a.legacy;$('tint-enabled').checked=false;
    try{
      await ready(a.pack);if(current?.id!==a.id)return;
      controlsFor(assets.get(a.id));$('detail').showModal();activePreview++;
      const url=new URL(location.href);url.searchParams.set('asset',a.id);
      history.replaceState(null,'',url);
    }catch(e){notify('Preview failed: '+e.message);}
  }
  async function downloadAsset(){if(!current)return;
    if(current.legacy){
      // One icon, one real cropped texture; no unrelated sheet cells in the ZIP.
      const asset=assets.get(current.id),src=await imageFor(asset.texture);
      const [x,y,w,h]=asset.rect_px,c=document.createElement('canvas');c.width=w;c.height=h;
      c.getContext('2d').drawImage(src,x,y,w,h,0,0,w,h);
      const png=await new Promise((resolve,reject)=>c.toBlob(b=>b?resolve(b):reject(Error('PNG encoding failed')),'image/png'));
      const zip=new JSZip();zip.file('textures/icon.png',png);
      const clean={...asset,texture:'icon'};for(const field of ['pack','legacy','rights_reviewed','review_status','category','published','previewable','animated','aliases'])delete clean[field];
      zip.file('manifest.json',JSON.stringify({schema:'smi-visual-pack/1',pack_id:'smi.legacy.icon.selection',version:'1.0.0',license:asset.license,description:'Historical icon export: verify rights before commercial redistribution',textures:{icon:{path:'textures/icon.png',width_px:w,height_px:h}},assets:[{...clean,rect_px:[0,0,w,h]}]},null,2)+'\n');
      zip.file('SOURCE-NOTICES.txt','Historical icon candidate. Rights review is pending. Original ID: '+asset.id+'\n');
      save(await zip.generateAsync({type:'blob',compression:'DEFLATE'}),current.id+'.zip');return;
    }
    const data=await ready(current.pack);const closure=new Set();function walk(id){if(closure.has(id))return;const a=assets.get(id);if(!a)throw Error('Missing dependency '+id);closure.add(id);Slots.refs(a).forEach(walk);}
    walk(current.id);const chosen=[...closure].map(id=>structuredClone(assets.get(id)));const required=new Set(chosen.filter(a=>a.kind==='region').map(a=>a.texture.split('::')[1]));
    const main=data.manifests[0];const zip=new JSZip();const defs={};
    for(const a of chosen){if(a.kind==='region')a.texture=a.texture.split('::')[1];for(const key of ['pack','sourcePack','sourceGroup','sourceLabel','ownerBag','source'])delete a[key];for(const contract of [...(a.implements||[]),...Object.values(a.slots||{}).map(s=>s.accepts)]){
      if(!main.interfaces?.[contract])throw Error('Missing compatible interface '+contract);defs[contract]=main.interfaces[contract];
    }}
    const textures=Object.fromEntries([...required].map(key=>[key,main.textures[key]]));
    for(const key of required){const t=data.textureMap.get(key);if(!t)throw Error('Missing texture '+key);zip.file(t.info.path,await t.file.async('blob'));}
    zip.file('manifest.json',JSON.stringify({schema:'smi-visual-pack/1',pack_id:main.pack_id+'.selection',version:main.version,description:'Portable asset: '+current.id,license:main.license,interfaces:defs,textures,assets:chosen},null,2)+'\n');
    zip.file('SOURCE-NOTICES.txt',`Original asset: ${current.id}\nSource: ${collections.get(current.pack).name}\nLicense: ${main.license}\nPreserve source rights and notices.\n`);
    const out=await zip.generateAsync({type:'blob',compression:'DEFLATE',compressionOptions:{level:6}});
    save(out,current.id+'.zip');
  }
  function save(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),15000);}
  function tick(ts){if(!previous)previous=ts;const dt=Math.min(80,ts-previous);previous=ts;if(playing)clock+=dt;
    const a=current;if(a&&$('detail').open&&!detailRendering){const token=activePreview;detailRendering=true;paint($('detail-canvas'),a,clock,{controls,state:chosenState,preset,slots:slotChoices}).catch(e=>{if(token===activePreview)notify(e.message)}).finally(()=>{detailRendering=false});$('time-value').textContent=(clock/1000).toFixed(1)+'s';}
    requestAnimationFrame(tick);
  }
  async function init(){
    const response=await fetch('public-catalog.json');if(!response.ok)throw Error('Public catalog unavailable');const index=await response.json();if(index.schema!=='smi-public-catalog/1')throw Error('Unsupported public catalog');
    entries=index.assets;if(!Array.isArray(entries)||!entries.length)throw Error('No assets in catalog');for(const pack of index.packs)collections.set(pack.id,pack);
    synonyms=index.synonyms||{};styleLabels=index.styles||{};
    for(const a of entries.filter(a=>a.legacy))assets.set(a.id,{...a,texture:'legacy-icons::'+a.texture});
    $('count').title=`${index.approved_count||0} approved assets and ${index.legacy_count||0} legacy icons`;

    cardObserver=new IntersectionObserver(es=>{for(const e of es)if(e.isIntersecting){cardObserver.unobserve(e.target);const a=entries.find(x=>x.id===e.target.dataset.assetId);if(a)paint(e.target.querySelector('canvas'),a,0,{card:true}).catch(()=>{e.target.querySelector('.art').textContent='Preview unavailable'});}}, {rootMargin:'260px'});
    update();
    const requested=new URLSearchParams(location.search).get('asset')||new URLSearchParams(location.search).get('icon');
    const found=requested&&entries.find(a=>a.id===requested);
    if(found)openDetail(found);
  }
  $('more').onclick=more;for(const id of ['search','sort',...FACETS])$(id).addEventListener('input',update);
  $('clear-filters').onclick=()=>{$('search').value='';for(const id of FACETS)$(id).value='';update()};
  $('copy-id').onclick=()=>{if(current)navigator.clipboard.writeText(current.id).then(()=>notify('Asset ID copied')).catch(()=>notify('Clipboard unavailable'))};
  $('copy-link').onclick=()=>{if(current){const url=new URL(location.href);url.searchParams.set('asset',current.id);navigator.clipboard.writeText(url.href).then(()=>notify('Asset link copied')).catch(()=>notify('Clipboard unavailable'))}};
  $('close').onclick=()=>$('detail').close();$('detail').addEventListener('close',()=>{
    current=null;activePreview++;
    const url=new URL(location.href);url.searchParams.delete('asset');url.searchParams.delete('icon');history.replaceState(null,'',url);
  });
  $('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play'};
  $('step').onclick=()=>{clock+=1000/12;playing=false;$('play').textContent='Play'};
  $('download-png').onclick=()=>{if(!current)return;const canvas=$('detail-canvas');canvas.toBlob(b=>b?save(b,current.id+'.png'):notify('PNG unavailable'),'image/png')};
  $('download-asset').onclick=()=>downloadAsset().catch(e=>notify('ZIP unavailable: '+e.message));
  requestAnimationFrame(tick);init().catch(e=>{$('browse-error').textContent=e.message;$('browse-error').hidden=false;$('count').textContent='Catalog unavailable';});
})();