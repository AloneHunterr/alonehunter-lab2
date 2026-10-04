#!/usr/bin/env python3
"""Generate the additive Replay V2 bootstrap without touching V1 artifacts."""
import hashlib, pathlib, subprocess

H=pathlib.Path(__file__).resolve().parent
consumer=(H/"control_plane_v2.py").read_text(encoding="utf-8")
runtime=(H/"framepack_inference_v2_microproof.py").read_text(encoding="utf-8")
template=(H/"inference_bootstrap_v2_generated.template.py").read_text(encoding="utf-8")

def blob_sha(text:str)->str:
    b=text.encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

commit=subprocess.check_output([
    "git","log","-1","--format=%H","--",
    str(H/"control_plane_v2.py"),
    str(H/"framepack_inference_v2_microproof.py"),
],text=True).strip()
if len(commit)!=40 or any(c not in "0123456789abcdef" for c in commit):
    raise SystemExit("V2_SOURCE_COMMIT_INVALID")

out=(template
    .replace("__CONSUMER_BLOB_SHA__",blob_sha(consumer))
    .replace("__RUNTIME_BLOB_SHA__",blob_sha(runtime))
    .replace("__SOURCE_COMMIT__",commit)
    .replace("__EMBEDDED_CONSUMER__",repr(consumer))
)
(H/"inference_bootstrap_v2_generated.py").write_text(out,encoding="utf-8")
print(blob_sha(consumer),blob_sha(runtime),commit)
