#!/usr/bin/env python3
"""Generated additive Replay V2 bootstrap. Non-production only."""
import hashlib, os, subprocess, sys, urllib.request
from pathlib import Path

CONSUMER_GIT_BLOB_SHA="__CONSUMER_BLOB_SHA__"
RUNTIME_GIT_BLOB_SHA="__RUNTIME_BLOB_SHA__"
VERIFIER_VERSION="EXECUTION_CONTROL_PLANE_V2"
SOURCE_COMMIT="__SOURCE_COMMIT__"
EMBEDDED_CONSUMER=__EMBEDDED_CONSUMER__

def git_blob_sha(text:str)->str:
    b=text.encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

if VERIFIER_VERSION!="EXECUTION_CONTROL_PLANE_V2":
    raise RuntimeError("V2_VERIFIER_VERSION_REQUIRED")
if git_blob_sha(EMBEDDED_CONSUMER)!=CONSUMER_GIT_BLOB_SHA:
    raise RuntimeError("EMBEDDED_V2_CONSUMER_HASH_MISMATCH")
if "EXECUTION_CONTROL_PLANE_V1" in EMBEDDED_CONSUMER:
    raise RuntimeError("V1_CONSUMER_FORBIDDEN")

WORK=Path(os.environ.get("AH_KAGGLE_WORKING","/kaggle/working"))
WORK.mkdir(parents=True,exist_ok=True)
(WORK/"control_plane_v2.py").write_text(EMBEDDED_CONSUMER,encoding="utf-8")

runtime_url=(
    "https://raw.githubusercontent.com/AloneHunterr/alonehunter-lab2/"
    +SOURCE_COMMIT+
    "/framepack/kaggle/framepack_inference_v2_microproof.py"
)
with urllib.request.urlopen(runtime_url,timeout=30) as response:
    runtime=response.read().decode("utf-8")
if git_blob_sha(runtime)!=RUNTIME_GIT_BLOB_SHA:
    raise RuntimeError("V2_RUNTIME_HASH_MISMATCH")
if "framepack_inference.py" in runtime and "framepack_inference_v2_microproof.py" not in runtime:
    raise RuntimeError("PRODUCTION_RUNTIME_ALIAS_FORBIDDEN")
target=WORK/"framepack_inference_v2_microproof.py"
target.write_text(runtime,encoding="utf-8")
raise SystemExit(subprocess.call([sys.executable,str(target)]))
