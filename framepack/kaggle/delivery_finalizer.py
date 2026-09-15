#!/usr/bin/env python3
"""Generic ALONEHUNTER Kaggle -> Drive resumable artifact finalizer.

The source kernel is mounted as a Kaggle data source. The caller supplies a
Drive resumable upload URL through AH_DRIVE_UPLOAD_URL. Exact artifact identity
is read from AH_FRAMEPACK_ARTIFACT_MANIFEST.json and verified before upload.
"""
from __future__ import annotations
import glob
import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

MANIFEST_NAME = "AH_FRAMEPACK_ARTIFACT_MANIFEST.json"
ROLE = os.environ.get("AH_ARTIFACT_ROLE", "admission_receipt")
UPLOAD_URL = os.environ["AH_DRIVE_UPLOAD_URL"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

manifest_matches = glob.glob(f"/kaggle/input/**/{MANIFEST_NAME}", recursive=True)
if not manifest_matches:
    raise SystemExit(f"manifest not mounted: {MANIFEST_NAME}")
manifest_path = Path(manifest_matches[0])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
entries = [x for x in manifest.get("artifacts", []) if x.get("role") == ROLE]
if len(entries) != 1:
    raise SystemExit(f"expected one artifact role={ROLE}, got {len(entries)}")
entry = entries[0]
source_matches = glob.glob(f"/kaggle/input/**/{entry['filename']}", recursive=True)
if not source_matches:
    raise SystemExit(f"artifact not mounted: {entry['filename']}")
source = Path(source_matches[0])
actual_bytes = source.stat().st_size
actual_sha256 = sha256_file(source)
assert actual_bytes == int(entry["bytes"]), (actual_bytes, entry["bytes"])
assert actual_sha256 == entry["sha256"], (actual_sha256, entry["sha256"])
body = source.read_bytes()
req = urllib.request.Request(
    UPLOAD_URL,
    data=body,
    method="PUT",
    headers={"Content-Type": entry["mime_type"], "Content-Length": str(actual_bytes)},
)
receipt = {
    "schema": "AH_FRAMEPACK_DIRECT_DRIVE_DELIVERY_RECEIPT_V1",
    "success": False,
    "role": ROLE,
    "source_path": str(source),
    "bytes": actual_bytes,
    "sha256": actual_sha256,
}
try:
    with urllib.request.urlopen(req, timeout=300) as response:
        receipt["upload_status"] = response.status
        receipt["upload_response"] = response.read().decode("utf-8", "replace")[:4000]
    receipt["success"] = receipt["upload_status"] in (200, 201)
except urllib.error.HTTPError as e:
    receipt["upload_status"] = e.code
    receipt["upload_response"] = e.read().decode("utf-8", "replace")[:4000]
    raise
finally:
    Path("/kaggle/working/AH_FRAMEPACK_DIRECT_DRIVE_DELIVERY_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("FINAL_RESULT=" + json.dumps(receipt, ensure_ascii=False))
if not receipt["success"]:
    raise SystemExit(2)
