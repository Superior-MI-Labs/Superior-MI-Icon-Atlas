'use strict';
/* Canonical Canvas 2D renderer for both public previews and the local builder.
 * Resolve assets and textures through injected functions; the manifest owns behavior.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  root.VisualAtlasRenderer=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  function create({getAsset,getImage,slots,timeline,visualCore}){
    // Repeat a state-family using typed inputs; no special heart/pip renderer.
    function repeatLayout(layer,values,size){
      const r=layer.repeat;
      const bounded=(v,lo,hi)=>Math.max(lo,Math.min(hi,Math.floor(Number(v)||0)));
      const count=bounded(values[r.count_input],1,256);
      const columns=bounded(values[r.columns_input],1,count);
      const units=r.levels.length-1;
      const value=bounded(values[r.value_input],0,count*units);
      const [gx,gy]=r.gap_px||[0,0];
      const rows=Math.ceil(count/columns);
      return {count,columns,rows,value,units,stepX:size[0]+gx,stepY:size[1]+gy,
        width:columns*size[0]+(columns-1)*gx,
        height:rows*size[1]+(rows-1)*gy};
    }
    function geometryFor(id,seen=new Set(),values=null){
      if(seen.has(id))throw Error('Cyclic asset dimensions: '+id);
      const a=getAsset(id);if(!a)throw Error('Missing asset '+id);
      const next=new Set(seen);next.add(id);
      const frame=(width,height,minX=0,minY=0)=>({width,height,minX,minY});
      if(a.kind==='region'){
        const [width,height]=a.logical_size_px||a.rect_px.slice(2,4);
        return frame(width,height);
      }
      if(a.kind==='sequence')return geometryFor(a.frames[0].asset,next);
      if(a.kind==='state_set')return geometryFor(a.states[a.default_state],next);
      if(a.kind!=='composition')throw Error('Unknown kind '+a.kind);
      if(!a.layers.some(layer=>layer.repeat))return frame(...a.size_px);
      const inputs={...Object.fromEntries(Object.entries(a.inputs||{}).map(([key,input])=>[key,input.default])),...(values||{})};
      // A repeated composition is content-sized. Include every layer, not only
      // the first repeater: frames/overlays and negative offsets must not clip.
      let minX=0,minY=0,maxX=0,maxY=0;
      for(const layer of a.layers){
        const target=layer.asset||(layer.slot&&a.slots?.[layer.slot]?.default);
        if(!target)continue;
        const child=geometryFor(target,next,layer.input_values||null);
        const [lw,lh]=layer.size_px||[child.width,child.height];
        const size=layer.repeat?repeatLayout(layer,inputs,[lw,lh]):{width:lw,height:lh};
        const x=(layer.offset_px?.[0]||0)+(layer.x||0);
        const y=(layer.offset_px?.[1]||0)+(layer.y||0);
        minX=Math.min(minX,x);minY=Math.min(minY,y);
        maxX=Math.max(maxX,x+size.width);maxY=Math.max(maxY,y+size.height);
      }
      return frame(Math.max(1,maxX-minX),Math.max(1,maxY-minY),minX,minY);
    }
    function sizeFor(id,seen=new Set(),values=null){
      const {width,height}=geometryFor(id,seen,values);
      return [width,height];
    }
    // Keep legacy full-rectangle behavior unless a region explicitly declares a
    // trim offset. Many existing packs use logical_size_px for display scaling
    // without trimming; changing those assets would be a breaking change.
    function regionRect(a,x,y,w,h){
      if(!a.trim_offset_px)return [x,y,w,h];
      if(!a.logical_size_px)throw Error('Trimmed region requires logical_size_px: '+a.id);
      const [logicalW,logicalH]=a.logical_size_px,[cropW,cropH]=a.rect_px.slice(2);
      const [offsetX,offsetY]=a.trim_offset_px;
      if(logicalW<=0||logicalH<=0||offsetX<0||offsetY<0||offsetX+cropW>logicalW||offsetY+cropH>logicalH)
        throw Error('Trimmed region outside logical canvas: '+a.id);
      return [x+w*offsetX/logicalW,y+h*offsetY/logicalH,w*cropW/logicalW,h*cropH/logicalH];
    }
    // The regular drawAsset API places a logical top-left rectangle.
    // Explicit pivot drawing is opt-in so existing UI assets do not move.
    function pivotFor(id,time=0,stateOverride=null,seen=new Set()){
      if(seen.has(id))throw Error('Cyclic pivot reference: '+id);
      const a=getAsset(id);if(!a)throw Error('Missing asset '+id);
      if(a.pivot)return a.pivot;
      const next=new Set(seen);next.add(id);
      if(a.kind==='sequence')return pivotFor(frameAt(a,time).asset,time,null,next);
      if(a.kind==='state_set')return pivotFor(a.states[stateOverride&&a.states[stateOverride]?stateOverride:a.default_state],time,null,next);
      return null;
    }
    async function drawAssetAtPivot(id,ctx,anchorX,anchorY,w,h,time,values={},stateOverride=null,stack=new Set(),slotOverrides=null,presetName=null){
      const pivot=pivotFor(id,time,stateOverride);
      if(!pivot)throw Error('Missing authored pivot for '+id);
      return drawAsset(id,ctx,anchorX-w*pivot[0],anchorY-h*pivot[1],w,h,time,values,stateOverride,stack,slotOverrides,presetName);
    }
    function nineSlice(ctx,img,src,target,margins){
      const [sx,sy,sw,sh]=src,[dx,dy,dw,dh]=target,[l,t,r,b]=margins;
      if(dw<l+r||dh<t+b){ctx.drawImage(img,sx,sy,sw,sh,dx,dy,dw,dh);return;}
      const xs=[0,l,sw-r,sw],ys=[0,t,sh-b,sh],tx=[0,l,dw-r,dw],ty=[0,t,dh-b,dh];
      for(let row=0;row<3;row++)for(let col=0;col<3;col++){
        const ww=xs[col+1]-xs[col],hh=ys[row+1]-ys[row],tw=tx[col+1]-tx[col],th=ty[row+1]-ty[row];
        if(ww>0&&hh>0&&tw>0&&th>0)ctx.drawImage(img,sx+xs[col],sy+ys[row],ww,hh,dx+tx[col],dy+ty[row],tw,th);
      }
    }
    function frameAt(a,t){
      const durations=a.frames.map(f=>f.duration_ms||1000/a.default_fps),total=durations.reduce((x,y)=>x+y,0);
      if(!(total>0))throw Error('Invalid animation duration '+a.id);
      let p=Math.max(0,t);
      if(a.playback==='loop')p%=total;
      else if(a.playback==='pingpong'){const t2=total*2;p%=t2;if(p>=total)p=t2-p-0.0001;}
      else p=Math.min(p,total-0.0001);
      for(let i=0;i<durations.length;i++){if(p<durations[i])return a.frames[i];p-=durations[i];}
      return a.frames.at(-1);
    }
    async function drawAsset(id,ctx,x,y,w,h,time,values={},stateOverride=null,stack=new Set(),slotOverrides=null,presetName=null){
      if(stack.has(id))throw Error('Circular asset ref '+id);
      const a=getAsset(id);if(!a)throw Error('Missing asset '+id);
      const next=new Set(stack);next.add(id);
      if(a.kind==='region'){
        const img=await getImage(a.texture),r=a.rect_px;
        const dest=regionRect(a,x,y,w,h);
        if(a.nine_slice_px){
          if(a.trim_offset_px)throw Error('Trimmed nine-slice region is not supported: '+a.id);
          nineSlice(ctx,img,r,dest,a.nine_slice_px);
        }else ctx.drawImage(img,...r,...dest);
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
      if(a.kind!=='composition')throw Error('Unknown kind '+a.kind);
      const slotState=slots.resolve(a,presetName,slotOverrides||{});
      const inputs={...slotState.inputs,...values};
      const geometry=geometryFor(id,new Set(),inputs);
      ctx.save();ctx.translate(x,y);ctx.scale(w/geometry.width,h/geometry.height);
      ctx.translate(-geometry.minX,-geometry.minY);
      try{
        for(const rawLayer of a.layers){
          const layer=timeline.layerAt(rawLayer,time,a.duration_ms,a.playback||'loop');
          if(layer.visible_when&&inputs[layer.visible_when.input]!==layer.visible_when.equals)continue;
          const target=layer.slot?slotState.slots[layer.slot]:layer.asset;
          const [lw,lh]=layer.size_px||sizeFor(target);
          let px=(layer.offset_px?.[0]||0)+(layer.x||0),py=(layer.offset_px?.[1]||0)+(layer.y||0);
          if(layer.position_from_input){const bind=layer.position_from_input;const v=visualCore.unitValue(a,inputs,bind.input),pos=bind.from_px+(bind.to_px-bind.from_px)*v;if(bind.axis==='x')px+=pos;else py+=pos;}
          ctx.save();
          try{
            ctx.globalAlpha*=layer.opacity??1;
            if(layer.rotation_deg||layer.scale_x!==undefined||layer.scale_y!==undefined){
              const midx=px+lw/2,midy=py+lh/2;
              ctx.translate(midx,midy);ctx.rotate((layer.rotation_deg||0)*Math.PI/180);
              ctx.scale(layer.scale_x??1,layer.scale_y??1);ctx.translate(-midx,-midy);
            }
            if(layer.blend)ctx.globalCompositeOperation=({normal:'source-over',multiply:'multiply',screen:'screen',add:'lighter'})[layer.blend]||'source-over';
            if(layer.clip){const fraction=visualCore.unitValue(a,inputs,layer.clip.input),horizontal=layer.clip.axis==='x';let cx=px,cy=py,cw=horizontal?lw*fraction:lw,ch=horizontal?lh:lh*fraction;if(layer.clip.origin==='end'){if(horizontal)cx+=lw-cw;else cy+=lh-ch;}ctx.beginPath();ctx.rect(cx,cy,cw,ch);ctx.clip();}
            if(layer.repeat){
              const child=getAsset(target),r=layer.repeat;
              if(child?.kind!=='state_set')throw Error('Repeated layer must reference a state set: '+target);
              const plan=repeatLayout(layer,inputs,[lw,lh]);
              for(let i=0;i<plan.count;i++){
                const filled=Math.max(0,Math.min(plan.units,plan.value-i*plan.units));
                const state=r.levels[filled];
                await drawAsset(target,ctx,px+(i%plan.columns)*plan.stepX,
                  py+Math.floor(i/plan.columns)*plan.stepY,lw,lh,time,inputs,state,next);
              }
            }else await drawAsset(target,ctx,px,py,lw,lh,time,{...inputs,...(layer.input_values||{})},layer.state_from_input?inputs[layer.state_from_input]:(layer.state||null),next);
          }finally{ctx.restore();}
        }
      }finally{ctx.restore();}
    }
    return Object.freeze({sizeFor,geometryFor,frameAt,drawAsset,drawAssetAtPivot,pivotFor,regionRect,repeatLayout});
  }
  return Object.freeze({create});
});