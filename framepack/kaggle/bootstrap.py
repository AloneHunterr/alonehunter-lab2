#!/usr/bin/env python3
"""ALONEHUNTER FramePack Kaggle dispatcher.

One stable Make/Kaggle control-plane entrypoint. Select workload by AH_FRAMEPACK_MODE
(default: admission). This prevents scenario proliferation while keeping every
workload versioned in GitHub.
"""
from __future__ import annotations
import os, subprocess, sys, urllib.request
from pathlib import Path

MODE=os.environ.get('AH_FRAMEPACK_MODE','admission').strip().lower()
SCRIPTS={
    'admission':'framepack_probe.py',
    'preflight':'framepack_preflight.py',
}
if MODE not in SCRIPTS:
    raise SystemExit(f'unsupported AH_FRAMEPACK_MODE={MODE!r}; allowed={sorted(SCRIPTS)}')
name=SCRIPTS[MODE]
source=f'https://raw.githubusercontent.com/AloneHunterr/alonehunter-lab2/main/framepack/kaggle/{name}'
target=Path('/kaggle/working')/name
print(f'AH_FRAMEPACK_DISPATCH mode={MODE} source={source}')
with urllib.request.urlopen(source,timeout=30) as response:
    target.write_bytes(response.read())
raise SystemExit(subprocess.call([sys.executable,str(target)]))
