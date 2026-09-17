#!/usr/bin/env python3
"""Stable Kaggle bootstrap for FramePack production inference.
Stages the canonical R020 source from durable Drive ingress before execution.
"""
import subprocess,sys,urllib.request
from pathlib import Path
SOURCE='https://raw.githubusercontent.com/AloneHunterr/alonehunter-lab2/main/framepack/kaggle/framepack_inference.py'
INGRESS='https://drive.usercontent.google.com/download?id=1CaaeDM1aa5WxaGLRp261fphwjsxdCuw6&export=download&confirm=t'
TARGET=Path('/kaggle/working/framepack_inference.py')
IMAGE=Path('/kaggle/working/AH_R020_SHOT001_SOURCE.png')
with urllib.request.urlopen(INGRESS,timeout=120) as r: IMAGE.write_bytes(r.read())
if IMAGE.stat().st_size < 1024: raise RuntimeError('durable_source_ingress_too_small')
with urllib.request.urlopen(SOURCE,timeout=30) as r: src=r.read().decode('utf-8')
old="h,w=360,640; y=np.linspace(0,1,h,dtype=np.float32)[:,None]; x=np.linspace(0,1,w,dtype=np.float32)[None,:]; img=np.zeros((h,w,3),dtype=np.uint8); img[...,0]=(12+18*y).astype(np.uint8); img[...,1]=(18+25*y).astype(np.uint8); img[...,2]=(28+45*y+8*x).astype(np.uint8); img[250:255,:,:]=110; img[285:292,:,:]=65"
new="from PIL import Image; img=np.array(Image.open('/kaggle/working/AH_R020_SHOT001_SOURCE.png').convert('RGB').resize((640,360)))"
if old not in src: raise RuntimeError('production_source_patch_boundary_not_found')
TARGET.write_text(src.replace(old,new),encoding='utf-8')
raise SystemExit(subprocess.call([sys.executable,str(TARGET)]))
