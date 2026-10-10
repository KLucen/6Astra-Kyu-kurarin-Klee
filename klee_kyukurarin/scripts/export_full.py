"""Ordered parallel composition, exact source PTS, explicit BT.709 and copied AAC."""
import av, cv2, json, subprocess, time
import numpy as np
from fractions import Fraction
from pathlib import Path
from collections import deque
from concurrent.futures import ProcessPoolExecutor

R=Path(__file__).resolve().parents[1]

def initialize_worker():
    global C
    cv2.setNumThreads(1)
    import composite_core as C
    C.init_tracks()

def compose_one(task):
    i,bgr=task
    src=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
    C.ISSUES.clear()
    dst=C.render(src,i)
    delta=cv2.absdiff(dst,src)
    changed=int(np.count_nonzero(np.max(delta,axis=2)>15))
    row={'frame':i,'family':C.SC[i]['family'],'present':C.SC[i].get('present'),'changed_pixels':changed}
    return i,dst,row,list(C.ISSUES)

def main():
    cv2.setNumThreads(1)
    M=json.loads((R/'analysis/source_meta.json').read_text())
    tb=Fraction(1,16000);ticks=M['pts_ticks']
    durations=[ticks[i+1]-ticks[i] for i in range(len(ticks)-1)]+[M['last_exposure_ticks']]
    lookup=dict(zip(ticks,durations));out=R/'output/Klee_Kyu-kurarin_DRAFT_v1-silent.mp4'
    co=av.open(str(out),'w',options={'video_track_timescale':'16000'})
    s=co.add_stream('libx264',rate=Fraction(88,3));s.width=1920;s.height=1080;s.pix_fmt='yuv420p'
    s.time_base=tb;s.codec_context.time_base=tb
    s.codec_context.colorspace=1;s.codec_context.color_range=1
    s.codec_context.color_primaries=1;s.codec_context.color_trc=1
    s.codec_context.sample_aspect_ratio=Fraction(1,1)
    s.options={'crf':'18','preset':'fast','bf':'0','threads':'3'}
    cap=cv2.VideoCapture(M['source']);t0=time.monotonic();coverage=[];issues=[]
    review=R/'output/full-render-review';review.mkdir(exist_ok=True)
    pending=deque();next_i=0
    with ProcessPoolExecutor(max_workers=4,initializer=initialize_worker) as pool:
        while next_i<M['frames'] or pending:
            while next_i<M['frames'] and len(pending)<8:
                ok,bgr=cap.read()
                if not ok:raise RuntimeError(next_i)
                pending.append(pool.submit(compose_one,(next_i,bgr)));next_i+=1
            i,dst,row,found=pending.popleft().result();coverage.append(row);issues.extend(found)
            if i%48==0 or i in [120,130,138,178,1464,1496,1536,3555,3748,4544,4760,5304,5556,5573,5784,5900,6039,6272]:
                cv2.imwrite(str(review/f'f{i:05d}.jpg'),cv2.cvtColor(dst,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,92])
            rgb=av.VideoFrame.from_ndarray(dst,format='rgb24')
            frame=rgb.reformat(format='yuv420p',dst_colorspace='ITU709',src_color_range='JPEG',dst_color_range='MPEG',dst_color_trc=1,dst_color_primaries=1,threads=1)
            frame.pts=ticks[i];frame.time_base=tb;frame.duration=durations[i]
            frame.colorspace=1;frame.color_range=1
            for p in s.encode(frame):
                if p.pts in lookup:p.duration=lookup[p.pts]
                co.mux(p)
            if i%120==0:
                state={'frame':i,'total_frames':M['frames'],'elapsed_seconds':round(time.monotonic()-t0,1),'state':'encoding_silent_video_bt709','workers':4}
                (R/'analysis/export-progress.json').write_text(json.dumps(state));print(json.dumps(state),flush=True)
    cap.release()
    for p in s.encode():
        if p.pts in lookup:p.duration=lookup[p.pts]
        co.mux(p)
    co.close();final=R/'output/Klee_Kyu-kurarin_DRAFT_v1.mp4'
    boundary=Fraction(M['video_end_pts_ticks'],16000)
    # Keep the complete final AAC packet crossing the video boundary; omit later packets.
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(out),'-i',M['source'],'-map','0:v:0','-map','1:a:0','-c','copy','-t',f'{float(boundary):.9f}','-map_metadata','-1','-movflags','+faststart',str(final)],check=True)
    (R/'analysis/full-render-coverage.json').write_text(json.dumps(coverage,indent=2))
    (R/'analysis/full-render-issues.json').write_text(json.dumps(issues,indent=2))
    (R/'analysis/export-progress.json').write_text(json.dumps({'state':'encoded_pending_verification','frames':M['frames'],'output':str(final),'elapsed_seconds':round(time.monotonic()-t0,1),'issues':len(issues)},indent=2))
    print('EXPORTED',final,'issues',len(issues),flush=True)

if __name__=='__main__':
    main()
