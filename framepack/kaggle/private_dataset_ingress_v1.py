#!/usr/bin/env python3
"""ALONEHUNTER private Kaggle Dataset ingress V1.

No network calls. No credentials. No signed/public URLs.
Provider mutation is intentionally outside this module and remains admission-gated.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, os, re, shutil
from pathlib import Path
from typing import Any, Mapping

class IngressError(RuntimeError):
    pass

FORBIDDEN_KEY = re.compile(r"(?:^|_)(signed|secret|token|credential|password|api[_-]?key|url)(?:$|_)", re.I)

def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _no_secret_fields(v: Any, path: str="$") -> None:
    if isinstance(v, Mapping):
        for k,x in v.items():
            if FORBIDDEN_KEY.search(str(k)):
                raise IngressError(f"FORBIDDEN_SECRET_OR_URL_FIELD:{path}.{k}")
            _no_secret_fields(x, f"{path}.{k}")
    elif isinstance(v, list):
        for i,x in enumerate(v):
            _no_secret_fields(x, f"{path}[{i}]")

def load_manifest(path: str|Path) -> dict[str,Any]:
    m=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(m,dict): raise IngressError("MANIFEST_OBJECT_REQUIRED")
    _no_secret_fields(m)
    for k in ("task_id","dataset","artifacts"):
        if k not in m: raise IngressError(f"MANIFEST_FIELD_REQUIRED:{k}")
    d=m["dataset"]
    for k in ("owner","slug","title"):
        if not d.get(k): raise IngressError(f"DATASET_FIELD_REQUIRED:{k}")
    if not isinstance(m["artifacts"],list) or not m["artifacts"]:
        raise IngressError("ARTIFACTS_REQUIRED")
    seen=set()
    for a in m["artifacts"]:
        for k in ("candidate_id","filename","bytes","sha256"):
            if k not in a: raise IngressError(f"ARTIFACT_FIELD_REQUIRED:{k}")
        fn=str(a["filename"])
        if Path(fn).name!=fn: raise IngressError(f"ARTIFACT_BASENAME_ONLY:{fn}")
        if fn in seen: raise IngressError(f"DUPLICATE_FILENAME:{fn}")
        seen.add(fn)
        if int(a["bytes"])<0: raise IngressError(f"NEGATIVE_SIZE:{fn}")
        if not re.fullmatch(r"[0-9a-f]{64}",str(a["sha256"]).lower()):
            raise IngressError(f"INVALID_SHA256:{fn}")
    return m

def dataset_ref(m: Mapping[str,Any]) -> str:
    d=m["dataset"]; return f"{d['owner']}/{d['slug']}"

def verify_artifact_dir(m: Mapping[str,Any], root: str|Path) -> list[dict[str,Any]]:
    root=Path(root); out=[]
    for a in m["artifacts"]:
        p=root/a["filename"]
        if not p.is_file(): raise IngressError(f"ARTIFACT_MISSING:{a['filename']}")
        size=p.stat().st_size
        if size!=int(a["bytes"]): raise IngressError(f"SIZE_MISMATCH:{a['filename']}")
        sha=_sha256(p)
        if sha!=str(a["sha256"]).lower(): raise IngressError(f"SHA256_MISMATCH:{a['filename']}")
        out.append({"candidate_id":a["candidate_id"],"filename":a["filename"],"bytes":size,"sha256":sha})
    return out

def build_dataset_metadata(m: Mapping[str,Any]) -> dict[str,Any]:
    _no_secret_fields(m); d=m["dataset"]
    return {
      "title":d["title"],"id":dataset_ref(m),"licenses":[{"name":"other"}],
      "description":f"Private operational input for {m['task_id']}. Exact immutable bytes; not for publication or redistribution.",
      "resources":[{"path":a["filename"],"description":f"{a['candidate_id']} sha256={a['sha256']} bytes={a['bytes']}"} for a in m["artifacts"]]
    }

def build_kernel_metadata(base: Mapping[str,Any], m: Mapping[str,Any]) -> dict[str,Any]:
    out=copy.deepcopy(dict(base)); ref=dataset_ref(m)
    out["dataset_sources"]=list(dict.fromkeys(list(out.get("dataset_sources",[]))+[ref]))
    out["is_private"]=True
    out["enable_internet"]=False
    return out

def stage_private_dataset(m: Mapping[str,Any], source_dir: str|Path, stage_dir: str|Path) -> dict[str,Any]:
    source=Path(source_dir); stage=Path(stage_dir); verify_artifact_dir(m,source)
    stage.mkdir(parents=True,exist_ok=True)
    for a in m["artifacts"]:
        src=source/a["filename"]; dst=stage/a["filename"]
        if dst.exists(): dst.unlink()
        try: os.link(src,dst)
        except OSError: shutil.copy2(src,dst)
    (stage/"dataset-metadata.json").write_text(json.dumps(build_dataset_metadata(m),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {
      "task_id":m["task_id"],"dataset_ref":dataset_ref(m),
      "provider_mutation_executed":False,
      "visibility_contract":"PRIVATE_DEFAULT__NO_PUBLIC_FLAG",
      "credential_transport":"CONTROL_PLANE_ONLY__NOT_SERIALIZED_TO_KERNEL",
      "verified":verify_artifact_dir(m,stage)
    }

def verify_runtime_dataset(m: Mapping[str,Any], kaggle_input_root: str|Path="/kaggle/input") -> dict[str,Any]:
    root=Path(kaggle_input_root)/m["dataset"]["slug"]
    return {"task_id":m["task_id"],"dataset_ref":dataset_ref(m),"runtime_root":str(root),
            "verified":verify_artifact_dir(m,root),"exact_input_gate":"PASS"}

def main() -> int:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("prepare"); a.add_argument("--manifest",required=True); a.add_argument("--source-dir",required=True); a.add_argument("--stage-dir",required=True); a.add_argument("--base-kernel-metadata"); a.add_argument("--kernel-metadata-out")
    v=sub.add_parser("verify-runtime"); v.add_argument("--manifest",required=True); v.add_argument("--kaggle-input-root",default="/kaggle/input")
    x=p.parse_args(); m=load_manifest(x.manifest)
    if x.cmd=="prepare":
        r=stage_private_dataset(m,x.source_dir,x.stage_dir)
        if bool(x.base_kernel_metadata)!=bool(x.kernel_metadata_out): raise IngressError("KERNEL_METADATA_INPUT_OUTPUT_MUST_BE_PAIRED")
        if x.base_kernel_metadata:
            base=json.loads(Path(x.base_kernel_metadata).read_text(encoding="utf-8"))
            Path(x.kernel_metadata_out).write_text(json.dumps(build_kernel_metadata(base,m),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            r["kernel_metadata_out"]=x.kernel_metadata_out
        print(json.dumps(r,ensure_ascii=False,sort_keys=True)); return 0
    print(json.dumps(verify_runtime_dataset(m,x.kaggle_input_root),ensure_ascii=False,sort_keys=True)); return 0

if __name__=="__main__":
    raise SystemExit(main())
