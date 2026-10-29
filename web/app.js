"use strict";
// The browser is a read-only projection of manifest.json, not a second icon registry.
(() => {
  const catalog = window.ICON_ATLAS_DATA;
  if (!catalog || !Array.isArray(catalog.icons)) throw new Error('Missing generated catalog-data.js');
  const $ = id => document.getElementById(id);
  const sheetMap = new Map(catalog.sheets.map(s => [s.path, s]));
  const iconMap = new Map(catalog.icons.map(i => [i.id, i]));
  const images = new Map();
  const params = new URLSearchParams(location.search);
  const search = $('search'), domain = $('domain'), variant = $('variant'), quality = $('quality');
  const gallery = $('gallery'), detail = $('detail'), count = $('count'), more = $('more');
  const tintEnabled = $('tint-enabled'), tintColor = $('tint-color');
  let selected = null, visible = 0, matches = [];
  const PAGE_SIZE = 120;
  let noticeTimeout;

  function notify(message) {
    const box = $('notice'); box.textContent = message; box.hidden = false;
    clearTimeout(noticeTimeout); noticeTimeout = setTimeout(() => box.hidden = true, 3400);
  }
  function option(select, value, label) {
    const el = document.createElement('option'); el.value = value; el.textContent = label; select.appendChild(el);
  }
  [...new Set(catalog.icons.map(x => x.domain))].sort().forEach(x => option(domain, x, x));
  [...new Set(catalog.icons.map(x => x.variant))].sort().forEach(x => option(variant, x, x));
  [...new Set(catalog.icons.map(x => x.quality).filter(Boolean))].sort().forEach(x => option(quality, x, x));
  $('release').textContent = 'v' + String(catalog.version || 'dev');
  const stats = $('stats');
  for (const [n, label] of [[catalog.icons.length, 'ASSETS'], [new Set(catalog.icons.map(x => x.domain)).size, 'CATEGORIES'], [catalog.sheets.length, 'ATLAS SHEETS']]) {
    const block = document.createElement('div'); block.className='stat';
    const strong=document.createElement('strong'); strong.textContent=n.toLocaleString();
    const sub=document.createElement('span');sub.textContent=label;
    block.append(strong,sub);stats.appendChild(block);
  }
  function normalized(v) { return String(v || '').toLowerCase().replace(/[_\-.]+/g,' ').replace(/\s+/g,' ').trim(); }
  function matchesSearch(item, term) {
    if (!term) return true;
    const hay = normalized([item.id, item.concept_id, item.name, item.domain, ...(item.tags || [])].join(' '));
    return term.split(' ').every(token => hay.includes(token));
  }
  function applyFilters() {
    const term = normalized(search.value);
    matches = catalog.icons.filter(i => (!domain.value || i.domain === domain.value) && (!variant.value || i.variant === variant.value) && (!quality.value || i.quality === quality.value) && matchesSearch(i, term));
    gallery.replaceChildren(); visible = 0; count.textContent = matches.length.toLocaleString() + ' matching icons';
    appendPage();
  }
  function appendPage() {
    const end = Math.min(visible + PAGE_SIZE, matches.length);
    const fragment = document.createDocumentFragment();
    for (let i = visible; i < end; i++) fragment.appendChild(createCard(matches[i]));
    gallery.appendChild(fragment); visible = end; more.hidden = visible === matches.length;
  }
  function createCard(item) {
    const card = document.createElement('article'); card.className='item';
    const preview = document.createElement('button'); preview.className='thumb-btn'; preview.type='button'; preview.setAttribute('aria-label','Details for '+item.name+' '+item.variant);
    preview.addEventListener('click',()=>openIcon(item.id));
    const check=document.createElement('div');check.className='preview checker';
    const sprite=document.createElement('span'); sprite.className='sprite';sprite.setAttribute('aria-hidden','true');
    // Sprite position is read from manifest; CSS never owns an independent geometry table.
    sprite.style.backgroundImage='url('+JSON.stringify(item.sheet)+')';
    sprite.style.backgroundPosition=`-${item.rect_px.x}px -${item.rect_px.y}px`;
    sprite.style.width=item.rect_px.w+'px'; sprite.style.height=item.rect_px.h+'px';
    check.appendChild(sprite);preview.appendChild(check);
    const title=document.createElement('h3');title.textContent=item.name;
    const meta=document.createElement('div');meta.className='meta';
    const a=document.createElement('span');a.textContent=item.domain;
    const b=document.createElement('span');b.textContent=item.variant;
    meta.append(a,b);
    const id=document.createElement('div');id.className='idline';id.title=item.id;id.textContent=item.id;
    const buttons=document.createElement('div');buttons.className='card-actions';
    const inspect=document.createElement('button');inspect.className='compact'; inspect.type='button'; inspect.textContent='Inspect';inspect.onclick=()=>openIcon(item.id);
    const download=document.createElement('button');download.className='compact primary';download.type='button';download.textContent='PNG ↓';download.setAttribute('aria-label','Download '+item.id+'.png');
    download.onclick=()=>downloadIcon(item, false, download);
    buttons.append(inspect,download); card.append(preview,title,meta,id,buttons);return card;
  }
  function image(path) {
    if (!images.has(path)) {
      const promise = new Promise((resolve,reject)=>{
        const img = new Image();
        img.onload=()=>resolve(img);
        img.onerror=()=>reject(new Error('Could not load: '+path));
        img.src=path;
      }); images.set(path,promise);
    }
    return images.get(path);
  }
  async function makeCanvas(item, tinted) {
    const r=item.rect_px, canvas=document.createElement('canvas');
    canvas.width=r.w;canvas.height=r.h;
    const ctx=canvas.getContext('2d',{willReadFrequently:false});
    if (!ctx) throw new Error('Canvas unavailable');
    if (!tinted) {
      const sprite=await image(item.sheet);
      ctx.drawImage(sprite,r.x,r.y,r.w,r.h,0,0,r.w,r.h);
      return canvas;
    }
    const sheet=sheetMap.get(item.sheet);
    if (!sheet || !sheet.black_outline || !sheet.foreground_mask) throw new Error('Tint layers unavailable for this icon');
    const [outline,mask]=await Promise.all([image(sheet.black_outline),image(sheet.foreground_mask)]);
    ctx.drawImage(outline,r.x,r.y,r.w,r.h,0,0,r.w,r.h);
    const fg=document.createElement('canvas');fg.width=r.w;fg.height=r.h;
    const fc=fg.getContext('2d');fc.drawImage(mask,r.x,r.y,r.w,r.h,0,0,r.w,r.h);
    fc.globalCompositeOperation='source-in';fc.fillStyle=tintColor.value;fc.fillRect(0,0,r.w,r.h);
    ctx.drawImage(fg,0,0);
    return canvas;
  }
  async function showPreview() {
    if (!selected) return;
    const id=selected.id;
    try {
      const result=await makeCanvas(selected,tintEnabled.checked);
      if (!selected || selected.id !== id) return;
      const canvas=$('detail-canvas'); canvas.width=result.width; canvas.height=result.height;
      canvas.getContext('2d').drawImage(result,0,0);
    } catch(e) {notify('Preview unavailable: '+e.message);}
  }
  function openIcon(id) {
    const item=iconMap.get(id);if(!item)return;
    selected=item;
    $('detail-title').textContent=item.name+' · '+item.variant;
    $('detail-id').textContent=item.id;
    $('filename').textContent='Filename: '+item.id+'.png · transparent RGBA';
    const dl=$('attributes');dl.replaceChildren();
    const s=sheetMap.get(item.sheet);
    for(const [label,value] of [['Category',item.domain],['Variant',item.variant],['Concept',item.concept_id],['Texture',item.sheet],['Grid cell',Math.floor(item.rect_px.x/s.cell_px)+', '+Math.floor(item.rect_px.y/s.cell_px)],['Pixel rect',`${item.rect_px.x}, ${item.rect_px.y} · ${item.rect_px.w}×${item.rect_px.h}`],['License',item.license || 'See manifest'],['Quality',item.quality || 'Unreviewed'],['Search tags',(item.tags||[]).join(', ')]]) {
      const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;dl.append(dt,dd);
    }
    tintEnabled.checked=false;tintColor.disabled=true;
    const u=new URL(location.href);u.searchParams.set('icon',item.id);
    try { history.replaceState(null,'',u.href); } catch { /* local sandbox / opaque origin */ }
    detail.showModal(); showPreview();
  }
  function closeIcon(){detail.close(); selected=null;const u=new URL(location.href);u.searchParams.delete('icon');try {history.replaceState(null,'',u.href);} catch {/* local sandbox */}}
  async function downloadIcon(item,tinted,button) {
    button.disabled=true;
    try {
      const canvas=await makeCanvas(item,tinted);
      // Raw atlas crop, not a screenshot of the preview/checkerboard.
      const blob=await new Promise((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(new Error('PNG export unsupported')),'image/png'));
      const url=URL.createObjectURL(blob);
      const a=document.createElement('a');a.href=url;a.download=item.id+'.png';document.body.appendChild(a);a.click();a.remove();
      setTimeout(()=>URL.revokeObjectURL(url),15000);
      notify('Downloaded '+item.id+'.png');
    } catch(e){notify('Download failed: '+e.message+' · For local use, run python -m http.server 8000 in site/');}
    finally{button.disabled=false;}
  }
  async function copyText(value) {
    try{await navigator.clipboard.writeText(value);notify('Copied');}catch{notify('Clipboard unavailable. Select and copy the ID manually.');}
  }
  for(const ctl of [search,domain,variant,quality])ctl.addEventListener('input',applyFilters);
  more.addEventListener('click',appendPage);
  $('close').addEventListener('click',closeIcon);
  detail.addEventListener('cancel',event=>{event.preventDefault();closeIcon();});
  tintEnabled.addEventListener('change',()=>{tintColor.disabled=!tintEnabled.checked;showPreview();});
  tintColor.addEventListener('input',()=>{if(tintEnabled.checked)showPreview();});
  $('copy').addEventListener('click',()=>{if(selected)copyText(selected.id);});
  $('download').addEventListener('click',()=>{if(selected)downloadIcon(selected,tintEnabled.checked,$('download'));});
  $('share').addEventListener('click',()=>{if(selected){const u=new URL(location.href);u.searchParams.set('icon',selected.id);copyText(u.href);}});
  applyFilters();
  const direct=params.get('icon');if(direct&&iconMap.has(direct))openIcon(direct);
})();
