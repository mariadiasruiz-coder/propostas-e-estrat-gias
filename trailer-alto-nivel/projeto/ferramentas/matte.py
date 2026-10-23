import onnxruntime as ort, numpy as np, cv2, os, glob, time
so=ort.SessionOptions(); so.intra_op_num_threads=3
sess=ort.InferenceSession('models/rvm_mobilenetv3_fp32.onnx',so,providers=['CPUExecutionProvider'])
print([ (i.name,i.shape) for i in sess.get_inputs()])
files=sorted(glob.glob('ext/duda/*.jpg'))
idx=[int(os.path.basename(f)[:5]) for f in files]
rec=[np.zeros([1,1,1,1],np.float32)]*4; dr=np.array([0.25],np.float32)
prev=None; t0=time.time()
for k,(f,n) in enumerate(zip(files,idx)):
    if prev is None or n!=prev+1: rec=[np.zeros([1,1,1,1],np.float32)]*4
    prev=n
    im=cv2.imread(f); im=cv2.resize(im,(1920,1080),interpolation=cv2.INTER_AREA)
    src=(im[:,:,::-1].astype(np.float32)/255).transpose(2,0,1)[None]
    fgr,pha,*rec=sess.run(None,{'src':src,'r1i':rec[0],'r2i':rec[1],'r3i':rec[2],'r4i':rec[3],'downsample_ratio':dr})
    cv2.imwrite(f'ext/matte/{n:05d}.png',(pha[0,0]*255).clip(0,255).astype(np.uint8))
    if k%100==0: print(k,len(files),f'{time.time()-t0:.0f}s',flush=True)
print('done',time.time()-t0)
