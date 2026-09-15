#!/usr/bin/env python3
"""Tiny Kaggle bootstrap: fetch the versioned ALONEHUNTER admission probe and run it."""
from __future__ import annotations
import subprocess
import sys
import urllib.request
from pathlib import Path

SOURCE = "https://raw.githubusercontent.com/AloneHunterr/alonehunter-lab2/main/framepack/kaggle/framepack_probe.py"
TARGET = Path("/kaggle/working/framepack_probe.py")

with urllib.request.urlopen(SOURCE, timeout=30) as response:
    TARGET.write_bytes(response.read())

raise SystemExit(subprocess.call([sys.executable, str(TARGET)]))
