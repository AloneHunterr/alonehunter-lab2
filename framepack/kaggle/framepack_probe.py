#!/usr/bin/env python3
"""ALONEHUNTER FramePack/Kaggle admission probe.

Produces runtime evidence plus a self-describing artifact manifest so downstream
transport can discover exact bytes/SHA256 dynamically. Existing Wan/VK routes are untouched.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path


def run(cmd: list[str]) -> dict:
    t0 = time.time()
    p = subprocess.run(cmd, text=True, capture_output=True)
    return {
        "cmd": cmd,
        "returncode": p.returncode,
        "stdout": p.stdout[-12000:],
        "stderr": p.stderr[-12000:],
        "seconds": round(time.time() - t0, 3),
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    working = Path("/kaggle/working")
    out = Path(os.environ.get("AH_PROBE_OUT", str(working / "framepack_probe.json")))
    manifest_path = working / "AH_FRAMEPACK_ARTIFACT_MANIFEST.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "AH_FRAMEPACK_KAGGLE_PROBE_V2",
        "python": sys.version,
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "env": {
            "KAGGLE_KERNEL_RUN_TYPE": os.environ.get("KAGGLE_KERNEL_RUN_TYPE"),
            "KAGGLE_URL_BASE": os.environ.get("KAGGLE_URL_BASE"),
        },
        "disk": list(shutil.disk_usage(working)) if working.exists() else None,
        "checks": {},
    }
    if shutil.which("nvidia-smi"):
        report["checks"]["nvidia_smi"] = run([
            "nvidia-smi",
            "--query-gpu=index,name,memory.total,memory.free,driver_version",
            "--format=csv,noheader,nounits",
        ])
        report["checks"]["topology"] = run(["nvidia-smi", "topo", "-m"])
    else:
        report["checks"]["nvidia_smi"] = {"returncode": 127, "stderr": "nvidia-smi missing"}
    report["checks"]["git"] = run(["git", "--version"]) if shutil.which("git") else {"returncode": 127}
    report["checks"]["ffmpeg"] = run(["ffmpeg", "-version"]) if shutil.which("ffmpeg") else {"returncode": 127}
    try:
        import torch
        report["torch"] = {
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_version": torch.version.cuda,
            "device_count": torch.cuda.device_count(),
            "devices": [{
                "index": i,
                "name": torch.cuda.get_device_name(i),
                "total_memory": torch.cuda.get_device_properties(i).total_memory,
                "capability": torch.cuda.get_device_capability(i),
            } for i in range(torch.cuda.device_count())],
        }
    except Exception as e:
        report["torch"] = {"error": repr(e)}

    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    manifest = {
        "schema": "AH_FRAMEPACK_ARTIFACT_MANIFEST_V1",
        "artifacts": [{
            "role": "admission_receipt",
            "filename": out.name,
            "path": str(out),
            "mime_type": "application/json",
            "bytes": out.stat().st_size,
            "sha256": sha256_file(out),
        }],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("AH_FRAMEPACK_PROBE=" + json.dumps(report, ensure_ascii=False, default=str))
    print("AH_ARTIFACT_MANIFEST=" + json.dumps(manifest, ensure_ascii=False))
    print(f"AH_PROBE_RECEIPT={out}")
    print(f"AH_MANIFEST_RECEIPT={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
