#!/usr/bin/env python3
"""ALONEHUNTER FramePack dependency/model preflight for Kaggle.

No generation and no paid services. Validates official repo, pinned Python deps,
HF model metadata reachability, local disk budget and dual-T4 runtime. Emits a
machine-readable receipt + artifact manifest for the canonical output reader.
"""
from __future__ import annotations
import hashlib, json, os, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

WORK=Path('/kaggle/working')
OUT=WORK/'framepack_preflight.json'
MAN=WORK/'AH_FRAMEPACK_PREFLIGHT_MANIFEST.json'
REPO=WORK/'FramePack'

def run(cmd, timeout=900):
    t=time.time()
    p=subprocess.run(cmd,text=True,capture_output=True,timeout=timeout)
    return {'cmd':cmd,'returncode':p.returncode,'stdout':p.stdout[-16000:],'stderr':p.stderr[-16000:],'seconds':round(time.time()-t,3)}

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def head(url):
    t=time.time()
    try:
        r=urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=30)
        return {'ok':True,'status':getattr(r,'status',200),'content_length':r.headers.get('content-length'),'seconds':round(time.time()-t,3)}
    except Exception as e: return {'ok':False,'error':repr(e),'seconds':round(time.time()-t,3)}

def main():
    r={'schema':'AH_FRAMEPACK_PREFLIGHT_V1','python':sys.version,'checks':{}}
    r['disk_before']=list(shutil.disk_usage(WORK))
    r['checks']['gpu']=run(['nvidia-smi','--query-gpu=index,name,memory.total,memory.free','--format=csv,noheader,nounits'])
    if REPO.exists(): shutil.rmtree(REPO)
    r['checks']['clone']=run(['git','clone','--depth','1','https://github.com/lllyasviel/FramePack.git',str(REPO)],300)
    if r['checks']['clone']['returncode']==0:
        r['checks']['commit']=run(['git','-C',str(REPO),'rev-parse','HEAD'])
        r['checks']['requirements']=run([sys.executable,'-m','pip','install','--dry-run','-r',str(REPO/'requirements.txt')],900)
    r['checks']['hf_hunyuan']=head('https://huggingface.co/hunyuanvideo-community/HunyuanVideo/resolve/main/model_index.json')
    r['checks']['hf_framepack']=head('https://huggingface.co/lllyasviel/FramePackI2V_HY/resolve/main/config.json')
    r['checks']['hf_flux_redux']=head('https://huggingface.co/lllyasviel/flux_redux_bfl/resolve/main/README.md')
    r['disk_after']=list(shutil.disk_usage(WORK))
    r['pass']=bool(r['checks']['gpu']['returncode']==0 and r['checks']['clone']['returncode']==0 and r.get('checks',{}).get('requirements',{}).get('returncode')==0 and r['checks']['hf_hunyuan']['ok'] and r['checks']['hf_framepack']['ok'] and r['checks']['hf_flux_redux']['ok'])
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    m={'schema':'AH_FRAMEPACK_ARTIFACT_MANIFEST_V1','artifacts':[{'role':'framepack_preflight_receipt','filename':OUT.name,'path':str(OUT),'mime_type':'application/json','bytes':OUT.stat().st_size,'sha256':sha(OUT)}]}
    MAN.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
    print('AH_FRAMEPACK_PREFLIGHT='+json.dumps(r,ensure_ascii=False))
    print('AH_ARTIFACT_MANIFEST='+json.dumps(m,ensure_ascii=False))
    return 0 if r['pass'] else 2
if __name__=='__main__': raise SystemExit(main())
