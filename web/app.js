'use strict';
/* Unified public browser. The manifest is authoritative; this is a derived read-only index. */
(()=>{
  const $=id=>document.getElementById(id);
  const {VisualAtlasRenderer:Renderer,VisualAtlasSlots:Slots,VisualAtlasTimeline:Timeline,VisualAtlasVisualCore:VisualCore,VisualAtlasInteractions:Interactions,VisualAtlasCollections:Collections}=window;
  const assets=new Map(),collections=new Map(),pending=new Map(),loaded=new Map();
  let entries=[],matches=[],shown=0,current=null,clock=0,playing=true,previous=0;
  let preset=null,chosenState=null,controls={},slotChoices={};
  let activePreview=0,cardObserver,detailRendering=false;
  const PAGE=24;
  const renderer=Renderer.create({getAsset:id=>assets.get(id),getImage:imageFor,slots:Slots,timeline:Timeline,visualCore:VisualCore});
  const notify=message=>{const box=$('notice');box.textContent=message;box.hidden=false;clearTimeout(notify.timer);notify.timer=setTimeout(()=>box.hidden=true,3200);};
  function filters(){const kind=$('kind'),pack=$('pack');for(const k of [...new Set(entries.map(a=>a.kind))].sort()){kind.add(new Option(k==='state_set'?'State variants':k[0].toUpperCase()+k.slice(1),k));}
    for(const p of collections.values())pack.add(new Option(p.name,p.id));}
  async function loadCollection(id){
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
  async function imageFor(key){const [packId,textureKey]=key.split('::');const data=await loadCollection(packId);const t=data.textureMap.get(textureKey);if(!t)throw Error('Missing texture '+key);
    if(!data.images.has(key)){data.images.set(key,(async()=>{
      const raw=await t.file.async('blob'),url=URL.createObjectURL(raw);
      try{return await new Promise((res,rej)=>{const img=new Image();img.onload=()=>res(img);img.onerror=()=>rej(Error('Texture decode failed'));img.src=url;});}
      finally{URL.revokeObjectURL(url);}
    })());}return data.images.get(key);}
  function bindTextures(packId){for(const a of assets.values())if(a.pack===packId&&a.kind==='region'&&!a.texture.includes('::'))a.texture=packId+'::'+a.texture;}
  async function ready(id){const data=await loadCollection(id);bindTextures(id);return data;}
  async function paint(canvas,entry,time=0,options={}){
    await ready(entry.pack);
    const size=renderer.sizeFor(entry.id),width=Math.max(1,size[0]),height=Math.max(1,size[1]);
    const maxW=options.card?200:520,maxH=options.card?124:255;
    const scale=Math.min(1,maxW/width,maxH/height);
    canvas.width=Math.max(1,Math.round(width*scale));canvas.height=Math.max(1,Math.round(height*scale));
    const ctx=canvas.getContext('2d');ctx.clearRect(0,0,canvas.width,canvas.height);
    const a=assets.get(entry.id),defaults=Object.fromEntries(Object.entries(a.inputs||{}).map(([k,v])=>[k,v.default]));
    await renderer.drawAsset(entry.id,ctx,0,0,canvas.width,canvas.height,time,{...defaults,...(options.controls||{})},options.state||null,new Set(),options.slots||null,options.preset||null);
  }
  function update(){
    const q=$('search').value,k=$('kind').value,p=$('pack').value,order=$('sort').value;
    matches=VisualAtlasSearch.results(entries,{query:q,kind:k,pack:p,sort:order});shown=0;$('gallery').replaceChildren();$('count').textContent=matches.length+' assets';
    $('browse-title').textContent=q?'Search results':'Recently published';$('browse-subtitle').textContent=q?'Results include finished compositions and reusable parts.':'Finished compositions appear first, followed by reusable source parts.';
    if(!matches.length){$('gallery').textContent='No matching published assets. Try slider, health, heart, or mana.';$('more').hidden=true;return;}
    more();
  }
  function card(a){const node=document.createElement('button');node.type='button';node.className='asset-tile';node.dataset.assetId=a.id;
    const art=document.createElement('div');art.className='art checker';const canvas=document.createElement('canvas');canvas.width=190;canvas.height=108;canvas.setAttribute('aria-hidden','true');art.append(canvas);
    const body=document.createElement('div');body.className='tile-details';const kind=document.createElement('span');kind.className='chip';kind.textContent=a.kind==='composition'?'Ready-to-use':a.kind==='state_set'?'State variants':a.kind;
    const name=document.createElement('strong');name.textContent=a.name;const meta=document.createElement('div');meta.className='tile-meta';const label=document.createElement('span');label.textContent=a.style||'Visual asset';const src=document.createElement('span');src.textContent=collections.get(a.pack)?.name||a.pack;meta.append(label,src);body.append(kind,name,meta);node.append(art,body);
    node.onclick=()=>openDetail(a);if(cardObserver)cardObserver.observe(node);
    else paint(canvas,a,0,{card:true}).catch(()=>art.textContent='Preview unavailable');return node;}
  function more(){const frag=document.createDocumentFragment();for(const a of matches.slice(shown,shown+PAGE))frag.append(card(a));shown=Math.min(matches.length,shown+PAGE);$('gallery').append(frag);$('more').hidden=shown>=matches.length;}
  function controlsFor(a){const area=$('controls');area.replaceChildren();const state={};
    if(a.kind==='state_set'){
      const lab=document.createElement('label');lab.textContent='Appearance';const sel=document.createElement('select');for(const key of Object.keys(a.states||{}))sel.add(new Option(key,key));sel.value=chosenState||a.default_state;sel.onchange=()=>{chosenState=sel.value;clock=0};lab.append(sel);area.append(lab);
    }
    if(a.kind==='composition'&&a.presets){const lab=document.createElement('label');lab.textContent='Preset';const sel=document.createElement('select');sel.add(new Option('Default',''));for(const name of Object.keys(a.presets))sel.add(new Option(name,name));sel.value=preset||'';sel.onchange=()=>{preset=sel.value||null;controls={};clock=0;controlsFor(a)};lab.append(sel);area.append(lab);}
    if(a.kind==='composition'&&a.slots){const selected=Slots.resolve(a,preset,slotChoices).slots;for(const [slotName,slot] of Object.entries(a.slots)){
      const lab=document.createElement('label');lab.textContent=slot.label||slotName;const sel=document.createElement('select');for(const id of slot.options)sel.add(new Option(assets.get(id)?.name||id,id));sel.value=selected[slotName];sel.onchange=()=>{slotChoices[slotName]=sel.value};lab.append(sel);area.append(lab);
    }}
    const defaultValues={...Slots.resolve(a,preset).inputs,...Object.fromEntries(Object.entries(a.inputs||{}).map(([k,v])=>[k,v.default]))};
    for(const [key,def] of Object.entries(a.inputs||{})){
      const lab=document.createElement('label');lab.textContent=key;let elem;
      if(def.type==='boolean'){elem=document.createElement('input');elem.type='checkbox';elem.checked=controls[key]??defaultValues[key];elem.onchange=()=>{controls[key]=elem.checked;};}
      else if(def.type==='number'){elem=document.createElement('input');elem.type='range';elem.min=def.min??0;elem.max=def.max??1;elem.step=def.step??1;elem.value=controls[key]??defaultValues[key];const info=document.createElement('span');info.textContent=elem.value;elem.oninput=()=>{controls[key]=Number(elem.value);info.textContent=elem.value;};lab.append(info);}
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
    $('download-pack').href=collections.get(a.pack).zip;
    $('open-builder').href='builder.html?example='+encodeURIComponent(collections.get(a.pack).zip.split('/').at(-1))+'&asset='+encodeURIComponent(a.id);
    try{await ready(a.pack);controlsFor(assets.get(a.id));$('detail').showModal();activePreview++;}catch(e){notify('Preview failed: '+e.message);}
  }
  async function downloadAsset(){if(!current)return;
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
    entries=index.assets;if(!Array.isArray(entries)||!entries.length)throw Error('No approved public assets');for(const pack of index.packs)collections.set(pack.id,pack);
    filters();
    cardObserver=new IntersectionObserver(es=>{for(const e of es)if(e.isIntersecting){cardObserver.unobserve(e.target);const a=entries.find(x=>x.id===e.target.dataset.assetId);if(a)paint(e.target.querySelector('canvas'),a,0,{card:true}).catch(()=>{e.target.querySelector('.art').textContent='Preview unavailable'});}}, {rootMargin:'260px'});
    update();
  }
  $('more').onclick=more;for(const id of ['search','kind','pack','sort'])$(id).addEventListener('input',update);
  $('close').onclick=()=>$('detail').close();$('detail').addEventListener('close',()=>{current=null;activePreview++});
  $('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'Pause':'Play'};
  $('step').onclick=()=>{clock+=1000/12;playing=false;$('play').textContent='Play'};
  $('download-png').onclick=()=>{if(!current)return;const canvas=$('detail-canvas');canvas.toBlob(b=>b?save(b,current.id+'.png'):notify('PNG unavailable'),'image/png')};
  $('download-asset').onclick=()=>downloadAsset().catch(e=>notify('ZIP unavailable: '+e.message));
  requestAnimationFrame(tick);init().catch(e=>{$('browse-error').textContent=e.message;$('browse-error').hidden=false;$('count').textContent='Catalog unavailable';});
})();