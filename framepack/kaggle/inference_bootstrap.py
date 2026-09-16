#!/usr/bin/env python3
"""Stable Kaggle bootstrap for the FramePack inference workload."""
import subprocess,sys,urllib.request
from pathlib import Path
SOURCE='https://raw.githubusercontent.com/AloneHunterr/alonehunter-lab2/main/framepack/kaggle/framepack_inference.py'
TARGET=Path('/kaggle/working/framepack_inference.py')
with urllib.request.urlopen(SOURCE,timeout=30) as r: TARGET.write_bytes(r.read())
raise SystemExit(subprocess.call([sys.executable,str(TARGET)]))
