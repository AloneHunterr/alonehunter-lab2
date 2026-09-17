#!/usr/bin/env python3
"""R020 SHOT001 production-bound FramePack bootstrap.
Reuses the physically proven V9 runtime, replacing only the synthetic sanity frame
with the exact Drive-bound R020 source and the locked SHOT001 motion contract.
"""
import os, urllib.request

BASE='https://raw.githubusercontent.com/AloneHunterr/alonehunter-lab2/main/framepack/kaggle/framepack_inference.py'
SOURCE_ID='1q32iMeLG-u0gvxhGcL142Z7-ol4qk2gF'
PROMPT='Locked-off cinematic camera. Preserve the exact input image geometry, architecture, materials and composition. Near-black opening gradually reveals the existing cold gray-green worn plaster and copper-toned details through a subtle natural exposure lift only. No camera travel, no pan, no tilt, no zoom, no dolly, no orbit. No new objects, no people, no fantasy elements, no structural deformation. Stable texture, stable straight lines, physically realistic low-light exposure, restrained micro-motion only, premium photorealistic music-video look.'
with urllib.request.urlopen(BASE, timeout=30) as r:
    src=r.read().decode('utf-8')
old="h,w=360,640; y=np.linspace(0,1,h,dtype=np.float32)[:,None]; x=np.linspace(0,1,w,dtype=np.float32)[None,:]; img=np.zeros((h,w,3),dtype=np.uint8); img[...,0]=(12+18*y).astype(np.uint8); img[...,1]=(18+25*y).astype(np.uint8); img[...,2]=(28+45*y+8*x).astype(np.uint8); img[250:255,:,:]=110; img[285:292,:,:]=65"
new="src_path=ROOT/'AH_R020_LTX_DURATION_BENCHMARK_SOURCE_V1_1024x576.png'; urllib.request.urlretrieve('https://drive.usercontent.google.com/download?id="+SOURCE_ID+"&export=download&confirm=t',src_path); from PIL import Image; img=np.array(Image.open(src_path).convert('RGB'))"
if old not in src:
    raise RuntimeError('proven_v9_synthetic_input_boundary_not_found')
src=src.replace(old,new)
src=src.replace("OUT=W/'AH_FRAMEPACK_SANITY.mp4'","OUT=W/'AH_R020_SHOT001_FRAMEPACK_PROOF.mp4'")
os.environ['AH_VIDEO_PROMPT']=PROMPT
ns={'__name__':'__main__','__file__':'framepack_inference.py'}
exec(compile(src,'framepack_inference.py','exec'),ns,ns)
