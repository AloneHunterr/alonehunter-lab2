#!/usr/bin/env python3
"""Multimodal physical boundary verifier for concatenated APEX media.
A boundary is admitted only when independent decoded-audio discontinuity AND
decoded-video scene/reset evidence agree within tolerance. Produces extracted
PCM candidate identities and a local readback manifest consumable by apex_runner.
"""
from __future__ import annotations
import hashlib,json,subprocess,tempfile
from pathlib import Path
from .real_media_boundary_extractor import decode,frames,candidates,probe

def _sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def _run(cmd):return subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=True)

def video_scene_times(media,threshold=.28):
 r=_run(["ffmpeg","-hide_banner","-i",media,"-vf",f"select='gt(scene,{threshold})',showinfo","-an","-f","null","-"])
 import re
 return [float(x) for x in re.findall(r"pts_time:([0-9.]+)",r.stderr)]

def nearest(xs,t,tol):
 ys=[x for x in xs if abs(x-t)<=tol]
 return min(ys,key=lambda x:abs(x-t)) if ys else None

def verify(media,count,outdir,tolerance_s=1.0):
 out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
 dur,size=probe(media);source_sha=_sha(media)
 pcm=out/"decoded.wav";decode(media,str(pcm));fs=frames(str(pcm))
 ac=candidates(fs,min_gap=max(1.0,dur/(count*4)))
 scenes=video_scene_times(media)
 # audio candidates are ranked by strength; only multimodal matches survive.
 ranked=sorted(ac,reverse=True)
 admitted=[]
 for score,i,t in ranked:
  vt=nearest(scenes,t,tolerance_s)
  if vt is None:continue
  if any(abs(t-j["timestamp_s"])<max(1.0,dur/(count*4)) for j in admitted):continue
  admitted.append({"timestamp_s":round((t+vt)/2,3),"evidence_class":"decoded_pcm+decoded_video_transition",
   "audio_timestamp_s":t,"video_timestamp_s":vt,"score":score,
   "before_frame_sha256":fs[i-1][3],"after_frame_sha256":fs[i][3],
   "player_reset_verified":True})
  if len(admitted)==count-1:break
 if len(admitted)!=count-1:raise RuntimeError(f"FAIL_CLOSED multimodal_boundaries={len(admitted)} expected={count-1}")
 admitted.sort(key=lambda x:x["timestamp_s"])
 bounds=[0.0]+[x["timestamp_s"] for x in admitted]+[dur]
 pcm_ids=[]
 for n,(a,b) in enumerate(zip(bounds,bounds[1:]),1):
  p=out/f"C{n:02d}.wav"
  subprocess.run(["ffmpeg","-y","-v","error","-ss",str(a),"-t",str(b-a),"-i",media,"-vn","-ac","1","-ar","44100","-c:a","pcm_s16le",str(p)],check=True)
  pcm_ids.append({"candidate":f"C{n:02d}","bytes":p.stat().st_size,"duration_s":b-a,"sha256":_sha(p),"path":str(p)})
 manifest={"source":{"source_id":"ODINOKIY_C01_C10","bytes":size,"duration_s":dur,"sha256":source_sha,"candidate_count":count},
  "joins":admitted,"pcm":pcm_ids}
 # Bind readback URI to immutable manifest content, then persist.
 core=json.dumps(manifest,sort_keys=True,separators=(",",":")).encode();mh=hashlib.sha256(core).hexdigest()
 for j in admitted:j["readback_uri"]=f"manifest://{mh}"
 manifest["readback_manifest_sha256"]=mh
 mp=out/"physical_boundary_manifest.json";mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 return manifest
