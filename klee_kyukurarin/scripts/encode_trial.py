import av,json,subprocess
from fractions import Fraction
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1];M=json.loads((R/'analysis/source_meta.json').read_text());ticks=M['pts_ticks'];start=128;end=192;tb=Fraction(1,16000)
out=R/'output/body-loop-trial-silent.mp4';co=av.open(str(out),'w',options={'video_track_timescale':'16000'});s=co.add_stream('libx264',rate=Fraction(88,3));s.width=1920;s.height=1080;s.pix_fmt='yuv420p';s.time_base=tb;s.codec_context.time_base=tb;s.options={'crf':'18','preset':'fast','bf':'0'}
for i in range(start,end):
    a=np.array(Image.open(R/'output/body-loop-trial-frames'/f'f{i:05d}.png'));f=av.VideoFrame.from_ndarray(a,format='rgb24');f.pts=ticks[i]-ticks[start];f.time_base=tb;f.duration=ticks[i+1]-ticks[i]
    for p in s.encode(f):
        ix=next((j for j in range(start,end) if ticks[j]-ticks[start]==p.pts),None)
        if ix is not None:p.duration=ticks[ix+1]-ticks[ix]
        co.mux(p)
for p in s.encode():
    ix=next((j for j in range(start,end) if ticks[j]-ticks[start]==p.pts),None)
    if ix is not None:p.duration=ticks[ix+1]-ticks[ix]
    co.mux(p)
co.close()
dur=(ticks[end]-ticks[start])/16000
cmd=['ffmpeg','-y','-v','error','-i',str(out),'-ss',str(ticks[start]/16000),'-i',M['source'],'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-t',str(dur),'-movflags','+faststart',str(R/'output/body-loop-TRIAL.mp4')]
subprocess.run(cmd,check=True)
cmd=['ffmpeg','-y','-v','error','-ss',str(ticks[start]/16000),'-i',M['source'],'-i',str(R/'output/body-loop-TRIAL.mp4'),'-filter_complex','[0:v]scale=960:540,setpts=PTS-STARTPTS[a];[1:v]scale=960:540,setpts=PTS-STARTPTS[b];[a][b]hstack=inputs=2[v]','-map','[v]','-map','1:a:0','-c:v','libx264','-crf','18','-preset','fast','-c:a','copy','-t',str(dur),str(R/'output/body-loop-COMPARISON-TRIAL.mp4')]
subprocess.run(cmd,check=True)
report={'scope':[start,end],'source_pts_ticks':[t-ticks[start] for t in ticks[start:end]],'audio':'trial segment reencoded AAC; full production must copy original audio','duration_seconds':dur,'artistic_status':'not_accepted'}
(R/'analysis/body-loop-encode-trial.json').write_text(json.dumps(report,indent=2));print('encoded',dur)
