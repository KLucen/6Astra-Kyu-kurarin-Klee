"""Splice the omitted open-eye Alice hug; preserve all other v3 video/audio packets."""
import av,cv2,json,time,hashlib
from fractions import Fraction
from finish_v2 import R,M,TICKS,TB,DURATION,stream,rgbframe,encode,mux
from hug_alice_v4 import initialize

def main():
    C=initialize();t0=time.monotonic();start,end=5784,6039
    baseline=R/'output/Klee_Kyu-kurarin_ALICE_v3-silent.mp4';repair=R/'output/alice-open-hug-v4-repair.mp4'
    b=av.open(str(baseline));keys={p.pts for p in b.demux(video=0) if p.pts is not None and p.is_keyframe};b.close()
    if TICKS[end] not in keys:raise RuntimeError('The unchanged resume point must be a baseline IDR frame.')
    co=av.open(str(repair),'w',options={'video_track_timescale':'16000'});s=stream(co)
    cap=cv2.VideoCapture(M['source'])
    for i in range(end):
        ok,bgr=cap.read()
        if not ok:raise RuntimeError(i)
        if i<start:continue
        dst=C.render(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB),i);encode(co,s,rgbframe(dst,i))
        if i%64==0:print('ALICE',i,'/',end,'seconds',round(time.monotonic()-t0,1),flush=True)
    encode(co,s,None);co.close();cap.release()
    baseline_in=av.open(str(baseline));repair_in=av.open(str(repair))
    if baseline_in.streams.video[0].codec_context.extradata!=repair_in.streams.video[0].codec_context.extradata:raise RuntimeError('SPS/PPS mismatch')
    ps=[p for p in repair_in.demux(video=0) if p.pts is not None]
    if not ps or not ps[0].is_keyframe:raise RuntimeError('New repair must begin with an IDR frame.')
    shift=TICKS[start]-int(ps[0].pts*ps[0].time_base/TB);replacements={}
    for p in ps:
        pts=int(p.pts*p.time_base/TB)+shift;dts=int(p.dts*p.time_base/TB)+shift;p.pts=pts;p.dts=dts;p.time_base=TB;p.duration=DURATION[pts];replacements[pts]=p
    if set(replacements)!=set(TICKS[start:end]):raise RuntimeError('Alice PTS mismatch')
    silent=R/'output/Klee_Kyu-kurarin_ALICE_v4-silent.mp4';co=av.open(str(silent),'w',options={'video_track_timescale':'16000'});s=co.add_stream_from_template(baseline_in.streams.video[0]);copied=0
    for p in baseline_in.demux(video=0):
        if p.pts is None:continue
        tick=int(p.pts*p.time_base/TB);chosen=replacements.get(tick,p);copied+=int(tick not in replacements);chosen.stream=s;co.mux(chosen)
    co.close();baseline_in.close();repair_in.close()
    final=R/'output/Klee_Kyu-kurarin_ALICE_v4.mp4';mux(silent,final)
    # Independently compare encoded payloads outside the user-requested interval.
    def packets(pth):
        c=av.open(str(pth));out={int(p.pts*p.time_base/TB):hashlib.sha256(bytes(p)).hexdigest() for p in c.demux(video=0) if p.pts is not None};c.close();return out
    old=packets(baseline);new=packets(final);outside=[t for t in TICKS if t not in replacements];same=all(old[t]==new[t] for t in outside)
    report={'baseline':str(baseline),'output':str(final),'changed_frames':[start,end],'changed_seconds':[TICKS[start]/16000,TICKS[end]/16000],'alice_cel':'generated/hug-open-alice-f05784-v1.png','registration':'analysis/alice-open-cel-registration.json','outside_interval_video_packets':len(outside),'outside_interval_video_payloads_unchanged':same,'elapsed_seconds':round(time.monotonic()-t0,1),'artistic_acceptance':'static_review_only'}
    (R/'analysis/alice-v4-change-scope.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
    if not same:raise RuntimeError('An out-of-scope video packet changed')

if __name__=='__main__':main()
