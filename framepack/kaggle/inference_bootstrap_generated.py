#!/usr/bin/env python3
import hashlib,os,subprocess,sys,urllib.request
from pathlib import Path
VERIFIER_SHA256="9669ecca9005b80f57e112063ff85c3310257fcec42329d6c9b78caccc710524"
VERIFIER_VERSION="EXECUTION_CONTROL_PLANE_V1"
SOURCE_COMMIT="f15a44f8590e13f2eb8479cfd501dbb3b2221df6"
EMBEDDED_VERIFIER='#!/usr/bin/env python3\n"""Fail-closed Python binding for ALONEHUNTER EXECUTION_CONTROL_PLANE_V1.\n\nThis mirrors the canonical admission-token integrity contract used by\nalonehunter-lab/evolution-engine/src/enforcer/control-plane-interceptor-v1.mjs.\nProduction executors consume a token; they do not mint one.\n"""\nfrom __future__ import annotations\nimport hashlib, json, os\nfrom typing import Any, Mapping\n\nGATEWAY_VERSION = "ROLE_EXECUTION_GATEWAY_V1"\nCONTROL_PLANE_VERSION = "EXECUTION_CONTROL_PLANE_V1"\nROLE = "BIG_TECH_TECH_RND"\nSURFACES = {"MAKE","KAGGLE","PROVIDER","DRIVE","GITHUB","SUPABASE","SOCIAL"}\n\nclass AdmissionDenied(RuntimeError):\n    pass\n\ndef _stable(value: Mapping[str, Any]) -> str:\n    # Match JSON.stringify(payload, Object.keys(payload).sort()) for the flat\n    # canonical admission payload.\n    return json.dumps(dict(sorted(value.items())), separators=(",",":"), ensure_ascii=False)\n\ndef _digest(value: Mapping[str, Any]) -> str:\n    return hashlib.sha256(_stable(value).encode("utf-8")).hexdigest()\n\ndef parse_token(raw: str | None = None, *, surface: str | None = None) -> dict[str, Any]:\n    if raw is None:\n        scoped = f"AH_EXECUTION_ADMISSION_TOKEN_{surface.upper()}" if surface else ""\n        raw = os.environ.get(scoped, "") if scoped else ""\n        raw = raw or os.environ.get("AH_EXECUTION_ADMISSION_TOKEN", "")\n    if not raw:\n        raise AdmissionDenied("ADMISSION_TOKEN_REQUIRED")\n    try:\n        token = json.loads(raw)\n    except Exception as exc:\n        raise AdmissionDenied("ADMISSION_TOKEN_INVALID_JSON") from exc\n    if not isinstance(token, dict) or not isinstance(token.get("admission"), dict) or not token.get("admission_id"):\n        raise AdmissionDenied("ADMISSION_TOKEN_REQUIRED")\n    return token\n\ndef require_admission(*, surface: str, operation: str, role: str = ROLE, raw: str | None = None) -> dict[str, Any]:\n    token = parse_token(raw, surface=surface)\n    admission = token["admission"]\n    expected_surface = surface.upper()\n    if expected_surface not in SURFACES:\n        raise AdmissionDenied("UNKNOWN_MUTATION_SURFACE")\n    if admission.get("gateway_version") != GATEWAY_VERSION:\n        raise AdmissionDenied("ADMISSION_GATEWAY_VERSION_MISMATCH")\n    if admission.get("control_plane_version") != CONTROL_PLANE_VERSION:\n        raise AdmissionDenied("ADMISSION_CONTROL_PLANE_VERSION_MISMATCH")\n    if admission.get("surface") != expected_surface:\n        raise AdmissionDenied("ADMISSION_SURFACE_MISMATCH")\n    if admission.get("operation") != operation:\n        raise AdmissionDenied("ADMISSION_OPERATION_MISMATCH")\n    if admission.get("role") != role:\n        raise AdmissionDenied("ADMISSION_ROLE_MISMATCH")\n    if _digest(admission) != token.get("admission_id"):\n        raise AdmissionDenied("ADMISSION_INTEGRITY_FAILURE")\n    return token\n\ndef require_terminal_admission(*, operation: str, raw: str | None = None) -> dict[str, Any]:\n    return require_admission(surface="PROVIDER", operation=operation, raw=raw)\n'
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
SOURCE="https://raw.githubusercontent.com/AloneHunterr/alonehunter-lab2/f15a44f8590e13f2eb8479cfd501dbb3b2221df6/framepack/kaggle/framepack_inference.py"
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
