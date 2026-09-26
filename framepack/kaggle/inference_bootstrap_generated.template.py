#!/usr/bin/env python3
import hashlib,subprocess,sys,urllib.request
from pathlib import Path
VERIFIER_SHA256="__VERIFIER_SHA256__"
VERIFIER_VERSION="__VERIFIER_VERSION__"
SOURCE_COMMIT="__SOURCE_COMMIT__"
EMBEDDED_VERIFIER=__EMBEDDED_VERIFIER__
def _verifier():
 if not isinstance(EMBEDDED_VERIFIER,str) or not EMBEDDED_VERIFIER.strip(): raise RuntimeError("EMBEDDED_VERIFIER_MISSING")
 if hashlib.sha256(EMBEDDED_VERIFIER.encode()).hexdigest()!=VERIFIER_SHA256: raise RuntimeError("EMBEDDED_VERIFIER_HASH_MISMATCH")
 ns={"__name__":"embedded_control_plane_v1"}
 try: exec(compile(EMBEDDED_VERIFIER,"<embedded_control_plane_v1>","exec"),ns,ns)
 except Exception as e: raise RuntimeError("EMBEDDED_VERIFIER_MALFORMED") from e
 if not callable(ns.get("require_admission")): raise RuntimeError("EMBEDDED_VERIFIER_MALFORMED")
 return ns["require_admission"]
require_admission=_verifier()
require_admission(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION")
WORK=Path(os.environ.get("AH_KAGGLE_WORKING","/kaggle/working"))
WORK.mkdir(parents=True,exist_ok=True)
(WORK/"control_plane_v1.py").write_text(EMBEDDED_VERIFIER)
SOURCE="https://raw.githubusercontent.com/AloneHunterr/alonehunter-lab2/__SOURCE_COMMIT__/framepack/kaggle/framepack_inference.py"
INGRESS="https://drive.usercontent.google.com/download?id=1CaaeDM1aa5WxaGLRp261fphwjsxdCuw6&export=download&confirm=t"
TARGET=WORK/"framepack_inference.py"; IMAGE=WORK/"AH_R020_SHOT001_SOURCE.png"
with urllib.request.urlopen(INGRESS,timeout=120) as r: IMAGE.write_bytes(r.read())
if IMAGE.stat().st_size!=897933: raise RuntimeError("canonical_source_size_mismatch")
with urllib.request.urlopen(SOURCE,timeout=30) as r: src=r.read().decode()
old="h,w=360,640; y=np.linspace(0,1,h,dtype=np.float32)[:,None]; x=np.linspace(0,1,w,dtype=np.float32)[None,:]; img=np.zeros((h,w,3),dtype=np.uint8); img[...,0]=(12+18*y).astype(np.uint8); img[...,1]=(18+25*y).astype(np.uint8); img[...,2]=(28+45*y+8*x).astype(np.uint8); img[250:255,:,:]=110; img[285:292,:,:]=65"
new="from PIL import Image; img=np.array(Image.open('/kaggle/working/AH_R020_SHOT001_SOURCE.png').convert('RGB').resize((640,360)))"
if old not in src: raise RuntimeError("production_source_patch_boundary_not_found")
src=src.replace(old,new)
oldp="cinematic rainy railway platform at night, subtle natural motion, locked camera, realistic light reflections, premium music video"
newp="locked camera; begin near-black and reveal the existing scene only through a slow natural exposure lift; preserve exact source geometry, composition, material texture and spatial relationships; cold gray-green worn plaster and restrained cinematic contrast; subtle physically plausible ambient motion only; no pan, no tilt, no zoom, no camera travel, no reframing, no object invention, no geometry deformation; premium photorealistic music-video image-to-video"
if oldp not in src: raise RuntimeError("production_prompt_patch_boundary_not_found")
src=src.replace(oldp,newp).replace("OUT=W/'AH_FRAMEPACK_SANITY.mp4'","OUT=W/'AH_R020_SHOT001_FRAMEPACK.mp4'")
if "'event':'AH_FRAMEPACK_TERMINAL'" not in src or "'manifest':manifest" not in src: raise RuntimeError("terminal_manifest_contract_not_found")
if "def direct_drive_upload()" not in src or "AH_DRIVE_RESUMABLE_URL" not in src: raise RuntimeError("v9_direct_drive_contract_not_found")
TARGET.write_text(src); raise SystemExit(subprocess.call([sys.executable,str(TARGET)]))
