#!/usr/bin/env python3
"""Fail-closed direct-byte leg for a private Kaggle dataset ingress.

This module intentionally does NOT contain provider credentials and does NOT
create a Kaggle job. A trusted control plane opens StartBlobUpload sessions
(metadata only). This runtime verifies exact bytes/SHA256, PUTs bytes directly
to each provider createUrl, and returns only blob tokens + immutable identity
for a separate authenticated CreateDataset/Version control call.

Forbidden by contract:
- public Google Drive sharing;
- Supabase signed download URLs;
- binary/media transfer through Make;
- scoring/provider submit before all ten identities pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SCHEMA = "AH_KAGGLE_PRIVATE_BLOB_RECEIPT_V1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    m = json.loads(path.read_text(encoding="utf-8"))
    files = m.get("files")
    if m.get("schema") != "AH_AUDIO_PCM_MANIFEST_V1" or not isinstance(files, list):
        raise ValueError("MANIFEST_SCHEMA_FAIL")
    expected = [f"C{i:02d}" for i in range(1, 11)]
    got = [str(x.get("candidate")) for x in files]
    if got != expected:
        raise ValueError(f"CANDIDATE_ORDER_FAIL:{got}")
    names = [str(x.get("name")) for x in files]
    if len(set(names)) != 10:
        raise ValueError("DUPLICATE_NAME_FAIL")
    return m


def verify_files(root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    verified = []
    for row in manifest["files"]:
        p = root / row["name"]
        if not p.is_file():
            raise FileNotFoundError(f"MISSING:{row['candidate']}:{p}")
        actual_bytes = p.stat().st_size
        if actual_bytes != int(row["bytes"]):
            raise ValueError(f"BYTES_FAIL:{row['candidate']}:{actual_bytes}:{row['bytes']}")
        actual_sha = sha256_file(p)
        if actual_sha != row["sha256"]:
            raise ValueError(f"SHA256_FAIL:{row['candidate']}:{actual_sha}:{row['sha256']}")
        verified.append({
            "candidate": row["candidate"],
            "name": row["name"],
            "bytes": actual_bytes,
            "sha256": actual_sha,
            "path": str(p),
        })
    return verified


def blob_session_requests(verified: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Metadata for the authenticated StartBlobUpload control plane."""
    return [{
        "name": x["name"],
        "contentType": "audio/wav",
        "contentLength": x["bytes"],
        "blobType": "DATASET",
    } for x in verified]


def _validate_create_url(url: str) -> None:
    u = urlparse(url)
    if u.scheme != "https" or not u.netloc or u.username or u.password:
        raise ValueError("UNSAFE_CREATE_URL")


def upload_direct(path: Path, create_url: str, expected_bytes: int, timeout: int = 300) -> int:
    """Upload one exact file directly runtime→provider. No Make byte transit."""
    _validate_create_url(create_url)
    data = path.read_bytes()
    if len(data) != expected_bytes:
        raise ValueError("PREUPLOAD_BYTES_CHANGED")
    req = Request(
        create_url,
        data=data,
        method="PUT",
        headers={
            "Content-Type": "application/octet-stream",
            "Content-Length": str(len(data)),
            "Content-Range": f"bytes 0-{len(data)-1}/{len(data)}",
        },
    )
    with urlopen(req, timeout=timeout) as resp:
        status = int(getattr(resp, "status", 0) or 0)
        if status not in (200, 201):
            raise RuntimeError(f"BLOB_UPLOAD_HTTP_{status}")
        return status


def execute_sessions(
    root: Path,
    manifest_path: Path,
    sessions_path: Path,
    *,
    do_upload: bool,
) -> dict[str, Any]:
    m = load_manifest(manifest_path)
    verified = verify_files(root, m)
    sessions = json.loads(sessions_path.read_text(encoding="utf-8"))
    if set(sessions) != {x["name"] for x in verified}:
        raise ValueError("SESSION_SET_MISMATCH")

    receipts = []
    for x in verified:
        s = sessions[x["name"]]
        token = str(s.get("token") or "")
        create_url = str(s.get("createUrl") or "")
        if not token or not create_url:
            raise ValueError(f"SESSION_INCOMPLETE:{x['name']}")
        _validate_create_url(create_url)
        status = None
        if do_upload:
            status = upload_direct(Path(x["path"]), create_url, x["bytes"])
        receipts.append({
            "candidate": x["candidate"],
            "name": x["name"],
            "bytes": x["bytes"],
            "sha256": x["sha256"],
            "blob_token": token,
            "upload_status": status,
        })

    return {
        "schema": SCHEMA,
        "task_id": m["task_id"],
        "source_manifest_drive_id": m["source_manifest_drive_id"],
        "all_exact_identities_verified": True,
        "provider_upload_executed": bool(do_upload),
        "files": receipts,
        "next_control_action": (
            "Create a PRIVATE Kaggle dataset/version from these blob tokens, "
            "then mount that dataset via kernelDataSources and re-verify the same hashes before APEX."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--sessions", type=Path)
    ap.add_argument("--emit-session-requests", action="store_true")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--out", type=Path)
    ns = ap.parse_args()

    manifest = load_manifest(ns.manifest)
    verified = verify_files(ns.root, manifest)

    if ns.emit_session_requests:
        result: Any = blob_session_requests(verified)
    else:
        if not ns.sessions:
            ap.error("--sessions is required unless --emit-session-requests is used")
        result = execute_sessions(ns.root, ns.manifest, ns.sessions, do_upload=ns.upload)

    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if ns.out:
        ns.out.write_text(encoded + "\n", encoding="utf-8")
    else:
        print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
