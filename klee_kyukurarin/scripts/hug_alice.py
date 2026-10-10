"""User-requested Alice substitution only within the closed-eye hug exposures."""
import cv2,json,numpy as np
from PIL import Image
import composite_core as C

def initialize():
    cv2.setNumThreads(1);C.init_tracks()
    new_name='hug-closed-alice-f06039-v1'
    new=C.load_layer(new_name)
    A=np.vstack([np.array(json.loads((C.R/'analysis/alice-cel-registration.json').read_text())['new_to_original_cel']),[0,0,1]])
    old_size=Image.open(C.R/'generated/hug-closed-f06039-v1.png').size
    new_size=Image.open(C.R/'generated'/f'{new_name}.png').size
    Sold=np.diag([1920/old_size[0],1080/old_size[1],1]);Snew=np.diag([1920/new_size[0],1080/new_size[1],1])
    B=(Sold@A@np.linalg.inv(Snew))[:2].astype('float32')
    C.L['hug_closed']=cv2.warpAffine(new,B,(1920,1080),flags=cv2.INTER_LANCZOS4)
    return C

if __name__=='__main__':
    C=initialize();cap=cv2.VideoCapture(C.M['source'])
    for i in range(6264):
        ok,bgr=cap.read()
        if i not in [6039,6080,6200,6263]:continue
        dst=C.render(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB),i)
        cv2.imwrite(str(C.R/'output/scene-draft-stills'/f'alice-f{i:05d}.png'),cv2.cvtColor(dst,cv2.COLOR_RGB2BGR))
    cap.release();print('Alice aligned composite samples saved')
