#!/usr/bin/env python3
"""ALONEHUNTER Video Factory — FramePack headless physical MP4 microproof.
V5: Kaggle-disk-safe NF4 model route + durable telemetry.
"""
from __future__ import annotations
import hashlib,json,os,shutil,subprocess,sys,time,traceback,urllib.request,threading
from pathlib import Path
W=Path('/kaggle/working'); R=W/'FramePack'; OUT=W/'AH_FRAMEPACK_SANITY.mp4'; REC=W/'AH_FRAMEPACK_INFERENCE_RECEIPT.json'; MAN=W/'AH_FRAMEPACK_ARTIFACT_MANIFEST.json'
PROMPT=os.environ.get('AH_VIDEO_PROMPT','cinematic rainy railway platform at night, subtle natural motion, locked camera, realistic light reflections, premium music video')
CALLBACK='https://hook.us2.make.com/z9tbdjw64o61sn2xmu5281fi0fmafcto'
SCHEMA='AH_FRAMEPACK_INFERENCE_V5_NF4'; HEARTBEAT_S=60

def callback(payload):
 try:
  b=json.dumps(payload,ensure_ascii=False,default=str).encode(); req=urllib.request.Request(CALLBACK,data=b,headers={'Content-Type':'application/json'},method='POST')
  with urllib.request.urlopen(req,timeout=20) as r: return {'status':r.status,'body':r.read(1000).decode(errors='replace')}
 except Exception as e: return {'error':repr(e)}

def gpu():
 try:
  p=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,memory.free','--format=csv,noheader,nounits'],text=True,capture_output=True,timeout=30)
  return {'returncode':p.returncode,'stdout':p.stdout[-8000:],'stderr':p.stderr[-8000:]}
 except Exception as e: return {'error':repr(e)}

def disk():
 try:
  d=shutil.disk_usage(W); return {'total':d.total,'used':d.used,'free':d.free,'free_gib':round(d.free/1024**3,3)}
 except Exception as e:return {'error':repr(e)}

def emit(event,rec,**extra):
 payload={'event':event,'schema':SCHEMA,'ts':time.time(),'stage':rec.get('stage'),'elapsed_s':round(time.time()-rec['started'],3),'gpu':gpu(),'disk':disk(),**extra}
 result=callback(payload); print('AH_TELEMETRY='+json.dumps({'payload':payload,'callback':result},ensure_ascii=False,default=str),flush=True); return result

def run(cmd,timeout=3600,cwd=None,rec=None,stage=None):
 if rec is not None and stage:
  rec['stage']=stage; emit('AH_FRAMEPACK_STAGE_START',rec,command=cmd)
 t=time.time()
 try:
  p=subprocess.run(cmd,text=True,capture_output=True,timeout=timeout,cwd=cwd)
  out={'cmd':cmd,'returncode':p.returncode,'seconds':round(time.time()-t,3),'stdout':p.stdout[-24000:],'stderr':p.stderr[-24000:]}
 except subprocess.TimeoutExpired as e:
  out={'cmd':cmd,'returncode':None,'timeout':True,'seconds':round(time.time()-t,3),'stdout':(e.stdout or '')[-24000:] if isinstance(e.stdout,str) else repr(e.stdout),'stderr':(e.stderr or '')[-24000:] if isinstance(e.stderr,str) else repr(e.stderr)}
 if rec is not None and stage:
  rec['steps'][stage]=out; emit('AH_FRAMEPACK_STAGE_END',rec,step=out)
 return out

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''): h.update(c)
 return h.hexdigest()

def find_mp4():
 xs=sorted((R/'outputs').glob('*.mp4'),key=lambda p:p.stat().st_mtime,reverse=True) if (R/'outputs').exists() else []; return xs[0] if xs else None

def heartbeat(rec,stop):
 while not stop.wait(HEARTBEAT_S): emit('AH_FRAMEPACK_HEARTBEAT',rec)

def finish(rec,ok,reason):
 rec['pass']=ok; rec['failure_reason']=reason; rec['gpu_after']=gpu(); rec['disk_after']=disk(); rec['finished']=time.time(); rec['elapsed_s']=round(rec['finished']-rec['started'],3); rec['stage']='terminal'
 arts=[]
 if OUT.exists(): arts.append({'role':'video','filename':OUT.name,'path':str(OUT),'mime_type':'video/mp4','bytes':OUT.stat().st_size,'sha256':sha(OUT)})
 REC.write_text(json.dumps(rec,ensure_ascii=False,indent=2,default=str),encoding='utf-8'); arts.append({'role':'inference_receipt','filename':REC.name,'path':str(REC),'mime_type':'application/json','bytes':REC.stat().st_size,'sha256':sha(REC)})
 manifest={'schema':'AH_FRAMEPACK_ARTIFACT_MANIFEST_V1','artifacts':arts}; MAN.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 cb=callback({'event':'AH_FRAMEPACK_TERMINAL','schema':SCHEMA,'receipt':rec,'manifest':manifest}); print('AH_CALLBACK='+json.dumps(cb),flush=True); print('AH_FRAMEPACK_INFERENCE='+json.dumps(rec,ensure_ascii=False,default=str),flush=True); print('AH_ARTIFACT_MANIFEST='+MAN.read_text(),flush=True); return 0 if ok else 2

def main():
 rec={'schema':SCHEMA,'adapter':'upstream_worker_direct_nf4','started':time.time(),'stage':'startup','prompt':PROMPT,'gpu_before':gpu(),'disk_before':disk(),'steps':{}}
 stop=threading.Event(); hb=threading.Thread(target=heartbeat,args=(rec,stop),daemon=True)
 emit('AH_FRAMEPACK_STARTUP',rec); hb.start()
 try:
  if R.exists(): shutil.rmtree(R)
  clone=run(['git','clone','--depth','1','https://github.com/lllyasviel/FramePack.git',str(R)],300,rec=rec,stage='clone')
  if clone.get('returncode')!=0: return finish(rec,False,'clone_timeout' if clone.get('timeout') else 'clone_failed')
  rec['steps']['commit']=run(['git','-C',str(R),'rev-parse','HEAD'],60,rec=rec,stage='commit')
  install=run([sys.executable,'-m','pip','install','--no-cache-dir','-r',str(R/'requirements.txt'),'bitsandbytes'],1200,rec=rec,stage='install')
  if install.get('returncode')!=0: return finish(rec,False,'dependency_install_timeout' if install.get('timeout') else 'dependency_install_failed')
  # Kaggle's writable volume cannot hold the official >30GB FramePack payload. Purge disposable caches before model fetch.
  for p in [Path('/root/.cache/pip'),Path.home()/'.cache'/'pip']:
   if p.exists(): shutil.rmtree(p,ignore_errors=True)
  adapter=R/'ah_headless_adapter.py'
  adapter.write_text(r'''import os,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent; os.chdir(ROOT); sys.argv=[str(ROOT/'demo_gradio.py')]
src=(ROOT/'demo_gradio.py').read_text(encoding='utf-8'); cut=src.rfind('\nblock.launch(')
if cut < 0: raise RuntimeError('upstream_launch_boundary_not_found')
src=src[:cut]
# Disk-safe serialized 4-bit replacements. Both repos preserve the upstream architectures while avoiding the >30GB BF16 download.
src=src.replace('LlamaModel.from_pretrained("hunyuanvideo-community/HunyuanVideo", subfolder=\'text_encoder\', torch_dtype=torch.float16).cpu()', 'LlamaModel.from_pretrained("furusu/hv_llama_nf4").cpu()')
src=src.replace("HunyuanVideoTransformer3DModelPacked.from_pretrained('lllyasviel/FramePackI2V_HY', torch_dtype=torch.bfloat16).cpu()", "HunyuanVideoTransformer3DModelPacked.from_pretrained('furusu/framepack_transformer_nf4').cpu()")
ns={'__name__':'ah_framepack_upstream','__file__':str(ROOT/'demo_gradio.py')}; exec(compile(src,str(ROOT/'demo_gradio.py'),'exec'),ns,ns)
h,w=360,640; y=np.linspace(0,1,h,dtype=np.float32)[:,None]; x=np.linspace(0,1,w,dtype=np.float32)[None,:]; img=np.zeros((h,w,3),dtype=np.uint8)
img[...,0]=(12+18*y).astype(np.uint8); img[...,1]=(18+25*y).astype(np.uint8); img[...,2]=(28+45*y+8*x).astype(np.uint8); img[250:255,:,:]=110; img[285:292,:,:]=65
prompt=os.environ.get('AH_VIDEO_PROMPT','cinematic rainy railway platform at night, subtle natural motion, locked camera, realistic light reflections, premium music video')
ns['worker'](img,prompt,'',31337,1.0,9,4,1.0,10.0,0.0,6.0,True,20); print('AH_HEADLESS_WORKER_RETURNED=1')
''',encoding='utf-8')
  adapter_result=run([sys.executable,str(adapter)],7200,cwd=str(R),rec=rec,stage='adapter')
  if adapter_result.get('timeout'): return finish(rec,False,'adapter_timeout_7200s')
  if adapter_result.get('returncode')!=0: return finish(rec,False,'adapter_process_failed')
  candidate=find_mp4()
  if not candidate or candidate.stat().st_size<1024: return finish(rec,False,'headless_worker_returned_without_physical_mp4')
  shutil.copy2(candidate,OUT); rec['source_mp4']=str(candidate); rec['stage']='artifact_verified'; emit('AH_FRAMEPACK_ARTIFACT_FOUND',rec,bytes=OUT.stat().st_size,sha256=sha(OUT)); return finish(rec,True,None)
 except BaseException as e:
  rec['exception']={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()[-30000:]}
  try: return finish(rec,False,'unhandled_'+type(e).__name__)
  except Exception as terminal_error:
   print('AH_TERMINAL_CALLBACK_FAILURE='+repr(terminal_error),flush=True); raise
 finally:
  stop.set()

if __name__=='__main__': raise SystemExit(main())
