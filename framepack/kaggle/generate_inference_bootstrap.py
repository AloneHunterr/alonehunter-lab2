#!/usr/bin/env python3
import hashlib,pathlib,re,subprocess
H=pathlib.Path(__file__).resolve().parent
v=(H/"control_plane_v1.py").read_text(); t=(H/"inference_bootstrap_generated.template.py").read_text()
sha=hashlib.sha256(v.encode()).hexdigest(); m=re.search(r'^CONTROL_PLANE_VERSION = "([^"]+)"',v,re.M)
if not m: raise SystemExit("CONTROL_PLANE_VERSION missing")
commit=subprocess.check_output(["git","log","-1","--format=%H","--","framepack/kaggle/control_plane_v1.py","framepack/kaggle/framepack_inference.py"],text=True).strip()
if not re.fullmatch(r"[0-9a-f]{40}",commit): raise SystemExit("source commit invalid")
o=t.replace("__VERIFIER_SHA256__",sha).replace("__VERIFIER_VERSION__",m.group(1)).replace("__SOURCE_COMMIT__",commit).replace("__EMBEDDED_VERIFIER__",repr(v))
(H/"inference_bootstrap_generated.py").write_text(o); print(sha,m.group(1),commit)

# generation trigger
