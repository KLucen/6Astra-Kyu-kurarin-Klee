"""Left original / right Klee comparison with exact PTS and original AAC."""
import av,json,time
import numpy as np
from finish_v2 import R,M,TICKS,DUR,TB,stream,encode,mux

def main():
    t0=time.monotonic();left=av.open(M['source']);right=av.open(str(R/'output/Klee_Kyu-kurarin_ALICE_v3.mp4'))
    a=left.decode(video=0);b=right.decode(video=0)
    silent=R/'output/Klee_Kyu-kurarin_ALICE_COMPARE-silent.mp4'
    co=av.open(str(silent),'w',options={'video_track_timescale':'16000'});s=stream(co,width=3840,preset='veryfast',crf='20')
    for i in range(M['frames']):
        f1=next(a);f2=next(b)
        if f1.pts*f1.time_base!=f2.pts*f2.time_base or f1.pts*f1.time_base!=TICKS[i]*TB:raise RuntimeError(f'PTS mismatch {i}')
        # Concatenate Y/U/V planes directly; both inputs use limited-range BT.709 4:2:0.
        f=av.VideoFrame(3840,1080,'yuv420p')
        for dst,p1,p2 in zip(f.planes,f1.planes,f2.planes):
            x=np.frombuffer(p1,dtype=np.uint8).reshape(p1.height,p1.line_size)[:,:p1.width]
            y=np.frombuffer(p2,dtype=np.uint8).reshape(p2.height,p2.line_size)[:,:p2.width]
            buf=np.zeros((dst.height,dst.line_size),dtype=np.uint8);buf[:,:dst.width]=np.concatenate([x,y],axis=1);dst.update(buf)
        f.pts=TICKS[i];f.time_base=TB;f.duration=DUR[i];f.colorspace=1;f.color_range=1
        encode(co,s,f)
        if i%1200==0:print('COMPARE',i,'/',M['frames'],'seconds',round(time.monotonic()-t0,1),flush=True)
    encode(co,s,None);co.close();left.close();right.close()
    final=R/'output/Klee_Kyu-kurarin_ALICE_COMPARE.mp4';mux(silent,final);print('COMPARISON_READY',final,flush=True)

if __name__=='__main__':main()
