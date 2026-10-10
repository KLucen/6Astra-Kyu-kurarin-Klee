"""Repair mouth and body-cut intervals while retaining baseline packets outside their GOPs."""
import av,cv2,json,subprocess,time
import numpy as np
from pathlib import Path
from fractions import Fraction
import composite_core as C

R=C.R
M=C.M
TB=Fraction(1,16000)
TICKS=M['pts_ticks']
DUR=[b-a for a,b in zip(TICKS,TICKS[1:])]+[M['last_exposure_ticks']]
DURATION=dict(zip(TICKS,DUR))

def stream(container,width=1920,preset='fast',crf='18'):
    s=container.add_stream('libx264',rate=Fraction(88,3));s.width=width;s.height=1080;s.pix_fmt='yuv420p';s.time_base=TB;s.codec_context.time_base=TB
    for k,v in {'colorspace':1,'color_range':1,'color_primaries':1,'color_trc':1,'sample_aspect_ratio':Fraction(1,1)}.items():setattr(s.codec_context,k,v)
    s.options={'crf':crf,'preset':preset,'bf':'0','threads':'4'}
    return s

def rgbframe(a,i):
    f=av.VideoFrame.from_ndarray(a,format='rgb24').reformat(format='yuv420p',dst_colorspace='ITU709',src_color_range='JPEG',dst_color_range='MPEG',dst_color_trc=1,dst_color_primaries=1,threads=1)
    f.pts=TICKS[i];f.time_base=TB;f.duration=DUR[i];f.colorspace=1;f.color_range=1
    return f

def encode(co,s,f):
    for p in s.encode(f):
        if p.pts in DURATION:p.duration=DURATION[p.pts]
        co.mux(p)

def mux(silent,final):
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(silent),'-i',M['source'],'-map','0:v:0','-map','1:a:0','-c','copy','-t',f'{M["video_end_pts_ticks"]/16000:.9f}','-map_metadata','-1','-movflags','+faststart',str(final)],check=True)

def main():
    cv2.setNumThreads(1);C.init_tracks();t0=time.monotonic()
    baseline=R/'output/Klee_Kyu-kurarin_DRAFT_v1-silent.mp4'
    targets=[(1145,1148),(1408,1664),(2912,3424),(3488,3544)]
    # Repairs are re-encoded with GOP-aligned context; all other packet payloads are retained.
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_packets','-show_entries','packet=pts,flags','-of','json',str(baseline)]))['packets']
    tick_to_i={t:i for i,t in enumerate(TICKS)}
    keys=[tick_to_i[int(p['pts'])] for p in probe if 'K' in p['flags']]+[M['frames']]
    intervals=[]
    for a,b in targets:
        aa=max(k for k in keys if k<=a);bb=min(k for k in keys if k>=b)
        if intervals and aa<=intervals[-1][1]:intervals[-1][1]=max(bb,intervals[-1][1])
        else:intervals.append([aa,bb])
    repaired={}
    cap=cv2.VideoCapture(M['source']);raw=av.open(str(baseline));decoded=raw.decode(video=0)
    for i in range(M['frames']):
        ok,bgr=cap.read();base=next(decoded)
        if not ok:raise RuntimeError(i)
        part=next((j for j,(a,b) in enumerate(intervals) if a<=i<b),None)
        if part is None:continue
        a,b=intervals[part]
        if i==a:
            temp=R/f'output/mouth-repair-gop-{part}.mp4';co=av.open(str(temp),'w',options={'video_track_timescale':'16000'});s=stream(co);repaired[part]=temp
        if any(a<=i<b for a,b in targets):
            rgb=C.render(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB),i)
            if i%8==0:cv2.imwrite(str(R/'output/full-render-review'/f'f{i:05d}.jpg'),cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,94])
            f=rgbframe(rgb,i)
        else:
            f=base;f.pts=TICKS[i];f.time_base=TB;f.duration=DUR[i]
        encode(co,s,f)
        if i%120==0:print('REPAIR',i,'seconds',round(time.monotonic()-t0,1),flush=True)
        if i==b-1:encode(co,s,None);co.close()
    cap.release();raw.close()
    # All streams have matching encoder configuration. Packet payloads outside repair GOPs are retained.
    out=R/'output/Klee_Kyu-kurarin_DRAFT_v2-silent.mp4';source=av.open(str(baseline));co=av.open(str(out),'w',options={'video_track_timescale':'16000'});s=co.add_stream_from_template(source.streams.video[0])
    patched_packets={}
    holders=[]
    for j,pth in repaired.items():
        holder=av.open(str(pth));holders.append(holder)
        if holder.streams.video[0].codec_context.extradata!=source.streams.video[0].codec_context.extradata:
            raise RuntimeError('Repair SPS/PPS differs from baseline; packet splicing is unsafe.')
        ps=[p for p in holder.demux(video=0) if p.pts is not None]
        # MP4 may normalize the nonzero initial PTS. Restore using the recorded first source tick.
        shift=TICKS[intervals[j][0]]-int(ps[0].pts*ps[0].time_base/TB)
        for p in ps:
            pts=int(p.pts*p.time_base/TB)+shift;dts=int(p.dts*p.time_base/TB)+shift
            p.pts=pts;p.dts=dts;p.duration=DURATION[pts];p.time_base=TB;patched_packets[pts]=p
    expected={TICKS[i] for a,b in intervals for i in range(a,b)}
    if set(patched_packets)!=expected:raise RuntimeError('Repair packet PTS do not match the source exposure intervals.')
    for p in source.demux(video=0):
        if p.pts is None:continue
        tick=int(p.pts*p.time_base/TB)
        chosen=patched_packets.get(tick,p);chosen.stream=s;co.mux(chosen)
    co.close();source.close()
    for h in holders:h.close()
    final=R/'output/Klee_Kyu-kurarin_DRAFT_v2.mp4';mux(out,final)
    report={'baseline':str(baseline),'output':str(final),'patched_intervals':targets,'reencoded_gop_intervals':intervals,'unchanged_video_packet_payloads_outside_repair_gops':True,'elapsed_seconds':round(time.monotonic()-t0,1),'artistic_review':'static_only_pending_original_speed'}
    (R/'analysis/mouth-repair-v2.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)

if __name__=='__main__':main()
