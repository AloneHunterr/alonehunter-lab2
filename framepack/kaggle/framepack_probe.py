#!/usr/bin/env python3
"""ALONEHUNTER FramePack/Kaggle admission probe.

Phase 0 only: proves runtime/GPU/storage/network prerequisites before model
installation or generation. It intentionally does not touch existing Wan/VK routes.
"""
from __future__ import annotations

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


def main() -> int:
    out = Path(os.environ.get("AH_PROBE_OUT", "/kaggle/working/framepack_probe.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "AH_FRAMEPACK_KAGGLE_PROBE_V1",
        "python": sys.version,
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "env": {
            "KAGGLE_KERNEL_RUN_TYPE": os.environ.get("KAGGLE_KERNEL_RUN_TYPE"),
            "KAGGLE_URL_BASE": os.environ.get("KAGGLE_URL_BASE"),
        },
        "disk": shutil.disk_usage("/kaggle/working") if Path("/kaggle/working").exists() else None,
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
            "devices": [
                {
                    "index": i,
                    "name": torch.cuda.get_device_name(i),
                    "total_memory": torch.cuda.get_device_properties(i).total_memory,
                    "capability": torch.cuda.get_device_capability(i),
                }
                for i in range(torch.cuda.device_count())
            ],
        }
    except Exception as e:
        report["torch"] = {"error": repr(e)}

    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=list), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, default=list))
    print(f"AH_PROBE_RECEIPT={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
