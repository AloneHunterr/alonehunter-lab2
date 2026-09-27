#!/usr/bin/env python3
"""ALONEHUNTER Audio Intelligence APEX A1/A2 enforcement surface.

Pure validation/reconciliation layer. It performs no provider submission.
"""
from __future__ import annotations
import hashlib, json
from dataclasses import dataclass
from typing import Any

STAGES=("SOURCE_VERIFIED","BOUNDARIES_VERIFIED","PCM_EXTRACTED","APEX_MUSIC","LYRICS_ALIGNMENT","BALANCED","TERMINAL_READBACK")

class GateError(ValueError): pass

def _hex64(v: Any)->bool:
    return isinstance(v,str) and len(v)==64 and all(c in "0123456789abcdef" for c in v.lower())

def _require(cond: bool, msg: str):
    if not cond: raise GateError(msg)

def validate_source_manifest(m: dict)->dict:
    parts=m.get("parts")
    _require(isinstance(parts,list) and parts,"parts_required")
    seen=set()
    for p in parts:
        _require(p.get("source_id") and p["source_id"] not in seen,"unique_source_id_required"); seen.add(p["source_id"])
        _require(int(p.get("bytes",0))>0,"source_bytes_required")
        _require(_hex64(p.get("sha256")),"source_sha256_required")
        _require(float(p.get("duration_s",0))>0,"source_duration_required")
        _require(int(p.get("candidate_count",0))>0,"candidate_count_required")
    return m

def validate_boundaries(source:dict,boundary:dict)->dict:
    validate_source_manifest(source)
    by_id={p["source_id"]:p for p in source["parts"]}
    joins=boundary.get("joins")
    _require(isinstance(joins,list) and joins,"joins_required")
    for j in joins:
        p=by_id.get(j.get("source_id")); _require(p is not None,"join_source_unknown")
        _require(j.get("source_sha256")==p["sha256"],"join_source_sha_mismatch")
        _require(float(j.get("timestamp_s",-1))>0 and float(j["timestamp_s"])<float(p["duration_s"]),"join_timestamp_invalid")
        # Silence/duration may nominate a join, never prove it.
        _require(j.get("evidence_class") not in ("equal_split","duration_only","silence_only","hardcoded"),"unproven_join_forbidden")
        _require(_hex64(j.get("before_frame_sha256")) and _hex64(j.get("after_frame_sha256")),"transition_frame_hashes_required")
        _require(bool(j.get("readback_uri")),"transition_readback_required")
        _require(j.get("player_reset_verified") is True,"player_reset_evidence_required")
    # n candidates require n-1 physically evidenced joins per source part.
    for sid,p in by_id.items():
        n=sum(1 for j in joins if j.get("source_id")==sid)
        _require(n==int(p["candidate_count"])-1,f"join_count_mismatch:{sid}")
    return boundary

def validate_pcm(source:dict,pcm:list)->list:
    expected=sum(int(p["candidate_count"]) for p in source["parts"])
    _require(len(pcm)==expected,"pcm_candidate_count_mismatch")
    for c in pcm:
        _require(int(c.get("bytes",0))>0 and float(c.get("duration_s",0))>0 and _hex64(c.get("sha256")),"pcm_identity_required")
    return pcm

def durable_config(task_id:str,source:dict,lyrics:dict,boundary:dict,model_version:str,formula_version:str)->dict:
    validate_boundaries(source,boundary)
    _require(task_id and model_version and formula_version,"durable_config_identity_required")
    _require(lyrics.get("authority_id") and _hex64(lyrics.get("sha256")),"lyrics_authority_hash_required")
    boundary_sha=hashlib.sha256(json.dumps(boundary,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    source_shas=[p["sha256"] for p in source["parts"]]
    raw="|".join([task_id,*source_shas,lyrics["sha256"],boundary_sha,model_version,formula_version])
    return {"task_id":task_id,"ordered_source_sha256s":source_shas,"lyrics_authority_id":lyrics["authority_id"],"lyrics_sha256":lyrics["sha256"],"boundary_manifest_sha256":boundary_sha,"model_version":model_version,"formula_version":formula_version,"idempotency_key":hashlib.sha256(raw.encode()).hexdigest()}

def reconcile_stage(receipts:list,config:dict)->str:
    """Return first incomplete stage. Fail closed on a receipt bound to another config."""
    key=config["idempotency_key"]; done=set()
    for r in receipts:
        _require(r.get("idempotency_key")==key,"prior_stage_identity_mismatch")
        _require(r.get("stage") in STAGES,"unknown_stage")
        _require(_hex64(r.get("artifact_sha256")),"stage_artifact_hash_required")
        done.add(r["stage"])
    for stage in STAGES:
        if stage not in done:return stage
    return "COMPLETE"
