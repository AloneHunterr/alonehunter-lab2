#!/usr/bin/env python3
"""ALONEHUNTER Video Factory — FramePack physical MP4 sanity inference.

Runs the official FramePack demo in its own subprocess after cloning/installing the
pinned upstream requirements. It deliberately targets a short sanity render first.
Success is ONLY a physical MP4 plus telemetry and a hash-bound artifact manifest.
"""
from __future__ import annotations
import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path

W=Path('/kaggle/working'); R=W/'FramePack'; OUT=W/'AH_FRAMEPACK_SANITY.mp4'
REC=W/'AH_FRAMEPACK_INFERENCE_RECEIPT.json'; MAN=W/'AH_FRAMEPACK_ARTIFACT_MANIFEST.json'
PROMPT=os.environ.get('AH_VIDEO_PROMPT','cinematic rainy railway platform at night, subtle natural motion, locked camera, realistic light reflections, premium music video')

def run(cmd,timeout=3600,cwd=None):
 t=time.time(); p=subprocess.run(cmd,text=True,capture_output=True,timeout=timeout,cwd=cwd)
 return {'cmd':cmd,'returncode':p.returncode,'seconds':round(time.time()-t,3),'stdout':p.stdout[-24000:],'stderr':p.stderr[-24000:]}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''): h.update(c)
 return h.hexdigest()
def gpu(): return run(['nvidia-smi','--query-gpu=index,name,memory.total,memory.used,memory.free','--format=csv,noheader,nounits'],60)
def find_mp4():
 xs=sorted(W.rglob('*.mp4'),key=lambda p:p.stat().st_mtime,reverse=True)
 return xs[0] if xs else None

def main():
 rec={'schema':'AH_FRAMEPACK_INFERENCE_V1','started':time.time(),'prompt':PROMPT,'gpu_before':gpu(),'disk_before':shutil.disk_usage(W)._asdict(),'steps':{}}
 if R.exists(): shutil.rmtree(R)
 rec['steps']['clone']=run(['git','clone','--depth','1','https://github.com/lllyasviel/FramePack.git',str(R)],300)
 if rec['steps']['clone']['returncode']!=0: return finish(rec,False,'clone_failed')
 rec['steps']['commit']=run(['git','-C',str(R),'rev-parse','HEAD'],60)
 rec['steps']['install']=run([sys.executable,'-m','pip','install','-r',str(R/'requirements.txt')],1200)
 if rec['steps']['install']['returncode']!=0: return finish(rec,False,'dependency_install_failed')
 # Official CLI surface is discovered from the checked-out commit rather than guessed.
 rec['steps']['help']=run([sys.executable,str(R/'demo_gradio.py'),'--help'],180,cwd=str(R))
 # FramePack upstream is Gradio-first. If a stable CLI is exposed, use it; otherwise
 # emit exact evidence for the next adapter revision instead of fabricating success.
 helptext=(rec['steps']['help']['stdout']+'\n'+rec['steps']['help']['stderr']).lower()
 if '--prompt' not in helptext:
  return finish(rec,False,'official_upstream_has_no_supported_headless_cli_in_this_commit')
 cmd=[sys.executable,str(R/'demo_gradio.py'),'--prompt',PROMPT,'--output',str(OUT)]
 rec['steps']['inference']=run(cmd,7200,cwd=str(R))
 candidate=OUT if OUT.exists() else find_mp4()
 if not candidate or candidate.stat().st_size<1024: return finish(rec,False,'no_physical_mp4')
 if candidate!=OUT: shutil.copy2(candidate,OUT)
 return finish(rec,True,None)

def finish(rec,ok,reason):
 rec['pass']=ok; rec['failure_reason']=reason; rec['gpu_after']=gpu(); rec['disk_after']=shutil.disk_usage(W)._asdict(); rec['finished']=time.time(); rec['elapsed_s']=round(rec['finished']-rec['started'],3)
 arts=[]
 if OUT.exists(): arts.append({'role':'video','filename':OUT.name,'path':str(OUT),'mime_type':'video/mp4','bytes':OUT.stat().st_size,'sha256':sha(OUT)})
 REC.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8')
 arts.append({'role':'inference_receipt','filename':REC.name,'path':str(REC),'mime_type':'application/json','bytes':REC.stat().st_size,'sha256':sha(REC)})
 MAN.write_text(json.dumps({'schema':'AH_FRAMEPACK_ARTIFACT_MANIFEST_V1','artifacts':arts},ensure_ascii=False,indent=2),encoding='utf-8')
 print('AH_FRAMEPACK_INFERENCE='+json.dumps(rec,ensure_ascii=False)); print('AH_ARTIFACT_MANIFEST='+MAN.read_text())
 return 0 if ok else 2
if __name__=='__main__': raise SystemExit(main())
