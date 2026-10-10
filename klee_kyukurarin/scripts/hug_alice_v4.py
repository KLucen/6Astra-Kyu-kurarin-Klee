"""Fill the omitted wide-eyed Alice hug; retain the v3 closed-eyed cel."""
import json
import cv2
import numpy as np
from PIL import Image
from hug_alice import initialize as initialize_closed


def initialize():
    C = initialize_closed()
    name = 'hug-open-alice-f05784-v1'
    new = C.load_layer(name)
    registration = json.loads((C.R / 'analysis/alice-open-cel-registration.json').read_text())
    A = np.vstack([registration['new_to_original_cel'], [0, 0, 1]])
    old_size = Image.open(C.R / 'generated/hug-open-f05784-v1.png').size
    new_size = Image.open(C.R / 'generated' / f'{name}.png').size
    Sold = np.diag([1920 / old_size[0], 1080 / old_size[1], 1])
    Snew = np.diag([1920 / new_size[0], 1080 / new_size[1], 1])
    B = (Sold @ A @ np.linalg.inv(Snew))[:2].astype('float32')
    C.L['hug'] = cv2.warpAffine(new, B, (1920, 1080), flags=cv2.INTER_LANCZOS4)
    return C


if __name__ == '__main__':
    C = initialize()
    cap = cv2.VideoCapture(C.M['source'])
    for i in range(6040):
        ok, bgr = cap.read()
        if not ok:
            raise RuntimeError(i)
        if i not in [5784, 5900, 6038, 6039]:
            continue
        dst = C.render(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), i)
        cv2.imwrite(str(C.R / 'output/scene-draft-stills' / f'alice-v4-f{i:05d}.png'), cv2.cvtColor(dst, cv2.COLOR_RGB2BGR))
    cap.release()
    print('Alice v4 aligned composite samples saved', flush=True)
