#!/usr/bin/env python3
import cv2,hashlib,json,math,os,urllib.request
from pathlib import Path
TASK="AH_R020_SHOT004_CANONICAL_CONTRACT_AUTHORING_20261002"
SOURCE_ID="1hNY1X6WxNebyt91Ha65-MHbI-M4sC6Ir"
SOURCE_BYTES=632252
SOURCE_SHA="b2632b34260a8d9eb1201aae89cf4e611cdcbf3c8502146dca38d1b684bc1c2e"
CALLBACK="https://hook.us2.make.com/z9tbdjw64o61sn2xmu5281fi0fmafcto"
UPLOAD=os.environ.get("AH_DRIVE_RESUMABLE_URL","")
W=Path("/kaggle/working"); src=W/"shot003_v2.mp4"; out=W/"AH_R020_SHOT004_LOCAL_SETTLE_V1.mp4"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def cb(payload):
 try:
  req=urllib.request.Request(CALLBACK,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"},method="POST")
  urllib.request.urlopen(req,timeout=20).read()
 except Exception: pass
with urllib.request.urlopen(f"https://drive.usercontent.google.com/download?id={SOURCE_ID}&export=download&confirm=t",timeout=120) as r: src.write_bytes(r.read())
if src.stat().st_size!=SOURCE_BYTES or sha(src)!=SOURCE_SHA: raise RuntimeError("SOURCE_IDENTITY_FAIL")
cap=cv2.VideoCapture(str(src)); frames=[]
while True:
 ok,fr=cap.read()
 if not ok: break
 frames.append(fr)
cap.release()
if len(frames)!=96: raise RuntimeError(f"SOURCE_FRAMECOUNT_FAIL:{len(frames)}")
base=frames[-1]
H,Wd=base.shape[:2]
if (Wd,H)!=(1080,1920): raise RuntimeError("SOURCE_GEOMETRY_FAIL")
fps=30.0; n=72
x0,x1,y0,y1=780,1080,500,1110
yy,xx=cv2.getGaussianKernel(y1-y0,120),cv2.getGaussianKernel(x1-x0,70)
mask=(yy@xx.T); mask=(mask/mask.max())[:,:,None].astype("float32")
writer=cv2.VideoWriter(str(out),cv2.VideoWriter_fourcc(*"mp4v"),fps,(Wd,H))
for i in range(n):
 t=i/(n-1)
 ease=0.5-0.5*math.cos(math.pi*min(1.0,t/0.58))
 fr=base.copy().astype("float32")
 roi=fr[y0:y1,x0:x1].copy()
 M=cv2.getRotationMatrix2D(((x1-x0)/2,(y1-y0)/2),-0.35*ease,1.0)
 M[0,2]+=-4.0*ease; M[1,2]+=7.0*ease
 warped=cv2.warpAffine(roi,M,(x1-x0,y1-y0),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
 fr[y0:y1,x0:x1]=roi*(1-mask*0.72*ease)+warped*(mask*0.72*ease)
 warm=max(0.0,(t-0.32)/0.68)
 fr[:,:,2]*=(1.0+0.018*warm); fr[:,:,1]*=(1.0+0.006*warm); fr[:,:,0]*=(1.0-0.004*warm)
 writer.write(fr.clip(0,255).astype("uint8"))
writer.release()
if not out.exists() or out.stat().st_size<100000: raise RuntimeError("OUTPUT_MISSING")
meta={"task_id":TASK,"event":"AH_R020_SHOT004_TERMINAL","state":"BINARY_CREATED","source_id":SOURCE_ID,"source_sha256":SOURCE_SHA,"output_name":out.name,"bytes":out.stat().st_size,"sha256":sha(out),"width":1080,"height":1920,"frames":72,"fps":30,"duration_s":2.4,"camera":"LOCKED","mutation":"bounded local upper-body settle + slight practical warmth"}
upload={"attempted":False}
if UPLOAD:
 data=out.read_bytes()
 req=urllib.request.Request(UPLOAD,data=data,headers={"Content-Type":"video/mp4","Content-Length":str(len(data))},method="PUT")
 with urllib.request.urlopen(req,timeout=600) as r: upload={"attempted":True,"status":r.status,"body":r.read(2000).decode(errors="replace")}
meta["drive_upload"]=upload
print(json.dumps(meta))
cb(meta)
