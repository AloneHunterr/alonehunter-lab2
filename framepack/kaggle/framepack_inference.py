#!/usr/bin/env python3
"""ALONEHUNTER Video Factory — FramePack headless physical MP4 microproof."""
from __future__ import annotations
import hashlib,json,os,shutil,subprocess,sys,time,urllib.request
from pathlib import Path
W=Path('/kaggle/working'); R=W/'FramePack'; OUT=W/'AH_FRAMEPACK_SANITY.mp4'; REC=W/'AH_FRAMEPACK_INFERENCE_RECEIPT.json'; MAN=W/'AH_FRAMEPACK_ARTIFACT_MANIFEST.json'
PROMPT=os.environ.get('AH_VIDEO_PROMPT','cinematic rainy railway platform at night, subtle natural motion, locked camera, realistic light reflections, premium music video')
CALLBACK='https://hook.us2.make.com/z9tbdjw64o61sn2xmu5281fi0fmafcto'
def run(cmd,timeout=3600,cwd=None):
 t=time.time(); p=subprocess.run(cmd,text=True,capture_output=True,timeout=timeout,cwd=cwd); return {'cmd':cmd,'returncode':p.returncode,'seconds':round(time.time()-t,3),'stdout':p.stdout[-24000:],'stderr':p.stderr[-24000:]}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''): h.update(c)
 return h.hexdigest()
def gpu(): return run(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,memory.free','--format=csv,noheader,nounits'],60)
def find_mp4():
 xs=sorted((R/'outputs').glob('*.mp4'),key=lambda p:p.stat().st_mtime,reverse=True) if (R/'outputs').exists() else []; return xs[0] if xs else None
def callback(payload):
 try:
  b=json.dumps(payload,ensure_ascii=False).encode(); req=urllib.request.Request(CALLBACK,data=b,headers={'Content-Type':'application/json'},method='POST')
  with urllib.request.urlopen(req,timeout=20) as r: return {'status':r.status,'body':r.read(1000).decode(errors='replace')}
 except Exception as e: return {'error':repr(e)}
def main():
 rec={'schema':'AH_FRAMEPACK_INFERENCE_V3','adapter':'upstream_worker_direct','started':time.time(),'prompt':PROMPT,'gpu_before':gpu(),'disk_before':shutil.disk_usage(W)._asdict(),'steps':{}}
 if R.exists(): shutil.rmtree(R)
 rec['steps']['clone']=run(['git','clone','--depth','1','https://github.com/lllyasviel/FramePack.git',str(R)],300)
 if rec['steps']['clone']['returncode']!=0: return finish(rec,False,'clone_failed')
 rec['steps']['commit']=run(['git','-C',str(R),'rev-parse','HEAD'],60)
 rec['steps']['install']=run([sys.executable,'-m','pip','install','-r',str(R/'requirements.txt')],1200)
 if rec['steps']['install']['returncode']!=0: return finish(rec,False,'dependency_install_failed')
 adapter=R/'ah_headless_adapter.py'
 adapter.write_text(r'''import os,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent; os.chdir(ROOT); sys.argv=[str(ROOT/'demo_gradio.py')]
src=(ROOT/'demo_gradio.py').read_text(encoding='utf-8'); cut=src.rfind('\nblock.launch(')
if cut < 0: raise RuntimeError('upstream_launch_boundary_not_found')
src=src[:cut]; ns={'__name__':'ah_framepack_upstream','__file__':str(ROOT/'demo_gradio.py')}; exec(compile(src,str(ROOT/'demo_gradio.py'),'exec'),ns,ns)
h,w=360,640; y=np.linspace(0,1,h,dtype=np.float32)[:,None]; x=np.linspace(0,1,w,dtype=np.float32)[None,:]; img=np.zeros((h,w,3),dtype=np.uint8)
img[...,0]=(12+18*y).astype(np.uint8); img[...,1]=(18+25*y).astype(np.uint8); img[...,2]=(28+45*y+8*x).astype(np.uint8); img[250:255,:,:]=110; img[285:292,:,:]=65
prompt=os.environ.get('AH_VIDEO_PROMPT','cinematic rainy railway platform at night, subtle natural motion, locked camera, realistic light reflections, premium music video')
ns['worker'](img,prompt,'',31337,1.0,9,4,1.0,10.0,0.0,6.0,True,20); print('AH_HEADLESS_WORKER_RETURNED=1')
''',encoding='utf-8')
 rec['steps']['adapter']=run([sys.executable,str(adapter)],7200,cwd=str(R)); candidate=find_mp4()
 if not candidate or candidate.stat().st_size<1024: return finish(rec,False,'headless_worker_returned_without_physical_mp4')
 shutil.copy2(candidate,OUT); rec['source_mp4']=str(candidate); return finish(rec,True,None)
def finish(rec,ok,reason):
 rec['pass']=ok; rec['failure_reason']=reason; rec['gpu_after']=gpu(); rec['disk_after']=shutil.disk_usage(W)._asdict(); rec['finished']=time.time(); rec['elapsed_s']=round(rec['finished']-rec['started'],3)
 arts=[]
 if OUT.exists(): arts.append({'role':'video','filename':OUT.name,'path':str(OUT),'mime_type':'video/mp4','bytes':OUT.stat().st_size,'sha256':sha(OUT)})
 REC.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8'); arts.append({'role':'inference_receipt','filename':REC.name,'path':str(REC),'mime_type':'application/json','bytes':REC.stat().st_size,'sha256':sha(REC)})
 manifest={'schema':'AH_FRAMEPACK_ARTIFACT_MANIFEST_V1','artifacts':arts}; MAN.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 cb=callback({'event':'AH_FRAMEPACK_TERMINAL','receipt':rec,'manifest':manifest}); print('AH_CALLBACK='+json.dumps(cb)); print('AH_FRAMEPACK_INFERENCE='+json.dumps(rec,ensure_ascii=False)); print('AH_ARTIFACT_MANIFEST='+MAN.read_text()); return 0 if ok else 2
if __name__=='__main__': raise SystemExit(main())
