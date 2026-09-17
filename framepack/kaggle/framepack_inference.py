#!/usr/bin/env python3
"""ALONEHUNTER Video Factory — FramePack headless physical MP4 microproof.
V8: NF4 route + quantized recast guards + projection FP16 compute alignment + durable telemetry.
"""
from __future__ import annotations
import hashlib,json,os,shutil,subprocess,sys,time,traceback,urllib.request,threading
from pathlib import Path
W=Path('/kaggle/working'); R=W/'FramePack'; OUT=W/'AH_FRAMEPACK_SANITY.mp4'; REC=W/'AH_FRAMEPACK_INFERENCE_RECEIPT.json'; MAN=W/'AH_FRAMEPACK_ARTIFACT_MANIFEST.json'
PROMPT=os.environ.get('AH_VIDEO_PROMPT','cinematic rainy railway platform at night, subtle natural motion, locked camera, realistic light reflections, premium music video')
CALLBACK='https://hook.us2.make.com/z9tbdjw64o61sn2xmu5281fi0fmafcto'; SCHEMA='AH_FRAMEPACK_INFERENCE_V8_NF4_FP16_COMPUTE'; HEARTBEAT_S=60

def callback(payload):
 try:
  b=json.dumps(payload,ensure_ascii=False,default=str).encode(); req=urllib.request.Request(CALLBACK,data=b,headers={'Content-Type':'application/json'},method='POST')
  with urllib.request.urlopen(req,timeout=20) as r:return {'status':r.status,'body':r.read(1000).decode(errors='replace')}
 except Exception as e:return {'error':repr(e)}
def gpu():
 try:
  p=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,memory.free','--format=csv,noheader,nounits'],text=True,capture_output=True,timeout=30); return {'returncode':p.returncode,'stdout':p.stdout[-8000:],'stderr':p.stderr[-8000:]}
 except Exception as e:return {'error':repr(e)}
def disk():
 d=shutil.disk_usage(W); return {'total':d.total,'used':d.used,'free':d.free,'free_gib':round(d.free/1024**3,3)}
def emit(event,rec,**extra):
 payload={'event':event,'schema':SCHEMA,'ts':time.time(),'stage':rec.get('stage'),'elapsed_s':round(time.time()-rec['started'],3),'gpu':gpu(),'disk':disk(),**extra}; result=callback(payload); print('AH_TELEMETRY='+json.dumps({'payload':payload,'callback':result},ensure_ascii=False,default=str),flush=True); return result
def run(cmd,timeout=3600,cwd=None,rec=None,stage=None):
 if rec is not None and stage:rec['stage']=stage; emit('AH_FRAMEPACK_STAGE_START',rec,command=cmd)
 t=time.time()
 try:p=subprocess.run(cmd,text=True,capture_output=True,timeout=timeout,cwd=cwd); out={'cmd':cmd,'returncode':p.returncode,'seconds':round(time.time()-t,3),'stdout':p.stdout[-24000:],'stderr':p.stderr[-24000:]}
 except subprocess.TimeoutExpired as e:out={'cmd':cmd,'returncode':None,'timeout':True,'seconds':round(time.time()-t,3),'stdout':repr(e.stdout),'stderr':repr(e.stderr)}
 if rec is not None and stage:rec['steps'][stage]=out; emit('AH_FRAMEPACK_STAGE_END',rec,step=out)
 return out
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
def find_mp4():
 xs=sorted((R/'outputs').glob('*.mp4'),key=lambda p:p.stat().st_mtime,reverse=True) if (R/'outputs').exists() else []; return xs[0] if xs else None
def heartbeat(rec,stop):
 while not stop.wait(HEARTBEAT_S):emit('AH_FRAMEPACK_HEARTBEAT',rec)
def finish(rec,ok,reason):
 rec.update(pass_=ok,failure_reason=reason,gpu_after=gpu(),disk_after=disk(),finished=time.time(),stage='terminal'); rec['pass']=rec.pop('pass_'); rec['elapsed_s']=round(rec['finished']-rec['started'],3); arts=[]
 if OUT.exists():arts.append({'role':'video','filename':OUT.name,'path':str(OUT),'mime_type':'video/mp4','bytes':OUT.stat().st_size,'sha256':sha(OUT)})
 REC.write_text(json.dumps(rec,ensure_ascii=False,indent=2,default=str),encoding='utf-8'); arts.append({'role':'inference_receipt','filename':REC.name,'path':str(REC),'mime_type':'application/json','bytes':REC.stat().st_size,'sha256':sha(REC)}); manifest={'schema':'AH_FRAMEPACK_ARTIFACT_MANIFEST_V1','artifacts':arts}; MAN.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8'); cb=callback({'event':'AH_FRAMEPACK_TERMINAL','schema':SCHEMA,'receipt':rec,'manifest':manifest}); print('AH_CALLBACK='+json.dumps(cb),flush=True); return 0 if ok else 2
def main():
 rec={'schema':SCHEMA,'adapter':'upstream_worker_direct_nf4_fp16_compute','started':time.time(),'stage':'startup','prompt':PROMPT,'gpu_before':gpu(),'disk_before':disk(),'steps':{}}; stop=threading.Event(); threading.Thread(target=heartbeat,args=(rec,stop),daemon=True).start(); emit('AH_FRAMEPACK_STARTUP',rec)
 try:
  if R.exists():shutil.rmtree(R)
  if run(['git','clone','--depth','1','https://github.com/lllyasviel/FramePack.git',str(R)],300,rec=rec,stage='clone').get('returncode')!=0:return finish(rec,False,'clone_failed')
  rec['steps']['commit']=run(['git','-C',str(R),'rev-parse','HEAD'],60,rec=rec,stage='commit')
  if run([sys.executable,'-m','pip','install','--no-cache-dir','-r',str(R/'requirements.txt'),'bitsandbytes'],1200,rec=rec,stage='install').get('returncode')!=0:return finish(rec,False,'dependency_install_failed')
  adapter=R/'ah_headless_adapter.py'; adapter.write_text(r'''import os,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent; os.chdir(ROOT); sys.argv=[str(ROOT/'demo_gradio.py')]
src=(ROOT/'demo_gradio.py').read_text(encoding='utf-8'); cut=src.rfind('\nblock.launch(')
if cut<0: raise RuntimeError('upstream_launch_boundary_not_found')
src=src[:cut]
src=src.replace('LlamaModel.from_pretrained("hunyuanvideo-community/HunyuanVideo", subfolder=\'text_encoder\', torch_dtype=torch.float16).cpu()', 'LlamaModel.from_pretrained("furusu/hv_llama_nf4").cpu()')
src=src.replace("HunyuanVideoTransformer3DModelPacked.from_pretrained('lllyasviel/FramePackI2V_HY', torch_dtype=torch.bfloat16).cpu()", "HunyuanVideoTransformer3DModelPacked.from_pretrained('furusu/framepack_transformer_nf4').cpu()")
src=src.replace('transformer.to(dtype=torch.bfloat16)', "transformer.to(dtype=torch.bfloat16) if getattr(transformer, 'quantization_method', None) is None else transformer")
src=src.replace('text_encoder.to(dtype=torch.float16)', "text_encoder.to(dtype=torch.float16) if getattr(text_encoder, 'quantization_method', None) is None else text_encoder")
# NF4 checkpoints carry FP16 projection biases. Keep sampler tensors FP16 so Conv3d/Linear inputs match their FP16 biases.
src=src.replace('dtype=torch.bfloat16, device=transformer.device', 'dtype=torch.float16, device=transformer.device')
src=src.replace('dtype=torch.bfloat16, device=device', 'dtype=torch.float16, device=device')
ns={'__name__':'ah_framepack_upstream','__file__':str(ROOT/'demo_gradio.py')}; exec(compile(src,str(ROOT/'demo_gradio.py'),'exec'),ns,ns)
h,w=360,640; y=np.linspace(0,1,h,dtype=np.float32)[:,None]; x=np.linspace(0,1,w,dtype=np.float32)[None,:]; img=np.zeros((h,w,3),dtype=np.uint8); img[...,0]=(12+18*y).astype(np.uint8); img[...,1]=(18+25*y).astype(np.uint8); img[...,2]=(28+45*y+8*x).astype(np.uint8); img[250:255,:,:]=110; img[285:292,:,:]=65
ns['worker'](img,os.environ.get('AH_VIDEO_PROMPT','cinematic rainy railway platform at night, subtle natural motion, locked camera, realistic light reflections, premium music video'),'',31337,1.0,9,4,1.0,10.0,0.0,6.0,True,20); print('AH_HEADLESS_WORKER_RETURNED=1')
''',encoding='utf-8')
  a=run([sys.executable,str(adapter)],7200,cwd=str(R),rec=rec,stage='adapter')
  if a.get('timeout'):return finish(rec,False,'adapter_timeout_7200s')
  if a.get('returncode')!=0:return finish(rec,False,'adapter_process_failed')
  c=find_mp4()
  if not c or c.stat().st_size<1024:return finish(rec,False,'headless_worker_returned_without_physical_mp4')
  shutil.copy2(c,OUT); emit('AH_FRAMEPACK_ARTIFACT_FOUND',rec,bytes=OUT.stat().st_size,sha256=sha(OUT)); return finish(rec,True,None)
 except BaseException as e:rec['exception']={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()[-30000:]}; return finish(rec,False,'unhandled_'+type(e).__name__)
 finally:stop.set()
if __name__=='__main__':raise SystemExit(main())
