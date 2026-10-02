#!/usr/bin/env python3
import cv2, numpy as np, os, sys, subprocess, hashlib, urllib.request, json
SRC_ID="1VJ7JrwubK5bjysc-ZPx3BwrcakqmCjfE"; SRC_BYTES=534907; SRC_SHA="df1c7f013131d0c693b3b3d38f8ce0610ea12777272572f6312b28af9c15f579"
OUT="/kaggle/working/AH_R020_SHOT005_LOCAL_DOOR_OPEN_V1.mp4"
UPLOAD=os.environ["AH_DRIVE_RESUMABLE_URL"]
subprocess.check_call([sys.executable,"-m","pip","-q","install","gdown","opencv-python-headless"])
import gdown
src="/kaggle/working/shot004.mp4"; gdown.download(id=SRC_ID,output=src,quiet=False)
if os.path.getsize(src)!=SRC_BYTES: raise RuntimeError(f"SOURCE_BYTES_FAIL:{os.path.getsize(src)}")
h=hashlib.sha256(open(src,"rb").read()).hexdigest()
if h!=SRC_SHA: raise RuntimeError("SOURCE_SHA_FAIL")
subprocess.check_call(["ffmpeg","-y","-sseof","-0.05","-i",src,"-frames:v","1","/kaggle/working/base.png"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
img=cv2.imread("/kaggle/working/base.png"); H,W=img.shape[:2]
x0,y0,x1,y1=900,260,1078,1500; door=img[y0:y1,x0:x1].copy()
warm=door.astype(np.float32); warm[:,:,2]=np.clip(warm[:,:,2]*1.10+6,0,255); warm[:,:,1]=np.clip(warm[:,:,1]*1.04+3,0,255); warm[:,:,0]=np.clip(warm[:,:,0]*0.96,0,255); warm=cv2.GaussianBlur(warm.astype(np.uint8),(0,0),1.1)
arm_src=img[610:980,955:1078].copy(); srcq=np.array([[0,0],[arm_src.shape[1]-1,0],[arm_src.shape[1]-1,arm_src.shape[0]-1],[0,arm_src.shape[0]-1]],np.float32)
def sm(t): return t*t*(3-2*t)
def frame(t):
 f=img.copy(); u=sm(np.clip((t-.18)/.62,0,1)); nl=x0+(x1-x0)*.62*u
 if nl>x0+1:
  poly=np.array([[x0,y0],[int(nl),y0+int(10*u)],[int(nl),y1-int(8*u)],[x0,y1]],np.int32); mask=np.zeros((H,W),np.uint8); cv2.fillPoly(mask,[poly],255); full=np.zeros_like(img); full[y0:y1,x0:x1]=warm; m=cv2.GaussianBlur(mask,(0,0),1.2).astype(np.float32)/255.; f=(f.astype(np.float32)*(1-m[...,None])+full.astype(np.float32)*m[...,None]).astype(np.uint8)
 closed=np.array([[x0,y0],[x1,y0],[x1,y1],[x0,y1]],np.float32); dst=np.array([[nl,y0+10*u],[x1,y0],[x1,y1],[nl,y1-8*u]],np.float32); P=cv2.getPerspectiveTransform(closed,dst); layer=np.zeros_like(img); layer[y0:y1,x0:x1]=door; warp=cv2.warpPerspective(layer,P,(W,H)); mm=np.zeros((H,W),np.uint8); mm[y0:y1,x0:x1]=255; wm=cv2.GaussianBlur(cv2.warpPerspective(mm,P,(W,H)),(0,0),.8).astype(np.float32)/255.; f=(f.astype(np.float32)*(1-wm[...,None])+(warp.astype(np.float32)*.98)*wm[...,None]).astype(np.uint8)
 a=sm(np.clip((t-.1)/.5,0,1)); sh=np.array([1015,670.]); hand=np.array([1005,875.])*(1-a)+np.array([923,865.])*a; v=hand-sh; L=np.linalg.norm(v); n=np.array([-v[1],v[0]])/(L+1e-6); dq=np.array([sh+n*24,sh-n*24,hand-n*13,hand+n*13],np.float32); P2=cv2.getPerspectiveTransform(srcq,dq); ar=cv2.warpPerspective(arm_src,P2,(W,H)); am=cv2.warpPerspective(np.ones(arm_src.shape[:2],np.uint8)*255,P2,(W,H)); am=cv2.GaussianBlur(am,(0,0),2).astype(np.float32)/255.*.72*a; f=(f.astype(np.float32)*(1-am[...,None])+ar.astype(np.float32)*am[...,None]).astype(np.uint8); return f
tmp="/kaggle/working/tmp.mp4"; vw=cv2.VideoWriter(tmp,cv2.VideoWriter_fourcc(*"mp4v"),30,(W,H))
for i in range(78): vw.write(frame(i/77))
vw.release()
subprocess.check_call(["ffmpeg","-y","-i",tmp,"-c:v","libx264","-pix_fmt","yuv420p","-r","30","-t","2.6","-crf","18",OUT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
b=open(OUT,"rb").read(); sha=hashlib.sha256(b).hexdigest()
req=urllib.request.Request(UPLOAD,data=b,headers={"Content-Type":"video/mp4","Content-Length":str(len(b))},method="PUT")
with urllib.request.urlopen(req,timeout=600) as r: body=r.read().decode(errors="replace")
print(json.dumps({"state":"PASS_LOCAL_SHOT005","bytes":len(b),"sha256":sha,"upload_status":r.status,"upload_body":body[:1000]},ensure_ascii=False))
