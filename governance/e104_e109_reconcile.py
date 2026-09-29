"""E104-E109 additive shadow reconciliation helpers. No SYSTEM STATE writes."""
from dataclasses import dataclass

class ReconcileError(ValueError): pass

def _req(c,m):
    if not c: raise ReconcileError(m)

def receiver_pass_correction(current:dict, receipt:dict)->dict|None:
    """S1 shadow-first: emit a proposed append-only correction, never mutate history."""
    _req(receipt.get("receiver") in ("Visual Studio V4","Producer HQ V4"),"authoritative_receiver_required")
    _req(receipt.get("verdict") in ("VISUAL_QA_PASS","HQ_QA_PASS"),"receiver_pass_required")
    for k in ("task_id","artifact_id","artifact_sha256"):
        _req(receipt.get(k),f"{k}_required")
        _req(current.get(k)==receipt.get(k),f"{k}_mismatch")
    if receipt["verdict"]=="VISUAL_QA_PASS":
        # Visual PASS alone must not terminal-close an HQ-gated shot.
        return None
    if current.get("status")=="TERMINAL__HQ_QA_PASS": return None
    return {"mode":"APPEND_ONLY_CORRECTION","task_id":current["task_id"],"artifact_id":current["artifact_id"],"artifact_sha256":current["artifact_sha256"],"supersedes_status":current.get("status"),"new_status":"TERMINAL__HQ_QA_PASS","receipt_id":receipt.get("receipt_id")}

def resolve_receiver_by_resource_key(resource_key:str, registry:list[dict])->dict:
    """I1: canonical RESOURCE_KEY is identity; similar prose names cannot choose executor."""
    matches=[r for r in registry if r.get("resource_key")==resource_key and r.get("status")=="CANONICAL_ACTIVE"]
    _req(len(matches)==1,"resource_key_ambiguous_or_missing")
    _req(matches[0].get("role_name"),"canonical_role_name_required")
    return matches[0]
