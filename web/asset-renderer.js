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
    function sizeFor(id,seen=new Set()){
      if(seen.has(id))throw Error('Cyclic asset dimensions: '+id);
      const a=getAsset(id);if(!a)throw Error('Missing asset '+id);
      seen.add(id);
      if(a.kind==='region')return a.logical_size_px||a.rect_px.slice(2,4);
      if(a.kind==='composition')return a.size_px;
      if(a.kind==='sequence')return sizeFor(a.frames[0].asset,seen);
      if(a.kind==='state_set')return sizeFor(a.states[a.default_state],seen);
      throw Error('Unknown kind '+a.kind);
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
      if(a.kind!=='composition')throw Error('Unknown kind '+a.kind);
      const slotState=slots.resolve(a,presetName,slotOverrides||{});
      const inputs={...slotState.inputs,...values};
      ctx.save();ctx.translate(x,y);ctx.scale(w/a.size_px[0],h/a.size_px[1]);
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
            await drawAsset(target,ctx,px,py,lw,lh,time,{...inputs,...(layer.input_values||{})},layer.state_from_input?inputs[layer.state_from_input]:(layer.state||null),next);
          }finally{ctx.restore();}
        }
      }finally{ctx.restore();}
    }
    return Object.freeze({sizeFor,frameAt,drawAsset});
  }
  return Object.freeze({create});
});