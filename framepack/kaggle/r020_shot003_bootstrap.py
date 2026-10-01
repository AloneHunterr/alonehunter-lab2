#!/usr/bin/env python3
"""R020 SHOT003 bounded bootstrap. Exact Reference B; no camera-motion substitute."""
import hashlib,os,subprocess,sys,urllib.request
from pathlib import Path
TASK='AH_VIDEO_STABILIZATION_V1_V2_20260927__R020_SHOT003'
SOURCE_ID='18JjpKKLZgOorflYEp06GuFFen61eIs2K'
SOURCE_BYTES=463048
SOURCE_SHA256='17ac9f5d4ef6aca950a9587cbd49b7db1e2a0dc67f6e6f05e0146a67aea1e2c1'
PROMPT=('static medium shot through the existing doorway; preserve the exact old-apartment geometry, peeling wall, radiator, doorframe axis and copper-pipe topology from the source; hero remains alone with closed posture and anonymous partial identity; one restrained dismissive half-gesture begins and stops, subtle shoulder and forearm motion only; locked camera; no pan, no tilt, no zoom, no dolly, no reframing; no new objects, no pipe morphing, no architecture drift, no melodrama, no horror, photorealistic')
W=Path('/kaggle/working'); src=W/'R020_REFERENCE_B.jpg'
with urllib.request.urlopen(f'https://drive.usercontent.google.com/download?id={SOURCE_ID}&export=download&confirm=t',timeout=120) as r: src.write_bytes(r.read())
if src.stat().st_size!=SOURCE_BYTES: raise RuntimeError('source_bytes_mismatch')
h=hashlib.sha256(src.read_bytes()).hexdigest()
if h!=SOURCE_SHA256: raise RuntimeError('source_sha256_mismatch')
os.environ.update(AH_VIDEO_TASK_ID=TASK,AH_VIDEO_SOURCE_ID=SOURCE_ID,AH_VIDEO_SOURCE_SHA256=h,AH_VIDEO_SOURCE_PATH=str(src),AH_VIDEO_PROMPT=PROMPT,AH_VIDEO_OUTPUT='AH_R020_SHOT003_FRAMEPACK.mp4',AH_FRAMEPACK_RECEIPT_URL='https://hook.us2.make.com/z9tbdjw64o61sn2xmu5281fi0fmafcto')
raise SystemExit(subprocess.call([sys.executable,'framepack/kaggle/framepack_inference.py']))
