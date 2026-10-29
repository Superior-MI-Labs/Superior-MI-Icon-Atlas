"use strict";
/* Pure, deterministic timeline primitives shared by browser, preview, and Node tests. */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.VisualAtlasTimeline=api;
})(typeof window==='undefined'?null:window,function(){
  const PROPERTIES=new Set(['x','y','opacity','scale_x','scale_y','rotation_deg']);
  const finite=Number.isFinite;
  function timelineTime(time,duration,playback='loop'){
    if(!finite(time))throw Error('Timeline time must be finite');
    if(!finite(duration)||duration<=0)throw Error('Timeline duration must be positive');
    if(playback==='once')return Math.max(0,Math.min(time,duration));
    if(playback==='loop')return ((time%duration)+duration)%duration;
    if(playback==='pingpong'){
      const period=duration*2,t=((time%period)+period)%period;
      return t<=duration?t:period-t;
    }
    throw Error('Unknown playback mode '+playback);
  }
  function ease(t,mode){
    if(mode==='step')return 0;
    if(mode==='smooth')return t*t*(3-2*t);
    if(mode==='linear'||mode===undefined)return t;
    throw Error('Unsupported easing: '+mode);
  }
  function valueAt(track,time,defaultValue=0){
    const keys=track?.keyframes;
    if(!keys?.length)return defaultValue;
    if(time<=keys[0].time_ms)return keys[0].value;
    for(let i=0;i<keys.length-1;i++){
      const a=keys[i],b=keys[i+1];
      if(time<=b.time_ms){
        if(time===b.time_ms)return b.value;
        const progress=(time-a.time_ms)/(b.time_ms-a.time_ms);
        return a.value+(b.value-a.value)*ease(progress,a.easing);
      }
    }
    return keys[keys.length-1].value;
  }
  function layerAt(layer,time,duration=undefined,playback='loop'){
    const t=duration?timelineTime(time,duration,playback):time;
    const output={...layer};
    for(const track of layer.tracks||[])output[track.property]=valueAt(track,t,output[track.property]??(track.property.startsWith('scale_')?1:track.property==='opacity'?1:0));
    return output;
  }
  function validateTracks(tracks,duration,errors,label){
    if(tracks===undefined)return errors;
    if(!Array.isArray(tracks)||tracks.length>6){errors.push(label+': tracks must be a list of <=6 properties');return errors;}
    const unique=new Set();
    for(const t of tracks){
      if(!t||!PROPERTIES.has(t.property)){errors.push(label+': unsupported track');continue;}
      if(unique.has(t.property))errors.push(label+': repeated track '+t.property);
      unique.add(t.property);
      if(!Array.isArray(t.keyframes)||!t.keyframes.length||t.keyframes.length>240){errors.push(label+': keyframes must be 1..240');continue;}
      let previous=-1;
      for(const k of t.keyframes){
        if(!k||!finite(k.time_ms)||!finite(k.value)||k.time_ms<0||k.time_ms<=previous||duration&&k.time_ms>duration){errors.push(label+': keyframe time/value out of order or range');break;}
        if(k.easing&&!['linear','step','smooth'].includes(k.easing))errors.push(label+': unsupported easing');
        if(t.property==='opacity'&&(k.value<0||k.value>1))errors.push(label+': opacity outside 0..1');
        if(t.property.startsWith('scale_')&&(k.value<0||k.value>20))errors.push(label+': scale outside 0..20');
        previous=k.time_ms;
      }
    }
    return errors;
  }
  return {PROPERTIES:[...PROPERTIES],timelineTime,ease,valueAt,layerAt,validateTracks};
});
