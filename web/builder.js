"use strict";
/* Superior MI Visual Atlas builder R0. Browser-local: no upload, no server-side state. */
(() => {
  const $ = id => document.getElementById(id);
  const Timeline = window.VisualAtlasTimeline;
  if(!Timeline)throw Error('Missing timeline-core.js');
  if (!window.JSZip) { $('builder-status').textContent = 'Local ZIP library missing: vendor/jszip.min.js'; return; }
  const library = new Map(); // unique asset ID -> authored/legacy asset
  const textures = new Map(); // namespaced texture ID -> {path, blob?, image?}
  const imports = new Set();
  const scene = { layers: [], selectedLayer:-1 };
  const timeline = { duration:2000, playback:'loop', exportFps:12 };
  const LIMIT_FRAMES=240;
  const ui = {selected:null, clock:0, playing:true, last:0, speed:1, controls:{}, isScene:false};
  const MAX_BYTES = 120 * 1024 * 1024, MAX_ENTRY = 24 * 1024 * 1024;
  const AI_URL = 'https://superior-mi-labs.github.io/Superior-MI-Icon-Atlas/ai-guide.html';
  const safePath = s => typeof s === 'string' && !!s && !s.startsWith('/') && !s.includes('\\') && !s.split('/').includes('..') && !s.includes(':') && !s.includes('\0');
  const range = (v,min,max) => Math.min(max,Math.max(min,Number(v)||0));
  const slug = s => String(s||'asset').toLowerCase().replace(/[^a-z0-9-]+/g,'-').replace(/^-|-$/g,'').slice(0,60)||'asset';
  const setStatus = (message,error=false) => { $('builder-status').textContent=message; $('builder-status').classList.toggle('error',error); };
  const asArray = v => Array.isArray(v)?v:[];
  const blobOf = (data,type) => new Blob([data],{type});
  const mime = path => /\.png$/i.test(path)?'image/png':/\.webp$/i.test(path)?'image/webp':/\.gif$/i.test(path)?'image/gif':'image/jpeg';
  const metaName = a => a.name || a.id;
  const binarySize = f => f.size ?? f.length ?? f.byteLength ?? 0;
  const keyframeProp = () => $('keyframe-property').value;

  // Convert the existing official icon catalog into regular region assets without changing its IDs.
  function addOfficialIcons() {
    const cat = window.ICON_ATLAS_DATA;
    if (!cat?.icons) return;
    for (const sheet of cat.sheets) {
      const key='official:'+sheet.path;
      textures.set(key,{path:sheet.path,src:sheet.path,license:'Apache-2.0',source:'Superior MI Icon Atlas'});
    }
    for (const icon of cat.icons) {
      const key='official:'+icon.sheet;
      library.set(icon.id,{
        id:icon.id,kind:'region',name:icon.name,rect_px:[icon.rect_px.x,icon.rect_px.y,icon.rect_px.w,icon.rect_px.h],
        texture:key,style:icon.style,tags:icon.tags||[],subjects:icon.subjects||[],license:'Apache-2.0',source:'Official Icon Atlas',review_status:icon.review_status
      });
    }
  }
  function validRect(r,w,h) {
    return Array.isArray(r)&&r.length===4&&r.every(Number.isInteger)&&r[0]>=0&&r[1]>=0&&r[2]>0&&r[3]>0&&r[0]+r[2]<=w&&r[1]+r[3]<=h;
  }
  function checkPack(pack) {
    if (pack?.schema!=='smi-visual-pack/1'||!pack.pack_id||!Array.isArray(pack.assets)||typeof pack.textures!=='object') throw Error('Expected a smi-visual-pack/1 manifest with assets and textures');
    if (pack.assets.length>3000||Object.keys(pack.textures).length>200) throw Error('Too many assets or textures in one pack');
    const ids=new Map();
    for (const a of pack.assets) {
      if (!a.id||ids.has(a.id)||library.has(a.id)) throw Error('Duplicate or existing asset ID: '+a.id);
      if (!['region','sequence','composition','state_set'].includes(a.kind)) throw Error('Invalid asset kind: '+a.id);
      ids.set(a.id,a);
    }
    const visiting=new Set(),seen=new Set();
    const walk = id => {
      if (visiting.has(id)) throw Error('Asset reference cycle at '+id);
      if (seen.has(id)) return;
      const a=ids.get(id);
      if (!a) { if (library.has(id)) return; throw Error('Missing asset reference: '+id); }
      visiting.add(id);
      let refs=[];
      if(a.kind==='region') {
        const t=pack.textures[a.texture];
        if(!t||!validRect(a.rect_px,t.width_px,t.height_px))throw Error('Invalid texture rectangle: '+id);
        if(a.nine_slice_px){ const s=a.nine_slice_px; if(s.length!==4||s.some(v=>!Number.isInteger(v)||v<0)||s[0]+s[2]>a.rect_px[2]||s[1]+s[3]>a.rect_px[3])throw Error('Invalid nine-slice: '+id); }
      } else if(a.kind==='sequence') {
        if(!a.frames?.length||!(a.default_fps>0))throw Error('Invalid sequence: '+id);
        refs=a.frames.map(f=>f.asset);
        if(a.frames.some(f=>f.duration_ms!==undefined&&!(f.duration_ms>0)))throw Error('Invalid frame duration: '+id);
      } else if(a.kind==='state_set') {
        if(!a.states?.[a.default_state])throw Error('Invalid default state: '+id);
        refs=Object.values(a.states);
      } else if(a.kind==='composition') {
        if(!Array.isArray(a.layers)||!a.layers.length||!a.size_px||a.size_px.length!==2)throw Error('Invalid composition: '+id);
        if(a.duration_ms!==undefined&&(!Number.isInteger(a.duration_ms)||a.duration_ms<1||a.duration_ms>600000))throw Error('Invalid animation duration: '+id);
        if(a.playback&&!['once','loop','pingpong'].includes(a.playback))throw Error('Invalid playback mode: '+id);
        refs=a.layers.map(l=>l.asset);
        for(const l of a.layers){
          for(const k of [l.visible_when?.input,l.clip?.input,l.state_from_input,l.position_from_input?.input].filter(Boolean))if(!a.inputs?.[k])throw Error('Unknown composition input '+k+' in '+id);
          const issues=Timeline.validateTracks(l.tracks,a.duration_ms||undefined,[],id+'/'+l.id);
          if(issues.length)throw Error(issues[0]);
        }
      }
      refs.forEach(walk);
      visiting.delete(id); seen.add(id);
    };
    pack.assets.forEach(a=>walk(a.id));
    for(const [id,t] of Object.entries(pack.textures)){
      if(!t||!safePath(t.path)||!Number.isInteger(t.width_px)||!Number.isInteger(t.height_px)||t.width_px<1||t.height_px<1||t.width_px>8192||t.height_px>8192)throw Error('Unsafe or invalid texture: '+id);
    }
  }
  function resolveZipPath(base,path){
    const p=[base,path].filter(Boolean).join('/').replace(/\/+/g,'/');
    if(!safePath(p))throw Error('Unsafe path in imported pack: '+p);
    return p;
  }
  async function importPack(pack,getTexture,packDirectory='') {
    checkPack(pack);
    let total=0;
    const pending=[];
    for(const [key,t] of Object.entries(pack.textures)){
      const path=resolveZipPath(packDirectory,t.path),data=await getTexture(path,t.path);
      if(!data) throw Error('Missing texture '+t.path);
      total+=binarySize(data); if(binarySize(data)>MAX_ENTRY||total>MAX_BYTES)throw Error('Imported textures exceed size limits');
      const blob=data instanceof Blob?data:blobOf(data,mime(t.path));
      const img=await imageFromBlob(blob);
      if(img.naturalWidth!==t.width_px||img.naturalHeight!==t.height_px) throw Error('Texture dimensions disagree with manifest: '+t.path);
      pending.push([key,t,blob,img]);
    }
    const prefix='local:'+slug(pack.pack_id)+':'+Date.now().toString(36)+':';
    for(const [key,def,blob,img] of pending){textures.set(prefix+key,{blob,path:def.path,image:img,source:pack.pack_id,license:pack.license||'UNSPECIFIED'});}
    for(const a of pack.assets){library.set(a.id,{...a,texture:a.texture?prefix+a.texture:undefined,source:pack.pack_id,license:a.license||pack.license||'UNSPECIFIED'});}
    imports.add(pack.pack_id); ui.selected=pack.assets.filter(a=>a.kind==='composition').at(-1)?.id||pack.assets.at(-1)?.id||ui.selected; ui.isScene=false; ui.controls={}; refreshList(); renderControlPanel(); setStatus('Imported '+pack.assets.length+' assets from '+pack.pack_id+' (kept in this browser session).');
  }
  async function imageFromBlob(blob){
    const url=URL.createObjectURL(blob);
    return await new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>{URL.revokeObjectURL(url);reject(Error('Could not decode texture image'));};im.src=url;});
  }
  async function importZip(file){
    if(file.size>MAX_BYTES)throw Error('ZIP exceeds 120 MB import limit');
    // Read ZIP central directory first. CRC checking inflates every member, so
    // validate cumulative uncompressed bytes before allowing that work.
    const zip=await JSZip.loadAsync(file,{checkCRC32:false});
    const entries=Object.values(zip.files).filter(x=>!x.dir);
    if(entries.length>4000)throw Error('Too many ZIP entries');
    let expanded=0;
    for(const e of entries){
      if(!safePath(e.name))throw Error('Unsafe ZIP path: '+e.name);
      const bytes=e._data?.uncompressedSize;
      if(!Number.isSafeInteger(bytes)||bytes<0||bytes>MAX_ENTRY)throw Error('Invalid or oversized ZIP member: '+e.name);
      expanded+=bytes;
      if(expanded>MAX_BYTES)throw Error('ZIP exceeds 120 MB expanded-size limit');
    }
    // The ZIP has passed size checks. CRC validation is now safe to perform.
    await JSZip.loadAsync(file,{checkCRC32:true});
    const candidates=entries.filter(e=>/\.json$/i.test(e.name)).sort((a,b)=>a.name.length-b.name.length);
    const found=[];
    for(const e of candidates){if(found.length>=12)break;if(e._data?.uncompressedSize>MAX_ENTRY)continue;let p;try{p=JSON.parse(await e.async('string'))}catch{continue;}if(p.schema==='smi-visual-pack/1')found.push({pack:p,dirname:e.name.includes('/')?e.name.slice(0,e.name.lastIndexOf('/')):''});}
    if(!found.length)throw Error('No smi-visual-pack/1 manifest found in ZIP. Use the AI guide to create one.');
    for(const f of found){await importPack(f.pack,async path=>{const entry=zip.file(path);if(!entry) return null;if(entry._data?.uncompressedSize>MAX_ENTRY)throw Error('Oversize texture '+path);return entry.async('uint8array');},f.dirname);}
  }
  async function importFiles(files){
    const jsons=files.filter(f=>/\.json$/i.test(f.name));
    const imgs=files.filter(f=>/\.(png|jpg|jpeg|webp|gif)$/i.test(f.name));
    if(jsons.length){for(const f of jsons){const pack=JSON.parse(await f.text());await importPack(pack,async(_path,original)=>imgs.find(i=>i.name===original||i.webkitRelativePath===original)||null);}}
    else for(const f of imgs) {
      if(f.size>MAX_ENTRY)throw Error('Image exceeds 24 MB: '+f.name);
      const im=await imageFromBlob(f);
      if(im.naturalWidth>8192||im.naturalHeight>8192)throw Error('Image exceeds 8192×8192: '+f.name);
      const id='local.image.'+slug(f.name)+'-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,7);
      const tex='loose:'+id;textures.set(tex,{blob:f,image:im,path:f.name,source:'Local image',license:'UNSPECIFIED'});
      library.set(id,{id,kind:'region',name:f.name,texture:tex,rect_px:[0,0,im.naturalWidth,im.naturalHeight],source:'Local image',license:'UNSPECIFIED',tags:['uploaded','image']});
      imports.add(f.name);
    }
    refreshList();if(!jsons.length&&imgs.length)setStatus('Imported '+imgs.length+' local image(s). No data was uploaded.');
  }
  async function imageFor(key){
    const entry=textures.get(key);
    if(!entry)throw Error('Unknown texture '+key);
    if(entry.image)return entry.image;
    if(!entry.loading)entry.loading=new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>{entry.image=im;resolve(im);};im.onerror=()=>reject(Error('Cannot load texture '+entry.path));im.src=entry.src;});
    return entry.loading;
  }
  const sizeFor=(id,seen=new Set())=>{
    if(seen.has(id))return [96,96];seen.add(id);
    const a=library.get(id);if(!a)return [96,96];
    if(a.kind==='region')return a.logical_size_px||a.rect_px.slice(2,4);
    if(a.kind==='composition')return a.size_px;
    if(a.kind==='sequence')return sizeFor(a.frames[0].asset,seen);
    return sizeFor(a.states[a.default_state],seen);
  };
  function nineSlice(ctx,img,src,target,margins){
    const [sx,sy,sw,sh]=src,[dx,dy,dw,dh]=target,[l,t,r,b]=margins;
    if(dw<l+r||dh<t+b){ctx.drawImage(img,sx,sy,sw,sh,dx,dy,dw,dh);return;}
    const xs=[0,l,sw-r,sw],ys=[0,t,sh-b,sh],tx=[0,l,dw-r,dw],ty=[0,t,dh-b,dh];
    for(let row=0;row<3;row++)for(let col=0;col<3;col++){
      const ww=xs[col+1]-xs[col],hh=ys[row+1]-ys[row],tw=tx[col+1]-tx[col],th=ty[row+1]-ty[row];
      if(ww>0&&hh>0&&tw>0&&th>0)ctx.drawImage(img,sx+xs[col],sy+ys[row],ww,hh,dx+tx[col],dy+ty[row],tw,th);
    }
  }
  const defaultInputs=a=>Object.fromEntries(Object.entries(a.inputs||{}).map(([k,v])=>[k,v.default]));
  function frameAt(a,t){
    const durations=a.frames.map(f=>f.duration_ms||1000/a.default_fps),total=durations.reduce((x,y)=>x+y,0);
    let p=Math.max(0,t);
    if(a.playback==='loop')p%=total;
    else if(a.playback==='pingpong') { const t2=total*2;p%=t2;if(p>=total)p=t2-p-0.0001; }
    else p=Math.min(p,total-0.0001);
    for(let i=0;i<durations.length;i++){if(p<durations[i])return a.frames[i];p-=durations[i];}
    return a.frames.at(-1);
  }
  async function drawAsset(id,ctx,x,y,w,h,time,values={},stateOverride=null,stack=new Set()){
    if(stack.has(id))throw Error('Circular asset ref '+id);
    const a=library.get(id);if(!a)throw Error('Missing asset '+id);
    const next=new Set(stack);next.add(id);
    if(a.kind==='region'){
      const img=await imageFor(a.texture),r=a.rect_px;
      if(a.nine_slice_px)nineSlice(ctx,img,r,[x,y,w,h],a.nine_slice_px);
      else ctx.drawImage(img,...r,x,y,w,h);
      return;
    }
    if(a.kind==='sequence'){
      const f=frameAt(a,time),[fw,fh]=sizeFor(f.asset);
      await drawAsset(f.asset,ctx,x+(f.offset_px?.[0]||0),y+(f.offset_px?.[1]||0),w||fw,h||fh,time,values,null,next);return;
    }
    if(a.kind==='state_set'){
      const key=stateOverride&&a.states[stateOverride]?stateOverride:a.default_state;
      await drawAsset(a.states[key],ctx,x,y,w,h,time,values,null,next);return;
    }
    const inputs={...defaultInputs(a),...values};
    ctx.save();ctx.translate(x,y);ctx.scale(w/a.size_px[0],h/a.size_px[1]);
    for(const rawLayer of a.layers){
      const layer=Timeline.layerAt(rawLayer,time,a.duration_ms,a.playback||'loop');
      if(layer.visible_when&&inputs[layer.visible_when.input]!==layer.visible_when.equals)continue;
      const [lw,lh]=layer.size_px||sizeFor(layer.asset);
      let px=(layer.offset_px?.[0]||0)+(layer.x||0),py=(layer.offset_px?.[1]||0)+(layer.y||0);
      if(layer.position_from_input){const bind=layer.position_from_input;const v=range(inputs[bind.input],0,1),pos=bind.from_px+(bind.to_px-bind.from_px)*v;if(bind.axis==='x')px+=pos;else py+=pos;}
      ctx.save();ctx.globalAlpha*=layer.opacity??1;
      if(layer.rotation_deg||layer.scale_x!==undefined||layer.scale_y!==undefined){
        const midx=px+lw/2,midy=py+lh/2;
        ctx.translate(midx,midy);ctx.rotate((layer.rotation_deg||0)*Math.PI/180);
        ctx.scale(layer.scale_x??1,layer.scale_y??1);ctx.translate(-midx,-midy);
      }
      if(layer.blend)ctx.globalCompositeOperation=({normal:'source-over',multiply:'multiply',screen:'screen',add:'lighter'})[layer.blend]||'source-over';
      if(layer.clip){const fraction=range(inputs[layer.clip.input],0,1),horizontal=layer.clip.axis==='x';let cx=px,cy=py,cw=horizontal?lw*fraction:lw,ch=horizontal?lh:lh*fraction;if(layer.clip.origin==='end'){if(horizontal)cx+=lw-cw;else cy+=lh-ch;}ctx.beginPath();ctx.rect(cx,cy,cw,ch);ctx.clip();}
      await drawAsset(layer.asset,ctx,px,py,lw,lh,time,{...inputs,...(layer.input_values||{})},layer.state_from_input?inputs[layer.state_from_input]:(layer.state||null),next);
      ctx.restore();
    }
    ctx.restore();
  }
  function assetThumbnail(a){
    if(a.kind!=='region')return '';
    const t=textures.get(a.texture);return t?.image?.src||t?.src||'';
  }
  function refreshList(){
    const q=$('asset-search').value.toLowerCase().trim(),kind=$('asset-kind').value;
    const kinds=[...new Set([...library.values()].map(a=>a.kind))].sort();
    const select=$('asset-kind'),current=select.value;select.replaceChildren(new Option('All asset types',''));for(const k of kinds)select.add(new Option(k,k));select.value=current;
    const results=[...library.values()].filter(a=>(!kind||a.kind===kind)&&(!q||[a.name,a.id,a.kind,...(a.tags||[]),...(a.subjects||[])].join(' ').toLowerCase().includes(q))).slice(0,110);
    $('asset-count').textContent=results.length+' shown / '+library.size.toLocaleString();
    const list=$('asset-list');list.replaceChildren();
    for(const a of results){
      const btn=document.createElement('button');btn.type='button';btn.className='asset-entry';btn.setAttribute('aria-current',String(a.id===ui.selected));
      if(a.kind==='region'){const thumb=document.createElement('canvas');thumb.width=40;thumb.height=40;thumb.setAttribute('aria-hidden','true');thumb.style.cssText='flex:none;width:40px;height:40px;background:#243647;border-radius:5px';btn.append(thumb);imageFor(a.texture).then(im=>{const r=a.rect_px;const c=thumb.getContext('2d'),scale=Math.min(40/r[2],40/r[3]);c.clearRect(0,0,40,40);c.drawImage(im,...r,(40-r[2]*scale)/2,(40-r[3]*scale)/2,r[2]*scale,r[3]*scale);}).catch(()=>{});}
      const label=document.createElement('span');label.className='item-label';const strong=document.createElement('strong');strong.textContent=metaName(a);const small=document.createElement('small');small.textContent=a.kind+' · '+(a.source||'pack');label.append(strong,small);btn.append(label);
      btn.addEventListener('click',()=>{ui.selected=a.id;ui.isScene=false;ui.controls={};refreshList();renderControlPanel();});list.append(btn);
    }
  }
  function renderControlPanel(){
    const a=library.get(ui.selected),controls=$('input-controls');controls.replaceChildren();
    $('preview-name').textContent=ui.isScene?'Composition':a?metaName(a):'Select an asset';
    $('preview-details').textContent=a?'ID: '+a.id+' · '+a.kind+' · License: '+(a.license||'unspecified'): 'Select any asset in the list';
    if(!a||ui.isScene)return;
    if(a.kind==='state_set'){
      const label=document.createElement('label');label.textContent='State';const select=document.createElement('select');for(const key of Object.keys(a.states))select.add(new Option(key,key));select.onchange=()=>{ui.controls._state=select.value;};label.append(select);controls.append(label);
    }
    for(const [key,def] of Object.entries(a.inputs||{})){
      const label=document.createElement('label');label.textContent=key;let input;
      if(def.type==='boolean'){input=document.createElement('input');input.type='checkbox';input.checked=def.default;input.onchange=()=>ui.controls[key]=input.checked;}
      else if(def.type==='number'){input=document.createElement('input');input.type='range';input.min=def.min??0;input.max=def.max??1;input.step='0.01';input.value=def.default;input.oninput=()=>ui.controls[key]=Number(input.value);}
      else{input=document.createElement('select');for(const v of def.values||[])input.add(new Option(v,v));input.value=def.default;input.onchange=()=>ui.controls[key]=input.value;}
      label.append(input);controls.append(label);
    }
  }
  function layerInputs(){
    const container=$('layer-list');container.replaceChildren();
    if(!scene.layers.length){const msg=document.createElement('p');msg.className='helper';msg.textContent='No layers yet. Select an asset and click Add selected asset as layer.';container.append(msg);}
    scene.layers.forEach((l,i)=>{
      const el=document.createElement('div');el.className='layer-entry';if(i===scene.selectedLayer)el.classList.add('selected');
      const name=document.createElement('button');name.type='button';name.className='select-layer';name.textContent=(i+1)+'. '+metaName(library.get(l.asset)||{id:l.asset});
      name.title='Select this layer for timeline editing';name.onclick=()=>{scene.selectedLayer=i;ui.isScene=true;layerInputs();refreshTimeline();};el.append(name);
      const row=document.createElement('div');row.className='layer-row';
      const toggle=document.createElement('input');toggle.type='checkbox';toggle.checked=l.enabled;toggle.title='Visible';toggle.onchange=()=>{l.enabled=toggle.checked;ui.isScene=true};row.append(toggle);
      for(const key of ['x','y']){const input=document.createElement('input');input.type='number';input.value=l[key];input.title=key+' offset in pixels';input.onchange=()=>{l[key]=range(input.value,-4096,4096);ui.isScene=true};row.append(input);}
      const up=document.createElement('button');up.textContent='↑';up.title='Move up';up.onclick=()=>{if(i){[scene.layers[i-1],scene.layers[i]]=[l,scene.layers[i-1]];scene.selectedLayer=i-1;layerInputs();refreshTimeline();}};row.append(up);
      const down=document.createElement('button');down.textContent='↓';down.title='Move down';down.onclick=()=>{if(i<scene.layers.length-1){[scene.layers[i+1],scene.layers[i]]=[l,scene.layers[i+1]];scene.selectedLayer=i+1;layerInputs();refreshTimeline();}};row.append(down);
      const remove=document.createElement('button');remove.textContent='×';remove.title='Remove layer';remove.onclick=()=>{scene.layers.splice(i,1);scene.selectedLayer=Math.min(scene.selectedLayer,scene.layers.length-1);layerInputs();refreshTimeline()};row.append(remove);el.append(row);const sizing=document.createElement('div');sizing.className='layer-row';for(const key of ['w','h']){const label=document.createElement('label');label.textContent=key+' ';const input=document.createElement('input');input.type='number';input.min=1;input.max=4096;input.value=l[key];input.onchange=()=>{l[key]=range(input.value,1,4096);ui.isScene=true;};label.append(input);sizing.append(label);}const opacityLabel=document.createElement('label');opacityLabel.textContent='Opacity ';const opacity=document.createElement('input');opacity.type='range';opacity.min=0;opacity.max=1;opacity.step=.05;opacity.value=l.opacity;opacity.oninput=()=>{l.opacity=Number(opacity.value);ui.isScene=true;};opacityLabel.append(opacity);sizing.append(opacityLabel);el.append(sizing);const target=library.get(l.asset);if(target?.kind==='state_set'){const selector=document.createElement('select');for(const k of Object.keys(target.states))selector.add(new Option(k,k));selector.value=l.state||target.default_state;selector.onchange=()=>{l.state=selector.value;ui.isScene=true;};el.append(selector);}for(const [key,def] of Object.entries(target?.inputs||{})){const wrapper=document.createElement('label');wrapper.textContent=key+' ';let ctrl;if(def.type==='boolean'){ctrl=document.createElement('input');ctrl.type='checkbox';ctrl.checked=l.values[key]??def.default;ctrl.onchange=()=>{l.values[key]=ctrl.checked;ui.isScene=true;};}else if(def.type==='number'){ctrl=document.createElement('input');ctrl.type='range';ctrl.min=def.min??0;ctrl.max=def.max??1;ctrl.step='0.01';ctrl.value=l.values[key]??def.default;ctrl.oninput=()=>{l.values[key]=Number(ctrl.value);ui.isScene=true;};}else{ctrl=document.createElement('select');for(const v of def.values||[])ctrl.add(new Option(v,v));ctrl.value=l.values[key]??def.default;ctrl.onchange=()=>{l.values[key]=ctrl.value;ui.isScene=true;};}wrapper.append(ctrl);el.append(wrapper);}container.append(el);
    });
  }
  async function renderAt(canvas,time,fullSize=false){
    const ctx=canvas.getContext('2d'),cw=range($('canvas-width').value,16,4096),ch=range($('canvas-height').value,16,4096);
    // The stage is capped for responsive preview, while export retains authored sizes.
    const scale=fullSize?1:Math.min(1,500/cw,400/ch),w=Math.max(1,Math.round(cw*scale)),h=Math.max(1,Math.round(ch*scale));
    if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}ctx.clearRect(0,0,w,h);
    ctx.save();ctx.scale(scale,scale);
    try{
      if(ui.isScene&&scene.layers.length){for(const raw of scene.layers){if(!raw.enabled)continue;
        // Tracks describe additive X/Y displacement relative to the layer's base offset.
        // That matches composition manifests where offset_px and track motion are independent.
        const l=Timeline.layerAt({...raw,x:0,y:0},time,timeline.duration,timeline.playback),[ww,hh]=sizeFor(l.asset);
        const px=raw.x+(l.x||0),py=raw.y+(l.y||0);
        ctx.save();ctx.globalAlpha*=l.opacity??1;
        const lw=(l.w||ww)*(l.scale_x??1),lh=(l.h||hh)*(l.scale_y??1);
        if(l.rotation_deg){const cx=px+lw/2,cy=py+lh/2;ctx.translate(cx,cy);ctx.rotate(l.rotation_deg*Math.PI/180);ctx.translate(-cx,-cy);}
        await drawAsset(l.asset,ctx,px,py,lw,lh,time,l.values||{},l.state||null);ctx.restore();}}
      else if(ui.selected){const [aw,ah]=sizeFor(ui.selected),factor=Math.min(cw/aw,ch/ah,1);await drawAsset(ui.selected,ctx,Math.max(0,(cw-aw*factor)/2),Math.max(0,(ch-ah*factor)/2),aw*factor,ah*factor,time,ui.controls,ui.controls._state||null);}
    }catch(e){setStatus(e.message,true);}finally{ctx.restore();}
  }
  async function renderFrame(){await renderAt($('stage'),ui.clock,false);}
  let rendering=false;
  async function tick(now){
    if(ui.last&&ui.playing)ui.clock+=(now-ui.last)*ui.speed;
    ui.last=now;
    updatePlayhead();
    if(!rendering){rendering=true;try{await renderFrame()}finally{rendering=false;}}
    requestAnimationFrame(tick);
  }
  function download(blob,name){const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),30000);}
  function dependencies(id,closure=new Set()){
    if(closure.has(id))return closure;const a=library.get(id);if(!a)throw Error('Unresolved '+id);closure.add(id);
    const refs=a.kind==='sequence'?(a.frames||[]).map(x=>x.asset):a.kind==='composition'?(a.layers||[]).map(x=>x.asset):a.kind==='state_set'?Object.values(a.states):[];
    for(const r of refs)dependencies(r,closure);return closure;
  }
  async function exportPack(){
    const hasLayers=scene.layers.length>0,selected=ui.selected;
    if(!hasLayers&&!selected)throw Error('Select an asset or add layers before exporting');
    const selectedIds=hasLayers?scene.layers.filter(l=>l.enabled).map(l=>l.asset):[selected];
    if(!selectedIds.length)throw Error('All composition layers are hidden');
    const all=new Set();selectedIds.forEach(id=>dependencies(id,all));
    let rootId=selected;
    const assets=[...all].map(id=>structuredClone(library.get(id)));
    if(hasLayers){rootId='smi.user.'+slug($('composition-name').value)+'.composition';if(all.has(rootId))throw Error('Composition ID conflicts with existing asset ID');
      assets.push({id:rootId,name:$('composition-name').value||'My Visual Asset',kind:'composition',size_px:[range($('canvas-width').value,16,4096),range($('canvas-height').value,16,4096)],duration_ms:timeline.duration,playback:timeline.playback,layers:scene.layers.filter(l=>l.enabled).map((l,i)=>({id:'layer-'+i,asset:l.asset,offset_px:[l.x,l.y],size_px:[l.w,l.h],opacity:l.opacity,...(l.tracks?.length?{tracks:structuredClone(l.tracks)}:{}),...(Object.keys(l.values||{}).length?{input_values:l.values}:{}),...(l.state?{state:l.state}:{})}))});
    }
    const zip=new JSZip(),texMap={},textureIDs=new Set(assets.filter(a=>a.kind==='region').map(a=>a.texture));let index=0;
    for(const key of textureIDs){const t=textures.get(key);if(!t)throw Error('Missing texture '+key);let blob=t.blob;
      if(!blob){const result=await fetch(t.src);if(!result.ok)throw Error('Cannot fetch official texture '+t.src);blob=await result.blob();}
      if(blob.size>MAX_ENTRY)throw Error('Texture exceeds per-entry size limit: '+key);
      const img=await imageFor(key),filename='textures/'+String(index++).padStart(3,'0')+(t.path.match(/\.(png|jpe?g|webp|gif)$/i)?.[0].toLowerCase()||'.png');
      texMap[key]='t'+String(index);zip.file(filename,blob);texMap[key]={id:'t'+index,path:filename,width_px:img.naturalWidth,height_px:img.naturalHeight};
    }
    for(const a of assets){if(a.kind==='region')a.texture=texMap[a.texture].id;delete a.source;delete a.review_status;}
    const out={schema:'smi-visual-pack/1',pack_id:'smi.user.'+slug($('composition-name').value),version:'1.0.0',description:'Visual Atlas Builder export. Root asset: '+rootId,
      textures:Object.fromEntries(Object.values(texMap).map(t=>[t.id,{path:t.path,width_px:t.width_px,height_px:t.height_px}])),assets};
    zip.file('manifest.json',JSON.stringify(out,null,2)+'\n');
    zip.file('SOURCE-NOTICES.txt',`Generated locally with Superior MI Visual Atlas Builder.\nRoot asset: ${rootId}\n\nPer-asset licenses:\n`+assets.map(a=>a.id+' : '+(a.license||'UNSPECIFIED')).join('\n')+'\n\nOriginal asset and code licenses must be respected. Unknown license is not equivalent to CC0.\n');
    const usesOfficial=assets.some(a=>(a.license||'')==='Apache-2.0');
    if(usesOfficial){const response=await fetch('LICENSE');if(response.ok)zip.file('LICENSES/Apache-2.0.txt',await response.text());}
    const data=await zip.generateAsync({type:'blob',compression:'DEFLATE',compressionOptions:{level:5}});
    download(data,slug($('composition-name').value)+'.zip');setStatus('Exported '+assets.length+' assets and '+textureIDs.size+' textures. No files were uploaded.');
  }
  function updatePlayhead(){
    const time=Timeline.timelineTime(ui.clock,timeline.duration,timeline.playback);
    $('time-display').textContent=(time/1000).toFixed(2)+'s / '+(timeline.duration/1000).toFixed(2)+'s';
    $('playhead').max=timeline.duration;
    if(document.activeElement!==$('playhead'))$('playhead').value=Math.round(time);
  }
  function refreshTimeline(){
    updatePlayhead();const container=$('keyframe-lanes');container.replaceChildren();
    for(const [index,l] of scene.layers.entries())for(const track of l.tracks||[]){
      const lane=document.createElement('div');lane.className='keyframe-lane';
      const label=document.createElement('span');label.className='name';label.textContent=(index+1)+': '+track.property;
      const rail=document.createElement('div');rail.className='keyframe-track';
      for(const key of track.keyframes){const dot=document.createElement('span');dot.className='keyframe-dot';dot.style.left=(Math.min(100,key.time_ms/timeline.duration*100))+'%';dot.title=key.time_ms+'ms = '+key.value;rail.append(dot);}
      lane.append(label,rail);container.append(lane);
    }
    if(!container.childElementCount){const help=document.createElement('span');help.className='helper';help.textContent='No keyframes yet. Select a layer and set the first keyframe.';container.append(help);}
  }
  function editKeyframe(remove){
    const l=scene.layers[scene.selectedLayer];if(!l){setStatus('Select a composition layer before editing keyframes.',true);return;}
    const property=keyframeProp(),now=Math.round(Number($('playhead').value)/10)*10;
    const value=Number($('keyframe-value').value),easing=$('keyframe-easing').value;
    if(!Number.isFinite(value)){setStatus('Keyframe value must be a number.',true);return;}
    l.tracks=l.tracks||[];let track=l.tracks.find(t=>t.property===property);
    if(!track&&!remove){track={property,keyframes:[]};l.tracks.push(track);}
    if(!track){setStatus('No keyframe found on this track.',true);return;}
    const old=track.keyframes.map(x=>({...x}));
    if(remove){track.keyframes=track.keyframes.filter(k=>k.time_ms!==now);}else{
      const key={time_ms:now,value,easing};const index=track.keyframes.findIndex(k=>k.time_ms===now);
      if(index>=0)track.keyframes[index]=key;else track.keyframes.push(key);
      track.keyframes.sort((a,b)=>a.time_ms-b.time_ms);
    }
    if(!track.keyframes.length)l.tracks=l.tracks.filter(t=>t!==track);
    const errors=Timeline.validateTracks(l.tracks,timeline.duration,[],'scene layer');
    if(errors.length){track.keyframes=old;if(!old.length)l.tracks=l.tracks.filter(t=>t!==track);setStatus(errors[0],true);refreshTimeline();return;}
    ui.isScene=true;refreshTimeline();setStatus(remove?'Keyframe removed.':'Keyframe saved at '+now+' ms.');
  }
  async function canvasBlob(canvas){
    return new Promise((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(Error('PNG export failed')),'image/png'));
  }
  async function exportFrames(){
    if(!(scene.layers.length||ui.selected))throw Error('Select an asset or compose layers before exporting frames.');
    const width=Math.floor(range($('canvas-width').value,16,4096)),height=Math.floor(range($('canvas-height').value,16,4096));
    const frames=Math.ceil(timeline.duration/1000*timeline.exportFps);
    if(frames>LIMIT_FRAMES)throw Error('Maximum '+LIMIT_FRAMES+' frames per export. Shorten the timeline or reduce FPS.');
    if(frames*width*height>35000000)throw Error('Export exceeds 35 million output pixels. Reduce size, duration, or FPS.');
    const canvas=document.createElement('canvas'),zip=new JSZip();let total=0;
    const times=[];
    for(let i=0;i<frames;i++){
      const at=i*1000/timeline.exportFps;times.push(Math.round(at));
      await renderAt(canvas,at,true);
      const blob=await canvasBlob(canvas);
      total+=blob.size;if(total>MAX_BYTES)throw Error('PNG sequence exceeds 120 MB limit.');
      zip.file('frames/'+String(i).padStart(4,'0')+'.png',blob);
      if(i%6===0)setStatus('Rendering frame '+(i+1)+' / '+frames);
    }
    zip.file('frames.json',JSON.stringify({schema:'smi-rendered-frames/1',name:$('composition-name').value||'Visual Asset',fps:timeline.exportFps,duration_ms:timeline.duration,playback:timeline.playback,frame_count:frames,size_px:[width,height],times_ms:times,license_note:'See SOURCE-NOTICES.txt in portable manifest export for asset licensing details.'},null,2)+'\n');
    zip.file('README.txt','Rendered PNG frames generated locally by Superior MI Visual Atlas.\nCheck original asset licenses before redistribution.\n');
    const roots=scene.layers.length&&ui.isScene?scene.layers.filter(l=>l.enabled).map(l=>l.asset):[ui.selected].filter(Boolean);
    const used=new Set();roots.forEach(id=>dependencies(id,used));
    zip.file('SOURCE-NOTICES.txt','Original asset licenses still apply to flattened frames.\n'+[...used].map(id=>id+' : '+(library.get(id)?.license||'UNSPECIFIED')).join('\n')+'\n');
    const blob=await zip.generateAsync({type:'blob',compression:'DEFLATE',compressionOptions:{level:4}});
    download(blob,slug($('composition-name').value)+'-frames.zip');setStatus('Exported '+frames+' PNG frames at '+timeline.exportFps+' FPS.');
  }
  function wire(){
    $('upload').addEventListener('change',async e=>{try{const files=[...e.target.files];for(const f of files.filter(f=>/\.zip$/i.test(f.name)))await importZip(f);const others=files.filter(f=>!/\.zip$/i.test(f.name));if(others.length)await importFiles(others);$('import-info').textContent=imports.size+' local files/packs loaded';}catch(err){setStatus(err.message,true)}finally{e.target.value='';}});
    $('load-demo').addEventListener('click',async()=>{try{const response=await fetch('demo/starter-pack.zip');if(!response.ok)throw Error('Could not load demo pack');const blob=await response.blob();await importZip(blob);$('import-info').textContent=imports.size+' local files/packs loaded';}catch(e){setStatus(e.message,true)}});
    $('clear-imports').addEventListener('click',()=>{for(const [id,a] of library)if(a.source!=='Official Icon Atlas')library.delete(id);for(const [key,t] of textures)if(!key.startsWith('official:')){if(t.image?.src?.startsWith('blob:'))URL.revokeObjectURL(t.image.src);textures.delete(key);}imports.clear();$('import-info').textContent='Built-in Icon Atlas loaded automatically';scene.layers=[];scene.selectedLayer=-1;ui.selected=null;ui.isScene=false;layerInputs();refreshTimeline();renderControlPanel();refreshList();setStatus('Local imports cleared. Public icons remain.');});
    let searchDebounce;for(const id of ['asset-search','asset-kind'])$(id).addEventListener('input',()=>{clearTimeout(searchDebounce);searchDebounce=setTimeout(refreshList,80)});
    $('add-layer').addEventListener('click',()=>{if(!ui.selected){setStatus('Select an asset first.',true);return;}scene.layers.push({asset:ui.selected,x:0,y:0,enabled:true,values:{},tracks:[],w:Math.min(sizeFor(ui.selected)[0],2048),h:Math.min(sizeFor(ui.selected)[1],2048),opacity:1});scene.selectedLayer=scene.layers.length-1;ui.isScene=true;layerInputs();refreshTimeline();renderControlPanel();});
    $('play').addEventListener('click',()=>{ui.playing=!ui.playing;$('play').textContent=ui.playing?'Pause':'Play';});
    $('step').addEventListener('click',()=>{ui.clock+=1000/12;ui.playing=false;$('play').textContent='Play';});
    $('speed').addEventListener('change',()=>{ui.speed=Number($('speed').value)||1;});
    $('export').addEventListener('click',async()=>{try{await exportPack()}catch(e){setStatus(e.message,true)}});
    $('export-frames').addEventListener('click',async()=>{const button=$('export-frames');button.disabled=true;try{await exportFrames()}catch(e){setStatus(e.message,true)}finally{button.disabled=false}});
    $('duration-ms').addEventListener('change',()=>{timeline.duration=Math.floor(range($('duration-ms').value,100,600000));$('duration-ms').value=timeline.duration;ui.clock=Math.min(ui.clock,timeline.duration);refreshTimeline()});
    $('scene-playback').addEventListener('change',()=>{timeline.playback=$('scene-playback').value;refreshTimeline()});
    $('export-fps').addEventListener('change',()=>{timeline.exportFps=Math.floor(range($('export-fps').value,1,60));$('export-fps').value=timeline.exportFps});
    $('playhead').addEventListener('input',()=>{ui.clock=Number($('playhead').value);ui.playing=false;$('play').textContent='Play';updatePlayhead();});
    $('add-keyframe').addEventListener('click',()=>editKeyframe(false));
    $('remove-keyframe').addEventListener('click',()=>editKeyframe(true));
    $('export-png').addEventListener('click',()=>{const canvas=$('stage');canvas.toBlob(blob=>{if(blob)download(blob,slug($('composition-name').value)+'-preview.png');else setStatus('PNG export unavailable',true);},'image/png');});
    $('copy-prompt').addEventListener('click',async()=>{const prompt='Read '+AI_URL+' and create a Superior MI Visual Atlas smi-visual-pack/1 ZIP. Include manifest.json, local texture PNGs and assets. Validate exact coordinates and references. Do not include remote URLs or copyrighted material without rights. I will import the ZIP into the local-first builder.';try{await navigator.clipboard.writeText(prompt);setStatus('Copied AI creation instructions and guide link.')}catch{setStatus('Copy unavailable. Open the AI workflow guide and copy the instructions.',true)}});
  }
  addOfficialIcons();wire();refreshList();renderControlPanel();layerInputs();refreshTimeline();requestAnimationFrame(tick);
})();
