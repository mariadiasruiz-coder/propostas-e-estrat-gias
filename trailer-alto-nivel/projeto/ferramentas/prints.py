import subprocess, numpy as np, cv2
W,H=3840,2160
def frames(ss,dur,step=6):
    p=subprocess.run(['ffmpeg','-v','error','-ss',str(ss),'-i','src/original.mov','-t',str(dur),'-vf',f'fps=30,select=not(mod(n\\,{step}))','-f','rawvideo','-pix_fmt','bgr24','-'],capture_output=True)
    a=np.frombuffer(p.stdout,np.uint8).reshape(-1,H,W,3); return a
for name,ss,dur in [('sara',40.0,6.8),('bianca',47.1,4.3),('rutilla',59.2,5.6)]:
    a=frames(ss,dur)
    bbs=[]
    for f in a:
        ys,xs=np.where(f.max(2)>18); bbs.append((xs.min(),xs.max(),ys.min(),ys.max()))
    print(name,len(a),set(bbs))
    med=np.median(a,axis=0).astype(np.uint8)
    x0,x1,y0,y1=bbs[len(bbs)//2]
    cv2.imwrite(f'ext/prints/{name}.png',med[y0:y1+1,x0:x1+1])
    print(name,'crop',x0,x1,y0,y1)
