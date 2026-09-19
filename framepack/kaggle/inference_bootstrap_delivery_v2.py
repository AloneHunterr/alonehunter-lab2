#!/usr/bin/env python3
"""R020 SHOT001 FramePack production bootstrap with low-data terminal artifact contract.
Uses proven V9 runtime and durable Drive ingress. Terminal callback carries manifest-bound
artifact metadata only; MP4 bytes bypass Make via the V9 direct Drive resumable upload
or the separate delivery_finalizer.py fallback.
"""
import subprocess,sys,urllib.request
from pathlib import Path

SOURCE='https://raw.githubusercontent.com/AloneHunterr/alonehunter-lab2/main/framepack/kaggle/framepack_inference.py'
INGRESS='https://drive.usercontent.google.com/download?id=1CaaeDM1aa5WxaGLRp261fphwjsxdCuw6&export=download&confirm=t'
TARGET=Path('/kaggle/working/framepack_inference.py')
IMAGE=Path('/kaggle/working/AH_R020_SHOT001_SOURCE.png')

with urllib.request.urlopen(INGRESS,timeout=120) as r:
    IMAGE.write_bytes(r.read())
if IMAGE.stat().st_size != 897933:
    raise RuntimeError(f'canonical_source_size_mismatch:{IMAGE.stat().st_size}')

with urllib.request.urlopen(SOURCE,timeout=30) as r:
    src=r.read().decode('utf-8')

old_img="h,w=360,640; y=np.linspace(0,1,h,dtype=np.float32)[:,None]; x=np.linspace(0,1,w,dtype=np.float32)[None,:]; img=np.zeros((h,w,3),dtype=np.uint8); img[...,0]=(12+18*y).astype(np.uint8); img[...,1]=(18+25*y).astype(np.uint8); img[...,2]=(28+45*y+8*x).astype(np.uint8); img[250:255,:,:]=110; img[285:292,:,:]=65"
new_img="from PIL import Image; img=np.array(Image.open('/kaggle/working/AH_R020_SHOT001_SOURCE.png').convert('RGB').resize((640,360)))"
if old_img not in src:
    raise RuntimeError('production_source_patch_boundary_not_found')
src=src.replace(old_img,new_img)

old_prompt="cinematic rainy railway platform at night, subtle natural motion, locked camera, realistic light reflections, premium music video"
new_prompt="locked camera; begin near-black and reveal the existing scene only through a slow natural exposure lift; preserve exact source geometry, composition, material texture and spatial relationships; cold gray-green worn plaster and restrained cinematic contrast; subtle physically plausible ambient motion only; no pan, no tilt, no zoom, no camera travel, no reframing, no object invention, no geometry deformation; premium photorealistic music-video image-to-video"
if old_prompt not in src:
    raise RuntimeError('production_prompt_patch_boundary_not_found')
src=src.replace(old_prompt,new_prompt)
src=src.replace("OUT=W/'AH_FRAMEPACK_SANITY.mp4'","OUT=W/'AH_R020_SHOT001_FRAMEPACK.mp4'")

# LOW_DATA_MODE invariant:
# - never put MP4 bytes/base64 through Make;
# - V9 terminal callback must expose manifest-bound filename/bytes/sha256;
# - binary delivery is direct Kaggle -> Drive via AH_DRIVE_RESUMABLE_URL when supplied,
#   with delivery_finalizer.py as the manifest-verified fallback.
terminal_anchor="'event':'AH_FRAMEPACK_TERMINAL'"
manifest_anchor="'manifest':manifest"
if terminal_anchor not in src or manifest_anchor not in src:
    raise RuntimeError('terminal_manifest_contract_not_found')
if "def direct_drive_upload()" not in src or "AH_DRIVE_RESUMABLE_URL" not in src:
    raise RuntimeError('v9_direct_drive_contract_not_found')

TARGET.write_text(src,encoding='utf-8')
raise SystemExit(subprocess.call([sys.executable,str(TARGET)]))
