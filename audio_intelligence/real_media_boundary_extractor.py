#!/usr/bin/env python3
"""Physical real-media boundary extractor for concatenated APEX candidates.

Uses decoded PCM fingerprint discontinuities + local spectral-change confirmation.
Silence is advisory only. No equal split / duration-only / hardcoded boundaries.
"""
from __future__ import annotations
import argparse, hashlib, json, math, subprocess, wave
from array import array
from pathlib import Path

def sh(cmd):
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
 return p.stdout

def probe(path):
 d=json.loads(sh(["ffprobe","-v","error","-show_entries","format=duration,size","-of","json",path]))
 return float(d["format"]["duration"]),int(d["format"]["size"])

def decode(path,out,sr=16000):
 subprocess.run(["ffmpeg","-y","-v","error","-i",path,"-vn","-ac","1","-ar",str(sr),"-c:a","pcm_s16le",out],check=True)

def frames(pcm,sr=16000,win_ms=250):
 a=array("h",Path(pcm).read_bytes()); n=max(1,int(sr*win_ms/1000))
 out=[]
 for i in range(0,len(a)-n+1,n):
  x=a[i:i+n]; mean=sum(x)/len(x); rms=math.sqrt(sum(v*v for v in x)/len(x))
  z=sum(1 for u,v in zip(x,x[1:]) if (u<0)<= (v<0))/max(1,len(x)-1)
  h=hashlib.sha256(x.tobytes()).hexdigest()
  out.append((i/sr,rms,z,h))
 return out

def candidates(fs,min_gap=2.0):
 # robust local discontinuity: relative RMS jump plus ZCR change.
 vals=[]
 for i in range(1,len(fs)):
  _,r0,z0,_=fs[i-1];t,r1,z1,_=fs[i]
  score=abs(math.log((r1+1)/(r0+1)))+4*abs(z1-z0)
  vals.append((score,i,t))
 vals.sort(reverse=True)
 chosen=[]
 for score,i,t in vals:
  if all(abs(t-x[2])>=min_gap for x in chosen):chosen.append((score,i,t))
 return sorted(chosen,key=lambda x:x[2])

def extract(path,count,outdir):
 out=Path(outdir);out.mkdir(parents=True,exist_ok=True); pcm=out/"decoded.wav"
 decode(path,str(pcm)); dur,size=probe(path); fs=frames(pcm)
 need=count-1; cs=candidates(fs)
 if len(cs)<need: raise SystemExit("FAIL_CLOSED: insufficient physical discontinuities")
 # choose strongest N, then chronological
 selected=sorted(sorted(cs,reverse=True)[:need],key=lambda x:x[2])
 joins=[]
 for score,i,t in selected:
  joins.append({"timestamp_s":round(t,3),"evidence_class":"pcm_discontinuity+local_spectral_proxy",
   "score":score,"before_frame_sha256":fs[i-1][3],"after_frame_sha256":fs[i][3],
   "player_reset_verified":False,"readback_uri":None})
 manifest={"source":{"path":path,"bytes":size,"duration_s":dur,"sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest()},
  "candidate_count":count,"joins":joins,"status":"CANDIDATE_BOUNDARIES_REQUIRE_READBACK"}
 (out/"boundary_candidates.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 print(json.dumps(manifest,ensure_ascii=False))
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("media");ap.add_argument("--count",type=int,required=True);ap.add_argument("--out",required=True)
 a=ap.parse_args();extract(a.media,a.count,a.out)
