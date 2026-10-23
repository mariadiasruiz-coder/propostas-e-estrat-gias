# Estima a posição da cabeça a partir do matte (topo da silhueta + centróide da região da cabeça)
import cv2, glob, os, json, numpy as np
files=sorted(glob.glob('ext/matte/*.png'))
idx=[int(os.path.basename(f)[:5]) for f in files]
arr=[]
for f in files:
    m=cv2.imread(f,0).astype(np.float32)/255   # 1920x1080
    rows=np.where(m.max(1)>0.5)[0]
    top=rows.min() if len(rows) else 200
    head=m[top:top+330]                       # ~ altura da cabeça em 1080p
    ys,xs=np.where(head>0.5)
    cx=xs.mean() if len(xs) else 960
    wds=(head>0.5).sum(1); wd=np.median(wds[wds>0]) if (wds>0).any() else 400
    arr.append([cx*2, (top+190)*2, wd*2])   # em coordenadas 4K: centro aprox. dos olhos
arr=np.array(arr,float)
groups=[]; prev=None
for i,n in enumerate(idx):
    if prev is None or n!=prev+1: groups.append([])
    groups[-1].append(i); prev=n
out={}
for gi in groups:
    a=arr[gi]; k=12
    pad=np.pad(a,((k,k),(0,0)),mode='edge')
    sm=np.stack([np.convolve(pad[:,j],np.ones(2*k+1)/(2*k+1),mode='valid') for j in range(3)],1)
    for i,v in zip(gi,sm): out[idx[i]]=[round(float(x),1) for x in v]
json.dump(out,open('ext/face.json','w'))
v=np.array(list(out.values())); print('cx',v[:,0].min(),v[:,0].max(),'cy',v[:,1].min(),v[:,1].max(),'w',v[:,2].min(),v[:,2].max())
