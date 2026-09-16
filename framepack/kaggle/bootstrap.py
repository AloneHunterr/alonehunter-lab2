#!/usr/bin/env python3
"""ALONEHUNTER FramePack Kaggle dispatcher.

One stable Make/Kaggle control-plane entrypoint. Workload selection is encoded in
Kaggle kernel slug/title so Make does not need executable scenario proliferation.
Environment variable AH_FRAMEPACK_MODE still overrides it when explicitly set.
"""
from __future__ import annotations
import os, subprocess, sys, urllib.request
from pathlib import Path

SCRIPTS={
    'admission':'framepack_probe.py',
    'preflight':'framepack_preflight.py',
    'inference':'framepack_inference.py',
}

def detect_mode() -> str:
    explicit=os.environ.get('AH_FRAMEPACK_MODE','').strip().lower()
    if explicit:
        return explicit
    haystack=' '.join(str(v).lower() for v in os.environ.values() if isinstance(v,str))
    if 'inference' in haystack or 'microproof' in haystack:
        return 'inference'
    if 'preflight' in haystack:
        return 'preflight'
    return 'admission'

MODE=detect_mode()
if MODE not in SCRIPTS:
    raise SystemExit(f'unsupported AH_FRAMEPACK_MODE={MODE!r}; allowed={sorted(SCRIPTS)}')
name=SCRIPTS[MODE]
source=f'https://raw.githubusercontent.com/AloneHunterr/alonehunter-lab2/main/framepack/kaggle/{name}'
target=Path('/kaggle/working')/name
print(f'AH_FRAMEPACK_DISPATCH mode={MODE} source={source}')
with urllib.request.urlopen(source,timeout=30) as response:
    target.write_bytes(response.read())
raise SystemExit(subprocess.call([sys.executable,str(target)]))
