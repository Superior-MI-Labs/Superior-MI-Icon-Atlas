'use strict';
/* One local clip registry feeds the individual preview and ordered sequence audition.
 * This is video-source QA, not another Visual Atlas rendering or asset-schema engine. */
(()=>{
  const $=id=>document.getElementById(id);
  const video=$('motion-video'),clips=new Map();
  const queue=[];
  let mode='none',current=null,queueAt=0,paused=false;
  const notice=text=>{$('motion-message').textContent=text;};
  const clock=s=>Number.isFinite(s)?`${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}`:'0:00';
  function sourceFor(clip){return $('motion-format').value==='mp4'?clip.mp4:clip.webm;}
  function startClip(id,play=true){
    const clip=clips.get(id);
    if(!clip)return;
    current=id;
    $('motion-name').textContent=clip.title;
    video.pause(); video.removeAttribute('src'); video.load();
    video.src=sourceFor(clip); video.load();
    $('motion-placeholder').hidden=true;
    $('motion-progress').textContent=`0:00 / ${clock(clip.duration_ms/1000)}`;
    renderQueue();
    if(play){const promise=video.play();if(promise)promise.catch(e=>notice(`Playback unavailable: ${e.message}. Try Original MP4.`));}
    notice(`Viewing ${clip.title} · ${$('motion-format').value==='webm'?'experimental transparent matte':'original source video'}`);
  }
  function playOne(id){mode='single';paused=false;startClip(id);}
  function stepQueue(){
    if(!queue.length){mode='none';return;}
    queueAt++;
    if(queueAt>=queue.length){
      if($('motion-loop-queue').checked)queueAt=0;
      else {mode='none';notice('Sequence completed.');renderQueue();return;}
    }
    startClip(queue[queueAt]);
  }
  function playQueue(){
    if(!queue.length){notice('Add at least one animation to the sequence.');return;}
    mode='queue';queueAt=0;paused=false;startClip(queue[queueAt]);
  }
  function renderQueue(){
    const el=$('motion-queue');el.replaceChildren();
    if(!queue.length){let li=document.createElement('li');li.className='motion-empty';li.textContent='Queue is empty. Add animations below.';el.append(li);return;}
    for(let i=0;i<queue.length;i++){
      let li=document.createElement('li');if(mode==='queue'&&queueAt===i)li.classList.add('active');
      let span=document.createElement('span');span.textContent=`${i+1}. ${clips.get(queue[i])?.title||queue[i]}`;li.append(span);
      for(const [label,disabled,doit] of [
        ['↑',i===0,()=>move(i,-1)],['↓',i===queue.length-1,()=>move(i,1)],['×',false,()=>{queue.splice(i,1);mode='none';renderQueue();}]
      ]){let btn=document.createElement('button');btn.type='button';btn.textContent=label;btn.disabled=disabled;btn.setAttribute('aria-label',`${label==='×'?'Remove':label==='↑'?'Move up':'Move down'} ${span.textContent}`);btn.addEventListener('click',doit);li.append(btn);}
      el.append(li);
    }
  }
  function move(i,d){[queue[i],queue[i+d]]=[queue[i+d],queue[i]];mode='none';renderQueue();}
  function add(id){queue.push(id);renderQueue();notice(`Added ${clips.get(id).title} to sequence.`);}
  function renderClips(){
    const root=$('motion-clips');root.replaceChildren();
    for(const clip of clips.values()){
      const card=document.createElement('article');card.className='motion-card';
      const img=document.createElement('img');img.src=clip.poster;img.alt=`${clip.title} starting pose`;img.loading='lazy';card.append(img);
      const h=document.createElement('h4');h.textContent=clip.title;card.append(h);
      const desc=document.createElement('p');desc.textContent=`${clip.frames} frames · ${(clip.duration_ms/1000).toFixed(1)}s · ${clip.fps} FPS · Review pending`;card.append(desc);
      const actions=document.createElement('div');actions.className='actions';
      const play=document.createElement('button');play.textContent='Play clip';play.addEventListener('click',()=>playOne(clip.id));
      const addBtn=document.createElement('button');addBtn.textContent='Add to sequence';addBtn.addEventListener('click',()=>add(clip.id));
      const original=document.createElement('a');original.href=clip.mp4;original.textContent='Source MP4';original.download=clip.id+'.mp4';
      actions.append(play,addBtn,original);card.append(actions);root.append(card);
    }
    $('motion-count').textContent=`${clips.size} clips`;
  }
  $('motion-play').addEventListener('click',()=>{if(current){const p=video.play();p?.catch(e=>notice(e.message));}else playOne(clips.keys().next().value);});
  $('motion-pause').addEventListener('click',()=>{video.pause();paused=true;});
  $('motion-stop').addEventListener('click',()=>{mode='none';video.pause();video.currentTime=0;notice('Playback stopped.');renderQueue();});
  $('motion-next').addEventListener('click',()=>mode==='queue'?stepQueue():notice('Next applies while a sequence is playing.'));
  $('motion-play-queue').addEventListener('click',playQueue);
  $('motion-clear-queue').addEventListener('click',()=>{queue.length=0;mode='none';renderQueue();});
  $('motion-format').addEventListener('change',()=>{if(current){const active=mode;startClip(current,false);mode=active;notice('Preview format switched. Press Play.');}});
  $('motion-background').addEventListener('change',()=>{const stage=$('motion-stage');stage.classList.remove('light','dark');if($('motion-background').value!=='checker')stage.classList.add($('motion-background').value);});
  $('motion-export-queue').addEventListener('click',()=>{
    const output={schema:'smi-sky-motion-playlist/1',kind:'video-preview-sequence',repeat:$('motion-loop-queue').checked,
      order:queue.map(id=>({clip_id:id,duration_ms:clips.get(id)?.duration_ms||0}))};
    const a=document.createElement('a'),href=URL.createObjectURL(new Blob([JSON.stringify(output,null,2)+'\n'],{type:'application/json'}));
    a.href=href;a.download='sky-motion-preview-sequence.json';a.click();setTimeout(()=>URL.revokeObjectURL(href),1000);
  });
  video.addEventListener('ended',()=>{
    if(mode==='queue')stepQueue();else if(mode==='single'&&$('motion-loop-single').checked){video.currentTime=0;video.play().catch(e=>notice(e.message));}
    else notice('Clip completed.');
  });
  video.addEventListener('timeupdate',()=>{$('motion-progress').textContent=`${clock(video.currentTime)} / ${clock(video.duration)}`;});
  video.addEventListener('error',()=>{if(current)notice('This video could not play. Switch to Original MP4 or check media files.');});
  fetch('sky-motion-lab/clips.json').then(r=>{if(!r.ok)throw Error('Clip manifest unavailable');return r.json();}).then(data=>{
    if(data.schema!=='smi-video-showcase/1'||!Array.isArray(data.clips))throw Error('Unsupported clip manifest');
    for(const c of data.clips){if(!/^[a-z0-9_]+$/.test(c.id))throw Error('Invalid clip ID');clips.set(c.id,c);}
    if(!clips.size)throw Error('No animation clips');renderClips();renderQueue();
  }).catch(e=>notice('Motion showcase could not load: '+e.message));
})();
