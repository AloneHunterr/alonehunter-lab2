#!/usr/bin/env python3
"""Additive non-production Replay V2 caller-binding microproof runtime.

Never replaces production FramePack V1. A target sentinel is reached only after
control_plane_v2 consumes an exact admission and a trusted CLAIMED receipt.
"""
from __future__ import annotations
import json, os
from pathlib import Path
from datetime import datetime
from control_plane_v2 import (
    consume_admission_v2,
    claim_replay_http,
    AdmissionDenied,
    AdmissionUnknown,
)

TASK_ID="AH_EXECUTION_ADMISSION_V2_CALLER_BINDING_MICROPROOF_20261004"
SURFACE="KAGGLE"
OPERATION="R020_FRAMEPACK_EXECUTION"
ROLE="BIG_TECH_TECH_RND"
DEFAULT_SENTINEL=Path(os.environ.get(
    "AH_V2_MICROPROOF_SENTINEL",
    "/kaggle/working/AH_EXECUTION_ADMISSION_V2_CALLER_BINDING_SENTINEL.json",
))

def _default_target(receipt:dict):
    DEFAULT_SENTINEL.parent.mkdir(parents=True,exist_ok=True)
    payload={
        "task_id":TASK_ID,
        "admission_id":receipt["admission_id"],
        "nonce":receipt["admission"]["nonce"],
        "authenticity":receipt["authenticity"],
        "state":"TARGET_SENTINEL_REACHED_ONCE",
    }
    with DEFAULT_SENTINEL.open("x",encoding="utf-8") as f:
        json.dump(payload,f,ensure_ascii=False,sort_keys=True)
    return payload

def run_microproof(*,raw:str|None=None,claim_fn=None,now:datetime|None=None,target_fn=None):
    claim_fn=claim_fn or claim_replay_http
    target_fn=target_fn or _default_target
    verified=consume_admission_v2(
        surface=SURFACE,
        operation=OPERATION,
        task_id=TASK_ID,
        role=ROLE,
        raw=raw,
        claim_fn=claim_fn,
        now=now,
    )
    replay=verified.get("replay_receipt") or {}
    admission=verified.get("admission") or {}
    if verified.get("authenticity")!="TRUSTED_CONTROL_PLANE_CLAIMED":
        raise AdmissionUnknown("TRUSTED_CLAIM_REQUIRED")
    if replay.get("state")!="CLAIMED":
        raise AdmissionUnknown("TRUSTED_CLAIM_STATE_REQUIRED")
    if replay.get("admission_id")!=verified.get("admission_id"):
        raise AdmissionUnknown("TRUSTED_CLAIM_ADMISSION_ID_MISMATCH")
    if replay.get("nonce")!=admission.get("nonce"):
        raise AdmissionUnknown("TRUSTED_CLAIM_NONCE_MISMATCH")
    return target_fn(verified)

def main():
    try:
        out=run_microproof()
        print(json.dumps({"state":"PASS_V2_CALLER_BINDING_MICROPROOF","result":out},sort_keys=True))
        return 0
    except (AdmissionDenied,AdmissionUnknown,FileExistsError) as exc:
        print(json.dumps({"state":"FAIL_CLOSED","error":str(exc)},sort_keys=True))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
