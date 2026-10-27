import numpy as np
from PIL import Image, ImageFilter
from rembg import remove, new_session
# Head: rembg for clean edges
im = Image.open("logo.jpg").convert("RGB")
s = new_session("isnet-general-use")
head = remove(im, session=s)
a = np.array(head)
ys, xs = np.where(a[:,:,3] > 10)
print("head bbox", xs.min(), xs.max(), ys.min(), ys.max())
head.crop((xs.min(), ys.min(), xs.max()+1, ys.max()+1)).save("web/head.png")
# Desk scene: character layer
m = Image.open("mascot.jpg").convert("RGB")
ch = remove(m, session=s)
b = np.array(ch); ys, xs = np.where(b[:,:,3] > 10)
print("char bbox", xs.min(), xs.max(), ys.min(), ys.max())
ch.save("web/char.png")
m.save("web/desk.jpg", quality=95)
im.save("web/logo.jpg", quality=95)
