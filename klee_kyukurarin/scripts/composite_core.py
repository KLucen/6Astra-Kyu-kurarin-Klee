"""Per-frame source-preserving draft compositor; artistic acceptance is separate."""
import cv2,numpy as np,json
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];W=1920;H=1080
M=json.loads((R/'analysis/source_meta.json').read_text())
ASSETS={'profile':'profile-f01173-v1','cheeks':'cheeks-closed-f01408-v1','rest':'cheeks-rest-f01632-v1','open':'cheeks-open-f03555-v1','covered':'face-covered-f03748-v1','sleep':'sleeping-head-f02493-v1','sit':'bed-sitting-f04544-v1','down':'head-down-f04712-v1','flowers':'flower-hands-f04760-v1','clock':'clock-hand-f00120-v1','hug':'hug-open-f05784-v1','hug_closed':'hug-closed-f06039-v1','cry':'crying-f05573-v1','upside':'upside-cry-upright-f05304-v1'}
BODY=['anchor-f01027-v1','pose02-f00138-v2','pose03-f00146-v1','pose04-f00154-v2','pose05-f00162-v2','pose06-f00170-v1','pose07-f00178-v1']
def load_layer(n):
    a=np.array(Image.open(R/'generated'/f'{n}.png').convert('RGBA'))
    if n==BODY[0]:
        rgb=a[:,:,:3].astype(int);bg=(rgb[:,:,0]>210)&(rgb[:,:,1]>125)&(rgb[:,:,1]<220)&(rgb[:,:,2]>rgb[:,:,1]+6)&(rgb[:,:,0]>rgb[:,:,2]+10)
        _,lab,_,_=cv2.connectedComponentsWithStats(bg.astype('uint8'));ids=np.unique(np.r_[lab[0],lab[-1],lab[:,0],lab[:,-1]]);ids=ids[ids>0];a[:,:,3][np.isin(lab,ids)]=0;a[:,:600,3]=0;a[:,1200:,3]=0
    # Suppress near-transparent matte fringing without changing opaque artwork.
    a[:,:,3][a[:,:,3]<12]=0
    return cv2.resize(a,(W,H),interpolation=cv2.INTER_LANCZOS4)
L={k:load_layer(v) for k,v in ASSETS.items()};BL=[load_layer(n) for n in BODY]
L['upside']=load_layer('upside-cry-upright-f05304-v2')
L['mouth_o']=load_layer('cheeks-mouth-o-f01504-v1');L['mouth_tiny']=load_layer('cheeks-mouth-tiny-f01496-v1');L['mouth_teeth']=load_layer('cheeks-mouth-teeth-f01432-v1')
L['upside']=cv2.flip(L['upside'],0)
# Artist/source anchor registration for seated body, measured from face and resting hand.
L['sit']=cv2.warpAffine(L['sit'],np.float32([[.8,0,210],[0,.8,36]]),(W,H))
I=np.float32([[1,0,0],[0,1,0]])
CURRENT_GRADE=1.0
CLOCK_CLEAR=cv2.cvtColor(cv2.imread(str(R/'refs/source-f00090.png')),cv2.COLOR_BGR2RGB)
_clock=cv2.cvtColor(cv2.imread(str(R/'refs/source-f00120.png')),cv2.COLOR_BGR2RGB).astype(int)
_cm=(np.max(abs(_clock-np.array([251,218,222])),axis=2)<13)|(np.max(abs(_clock-np.array([247,176,203])),axis=2)<13)
_cz=np.zeros((H,W),np.uint8);_cz[325:1080,575:1330]=1;_cm=(_cm&_cz.astype(bool)).astype('uint8')*255
_contours,_=cv2.findContours(_cm,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);_allpts=np.concatenate([c for c in _contours if cv2.contourArea(c)>200]);_hull=cv2.convexHull(_allpts);cv2.fillConvexPoly(_cm,_hull,255);CLOCK_HAND_MASK=cv2.dilate(_cm,np.ones((19,19),np.uint8))
_layer_boxes={}
def composite(dst,layer,A=None):
    key=id(layer)
    if key not in _layer_boxes:
        yy,xx=np.where(layer[:,:,3]>0);_layer_boxes[key]=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))
    sx0,sy0,sx1,sy1=_layer_boxes[key];A=I if A is None else np.float32(A)
    corners=np.float32([[sx0,sy0],[sx1,sy0],[sx1,sy1],[sx0,sy1]])@A[:,:2].T+A[:,2]
    x0=max(0,int(np.floor(corners[:,0].min()))-2);y0=max(0,int(np.floor(corners[:,1].min()))-2);x1=min(W,int(np.ceil(corners[:,0].max()))+2);y1=min(H,int(np.ceil(corners[:,1].max()))+2)
    if x1<=x0 or y1<=y0:return dst
    T=A.copy();T[:,2]+=T[:,:2]@np.float32([sx0,sy0])-np.float32([x0,y0]);a=cv2.warpAffine(layer[sy0:sy1,sx0:sx1],T,(x1-x0,y1-y0),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0));alpha=a[:,:,3:4].astype(np.float32)/255
    dst[y0:y1,x0:x1]=np.clip(dst[y0:y1,x0:x1].astype(np.float32)*(1-alpha)+a[:,:,:3].astype(np.float32)*CURRENT_GRADE*alpha,0,255).astype('uint8');return dst
def background(src,left=False):
    lo,hi=(15,170) if left else (1780,1880)
    return np.median(src[:,lo:hi],axis=1).astype('uint8')
def solid_components(mask,minarea=1500):
    n,lab,stats,_=cv2.connectedComponentsWithStats(mask.astype('uint8'))
    ids=[k for k in range(1,n) if stats[k,4]>minarea];m=np.isin(lab,ids).astype('uint8')*255
    contours,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE);cv2.drawContours(m,contours,-1,255,-1)
    return m
def actor_mask(src,bg):
    d=np.max(abs(src.astype(np.int16)-bg[:,None,:].astype(np.int16)),axis=2);mask=(d>9).astype('uint8');mask[:,:5]=0;mask[:,-5:]=0
    mask=cv2.dilate(solid_components(mask),np.ones((7,7),np.uint8))>0
    mask[:,:5]=mask[:,5:6];mask[:,-5:]=mask[:,-6:-5]
    return mask
def erase_actor(src,bg):
    out=src.copy();mask=actor_mask(src,bg);out[mask]=np.broadcast_to(bg[:,None,:],src.shape)[mask];return out
def restore_lyrics(src,dst,fam):
    s=src.astype(int);white=(s[:,:,0]>228)&(s[:,:,1]>222)&(s[:,:,2]>224)&(np.max(s,axis=2)-np.min(s,axis=2)<40)
    zone=np.zeros((H,W),np.uint8)
    if fam in ['sleep','sleep_late','sit']:zone[100:300,600:1300]=1
    elif fam=='upside':zone[400:710,1240:1780]=1
    elif fam=='flowers':zone[360:660,1340:1790]=1
    else:zone[120:800,1330:1850]=1
    mask=(white&zone.astype(bool)).astype('uint8');mask=cv2.dilate(mask,np.ones((2,2),np.uint8))>0;dst[mask]=src[mask];return dst
def get_A(row):return np.float32(row.get('affine',I))
def init_tracks():
    global SC,BC,BY_PHASE,ISSUES,REG,BODY_BLANK
    BODY_BLANK=set(json.loads((R/'analysis/body-source-blank-frames.json').read_text()))
    SC=json.loads((R/'analysis/scene_tracks.json').read_text())['rows'];BC={x['frame']:x['layers'] for x in json.loads((R/'analysis/body_tracks_proposal.json').read_text())['frames']};BY_PHASE={};ISSUES=[];REG=json.loads((R/'analysis/expression_reference_registration.json').read_text())
    for i,ls in BC.items():
        section=0 if i<2000 else 1;start=128 if section==0 else 2912;phase=(i-start)%64;active=0 if section==0 and phase>=60 else min(7,phase//8+1)
        for z in ls:
            if z['pose']>active:continue
            key=(section,phase,z['pose']);BY_PHASE.setdefault(key,[]).append((i,z))
def body_layers(i):
    if i in BODY_BLANK:return []
    section=0 if i<2000 else 1;start=128 if section==0 else 2912;phase=(i-start)%64;active=0 if section==0 and phase>=60 else min(7,phase//8+1);out=[]
    for pid in range(1,active+1):
        # In the second passage the straight-leg cel is still outside the frame at 16..20.
        # Source frames 2928..2932 show only the previous upper cel and the phone cel.
        if section==1 and pid==3 and 16<=phase<=20:continue
        direct=next((x for x in BC.get(i,[]) if x['pose']==pid),None);pool=BY_PHASE.get((section,phase,pid),[])
        chosen=direct or (max(pool,key=lambda q:q[1]['inliers'])[1] if pool else None)
        if chosen is None:ISSUES.append({'frame':i,'pose':pid,'status':'body_missing'});continue
        dx,dy=chosen['translation'];donor=None
        if phase<56 and phase%8==0 and pid==active:
            # Source entrants at phase 0 descend from the top; distinguish them from settled copies.
            expected=-578.2-(500 if section==1 and pid!=2 else 0)
            valid=[q for q in pool if abs(q[1]['translation'][0])<25 and q[1]['translation'][1]<-450]
            if valid:
                donor,z=max(valid,key=lambda q:q[1]['inliers']);dx,dy=z['translation']
            elif abs(dx)>25 or dy>-450:
                dx=0;dy=expected;ISSUES.append({'frame':i,'pose':pid,'status':'entry_pattern_needs_pixel_review'})
        if direct is None:ISSUES.append({'frame':i,'pose':pid,'status':'same_exposure_source_registration_donor','donor':donor})
        out.append((pid,np.float32([[1,0,dx],[0,1,dy]])))
    return out
def scene_layers(row,src):
    fam=row['family'];A=get_A(row);name=fam
    if fam=='cheeks':
        i=row['frame']
        # Read the mouth in canonical source coordinates, preserving actual lip-sync exposures.
        canon=cv2.warpAffine(src,cv2.invertAffineTransform(A),(W,H));mouth=canon[514:590,810:935].astype(int)
        pink=(mouth[:,:,0]>mouth[:,:,1]+45)&(mouth[:,:,2]>mouth[:,:,1]+15);white=(mouth[:,:,0]>239)&(mouth[:,:,1]>230)&(mouth[:,:,2]>230)
        # Fringe pixels along the cuff are pink too; classify the connected mouth interior.
        _,_,stats,_=cv2.connectedComponentsWithStats(pink.astype('uint8'))
        area=int(stats[1:,4].max()) if len(stats)>1 else 0
        if 1664<=i<1888:name='open'
        elif 1536<=i<1664:name='rest'
        elif area>2000:name='cheeks'
        elif area>500:name='mouth_o'
        elif white.sum()>300:name='mouth_teeth'
        elif area>180:name='mouth_tiny'
        else:name='rest'
        # All three replacement expressions share the same new cel geometry.
    def adjust(B):
        if fam in ['open','covered','hug_closed']:
            BB=np.vstack([B,[0,0,1]]);RR=np.vstack([REG[fam],[0,0,1]]);return (BB@RR)[:2].astype('float32')
        return B
    if fam in ['profile','cheeks','open','covered','upside','hug','hug_closed']:
        # Repeated source drawings: use source one-to-many feature offsets, not motion interpolation.
        votes=row.get('copy_votes',[])
        AA=[]
        for z in votes:
            B=A.copy();B[:,2]=z['translation']
            AA.append(adjust(B))
        if not AA:AA=[adjust(A)]
        # Rightmost figure is in front in the inspected source echo scenes.
        return [(name,a) for a in sorted(AA,key=lambda a:a[0,2])]
    return [(name,adjust(A))]
def render(src,i):
    global CURRENT_GRADE
    row=SC[i];fam=row['family']
    rgbsmall=cv2.resize(src,(480,270)).astype(int);hair=(rgbsmall[:,:,1]-rgbsmall[:,:,0]>7)&(rgbsmall[:,:,1]-rgbsmall[:,:,0]<37)&(abs(rgbsmall[:,:,1]-rgbsmall[:,:,2])<14)&(rgbsmall[:,:,0]>45)&(rgbsmall[:,:,0]<165);hair[:,:4]=False;hair[:,-4:]=False
    CURRENT_GRADE=float(np.clip(np.median(rgbsmall[hair])/145,.65,1.04)) if hair.sum()>200 else 1.0
    if fam=='blank':return src
    if fam=='body':
        ls=body_layers(i)
        if not ls:return src
        bg=background(src);dst=erase_actor(src,bg)
        for pid,A in ls:dst=composite(dst,BL[pid-1],A)
        return restore_lyrics(src,dst,fam)
    if not row.get('present'):return src
    if 'affine' not in row and fam not in ['sleep','sleep_late']:
        ISSUES.append({'frame':i,'family':fam,'status':'registration_missing_used_identity_for_draft'})
    if fam in ['sleep','sleep_late']:
        bbox=row.get('hair_bbox')
        if not bbox:ISSUES.append({'frame':i,'family':fam,'status':'hair_missing'});return src
        x,y,w,h=bbox
        # Match the visible original crown's scale; preserve original bed pixels outside the crown.
        A=np.float32([[w/195,0,x-w/195*1205],[0,h/137,y-h/137*510]])
        dst=src.copy();rgb=src.astype(int);hair=(rgb[:,:,1]>rgb[:,:,0]+5)&(rgb[:,:,1]>=rgb[:,:,2]-7)&(rgb[:,:,0]<205)
        zone=np.zeros((H,W),np.uint8);zone[max(0,y-10):min(H,y+h+10),max(0,x-10):min(W,x+w+10)]=1;mask=cv2.dilate((hair&zone.astype(bool)).astype('uint8'),np.ones((5,5),np.uint8))>0
        pillow=np.median(src[min(H-1,y+h//2),min(W-1,x+w+15):min(W,x+w+55)],axis=0).astype('uint8');dst[mask]=pillow
        dst=composite(dst,L['sleep'],A)
        # Preserve the actual foreground blanket where it covers the crown.
        blanket=(rgb[:,:,0]>175)&(np.max(rgb,axis=2)-np.min(rgb,axis=2)<45)&(~hair)&zone.astype(bool)
        yy=np.arange(H)[:,None];blanket&=yy>y+int(h*.45);dst[blanket]=src[blanket]
        return restore_lyrics(src,dst,fam)
    if fam=='sit':
        A=get_A(row);rgb=src.astype(int);bg=background(src);dst=src.copy()
        # Original head and pajama material are independent from the original bed and duvet.
        nearpink=(abs(rgb[:,:,0]-247)<22)&(abs(rgb[:,:,1]-175)<22)&(abs(rgb[:,:,2]-207)<22)
        green=(rgb[:,:,1]>rgb[:,:,0]+5)&(rgb[:,:,1]>=rgb[:,:,2]-7)&(rgb[:,:,0]<205)
        zone=np.zeros((H,W),np.uint8);zone[245:780,1010:1400]=1
        mask=cv2.dilate(solid_components((nearpink|green)&zone.astype(bool),400),np.ones((7,7),np.uint8))>0
        yy=np.arange(H)[:,None];top=mask&(yy<558);bot=mask&(~top);dst[top]=np.broadcast_to(bg[:,None,:],src.shape)[top];dst[bot]=np.median(src[800:820,1100:1400],axis=(0,1))
        # Old foreground resting hand is the duvet's color; remove just its outline.
        dst[696:754,1045:1155]=np.median(src[790:810,1100:1300],axis=(0,1))
        dst=composite(dst,L['sit'],A);return restore_lyrics(src,dst,fam)
    if fam=='clock':
        # Restore the original unobstructed clock under the independently registered hand.
        dst=src.copy();A=get_A(row);B=np.float32(row.get('clock_background_affine',A));clear=cv2.warpAffine(CLOCK_CLEAR,B,(W,H),borderMode=cv2.BORDER_REPLICATE);mask=cv2.warpAffine(CLOCK_HAND_MASK,A,(W,H))>0;dst[mask]=clear[mask]
        dst=composite(dst,L['clock'],get_A(row));return dst
    bg=background(src,left=fam=='flowers');dst=erase_actor(src,bg)
    for name,A in scene_layers(row,src):dst=composite(dst,L[name],A)
    if fam=='flowers':
        # Original pink hairpins and their dark stems are foreground props.
        A=get_A(row);inv=cv2.invertAffineTransform(A);canon=cv2.warpAffine(src,inv,(W,H));rgb=canon.astype(int);props=np.zeros((H,W),np.uint8)
        props[525:890,770:1160]=255
        pink=(rgb[:,:,0]>rgb[:,:,1]+35)&(rgb[:,:,2]>rgb[:,:,1]+15);dark=np.max(rgb,axis=2)<150
        seed=cv2.morphologyEx(((props>0)&pink).astype('uint8'),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
        petals=cv2.dilate(seed,np.ones((5,5),np.uint8))
        stems=np.zeros((H,W),np.uint8)
        for poly in [[[970,530],[993,538],[995,690],[976,691]],[[877,699],[911,699],[911,860],[881,860]],[[1094,741],[1122,748],[1064,891],[1033,885]],[[906,780],[955,735],[972,747],[918,796]]]:cv2.fillPoly(stems,[np.int32(poly)],1)
        skin=np.median(rgb[600:615,1165:1180],axis=(0,1));away=np.max(abs(rgb-skin),axis=2)>32
        props=(((petals>0)&away)|((stems>0)&dark)).astype('uint8');props=cv2.warpAffine(props,A,(W,H))>0;dst[props]=src[props]
    return restore_lyrics(src,dst,fam)
