#!/usr/bin/env python3
import urllib.request,subprocess,sys
from pathlib import Path
W=Path('/kaggle/working'); base=W/'framepack_base.py'
base.write_bytes(urllib.request.urlopen('https://raw.githubusercontent.com/AloneHunterr/alonehunter-lab2/main/framepack/kaggle/framepack_inference.py',timeout=30).read())
s=base.read_text()
source_url='https://sdmntprnortheu.oaiusercontent.com/files/00000000-d22c-81f4-8836-ddcd6d8733ab/raw?se=2026-09-17T15%3A19%3A20Z&sp=r&sv=2026-02-06&sr=b&scid=1e8daca7-ec66-5bf7-b57c-2cfb769af46d&skoid=76024c37-11e2-4c92-aa07-7e519fbe2d0f&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2026-09-17T02%3A39%3A06Z&ske=2026-09-18T02%3A39%3A06Z&sks=b&skv=2026-02-06&sig=WDPC3J/LeVgVAvT2yy9QLwbeLyIaUNdUq8D0HsE0ldg%3D'
old="h,w=360,640; y=np.linspace(0,1,h,dtype=np.float32)[:,None]; x=np.linspace(0,1,w,dtype=np.float32)[None,:]; img=np.zeros((h,w,3),dtype=np.uint8); img[...,0]=(12+18*y).astype(np.uint8); img[...,1]=(18+25*y).astype(np.uint8); img[...,2]=(28+45*y+8*x).astype(np.uint8); img[250:255,:,:]=110; img[285:292,:,:]=65"
new="from PIL import Image; import urllib.request; src=ROOT/'AH_R020_SHOT001_SOURCE.png'; urllib.request.urlretrieve('"+source_url+"',src); img=np.array(Image.open(src).convert('RGB').resize((640,360)))"
if old not in s: raise RuntimeError('synthetic_source_boundary_not_found')
s=s.replace(old,new).replace("OUT=W/'AH_FRAMEPACK_SANITY.mp4'","OUT=W/'AH_R020_SHOT001_FRAMEPACK_V1.mp4'")
prompt='locked camera, near-black opening into a subtle exposure reveal, cold gray-green worn plaster, preserve exact source geometry and material texture, no people, no camera travel, no dolly, no pan, no tilt, no zoom, stable texture, restrained cinematic light change only'
s=s.replace("PROMPT=os.environ.get('AH_VIDEO_PROMPT','cinematic rainy railway platform at night, subtle natural motion, locked camera, realistic light reflections, premium music video')","PROMPT='"+prompt+"'")
runner=W/'r020_framepack_exec.py'; runner.write_text(s); raise SystemExit(subprocess.call([sys.executable,str(runner)]))
