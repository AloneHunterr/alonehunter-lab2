#!/usr/bin/env python3
"""Additive EXECUTION_CONTROL_PLANE_V2 consumer. V1 remains production-active.

V2B trust boundary: workload code never receives the issuer signing/verifier key.
It performs structural/scope/freshness/integrity checks locally, then requires a
trusted control-plane claim receipt. Issuer authenticity is verified only by the
trusted claim service.
"""
from __future__ import annotations
from datetime import datetime, timezone
import copy, hashlib, json, math, os, urllib.request
from typing import Any, Callable, Mapping

GATEWAY_VERSION="ROLE_EXECUTION_GATEWAY_V1"
CONTROL_PLANE_VERSION="EXECUTION_CONTROL_PLANE_V2"
ROLE="BIG_TECH_TECH_RND"
CLOCK_SKEW_SECONDS=60
TTL_POLICY={("KAGGLE","R020_FRAMEPACK_EXECUTION"):900}

class AdmissionDenied(RuntimeError): pass
class AdmissionUnknown(RuntimeError): pass

def _canonical(v: Any) -> Any:
    if isinstance(v, Mapping): return {k:_canonical(v[k]) for k in sorted(v)}
    if isinstance(v, list): return [_canonical(x) for x in v]
    return v

def _stable(v: Any) -> str:
    return json.dumps(_canonical(v),separators=(",",":"),ensure_ascii=False)

def _digest(v: Any) -> str:
    return hashlib.sha256(_stable(v).encode()).hexdigest()

def _parse_ts(value: str) -> datetime:
    try: dt=datetime.fromisoformat(value.replace("Z","+00:00"))
    except Exception as exc: raise AdmissionDenied("ADMISSION_TIMESTAMP_INVALID") from exc
    if dt.tzinfo is None: raise AdmissionDenied("ADMISSION_TIMESTAMP_INVALID")
    return dt.astimezone(timezone.utc)

def parse_token(raw: str|None=None,*,surface: str|None=None)->dict[str,Any]:
    if raw is None:
        scoped=f"AH_EXECUTION_ADMISSION_TOKEN_{surface.upper()}" if surface else ""
        raw=os.environ.get(scoped,"") if scoped else ""
        raw=raw or os.environ.get("AH_EXECUTION_ADMISSION_TOKEN","")
    if not raw: raise AdmissionDenied("ADMISSION_TOKEN_REQUIRED")
    try: token=json.loads(raw)
    except Exception as exc: raise AdmissionDenied("ADMISSION_TOKEN_INVALID_JSON") from exc
    if (
        not isinstance(token,dict)
        or not isinstance(token.get("admission"),dict)
        or not token.get("admission_id")
        or not token.get("issuer_mac")
    ):
        raise AdmissionDenied("ADMISSION_TOKEN_REQUIRED")
    return token

def validate_admission_v2(*,surface:str,operation:str,task_id:str,role:str=ROLE,raw:str|None=None,
                          now:datetime|None=None,clock_skew_seconds:float=CLOCK_SKEW_SECONDS)->dict[str,Any]:
    """Local non-authoritative validation only.

    This function intentionally cannot authenticate issuer_mac because the workload
    has no issuer verifier/signing secret. Authenticity becomes trusted only after
    the control-plane claim service returns an exact CLAIMED receipt.
    """
    if not task_id: raise AdmissionDenied("EXPECTED_TASK_ID_REQUIRED")
    if not isinstance(clock_skew_seconds,(int,float)) or not math.isfinite(clock_skew_seconds) or clock_skew_seconds<0:
        raise AdmissionDenied("ADMISSION_CLOCK_INVALID")
    token=parse_token(raw,surface=surface); a=token["admission"]
    required=("gateway_version","control_plane_version","surface","operation","role","task_id",
              "issued_at","expires_at","nonce","evidence_digest","issuer_id")
    for field in required:
        if not a.get(field): raise AdmissionDenied(f"ADMISSION_FIELD_REQUIRED:{field}")
    expected_surface=surface.upper()
    if a["gateway_version"]!=GATEWAY_VERSION: raise AdmissionDenied("ADMISSION_GATEWAY_VERSION_MISMATCH")
    if a["control_plane_version"]!=CONTROL_PLANE_VERSION: raise AdmissionDenied("ADMISSION_CONTROL_PLANE_VERSION_MISMATCH")
    if a["surface"]!=expected_surface: raise AdmissionDenied("ADMISSION_SURFACE_MISMATCH")
    if a["operation"]!=operation: raise AdmissionDenied("ADMISSION_OPERATION_MISMATCH")
    if a["role"]!=role: raise AdmissionDenied("ADMISSION_ROLE_MISMATCH")
    if a["task_id"]!=task_id: raise AdmissionDenied("ADMISSION_TASK_MISMATCH")
    if _digest(a)!=token["admission_id"]: raise AdmissionDenied("ADMISSION_INTEGRITY_FAILURE")
    if not isinstance(a["nonce"],str) or len(a["nonce"])<32: raise AdmissionDenied("ADMISSION_NONCE_ENTROPY_FAILURE")
    issued=_parse_ts(a["issued_at"]); expires=_parse_ts(a["expires_at"])
    if expires<=issued: raise AdmissionDenied("ADMISSION_EXPIRY_ORDER_FAILURE")
    max_ttl=TTL_POLICY.get((expected_surface,operation))
    if max_ttl is None: raise AdmissionDenied("V2_SURFACE_POLICY_NOT_ADMITTED")
    if (expires-issued).total_seconds()>max_ttl: raise AdmissionDenied("ADMISSION_TTL_POLICY_FAILURE")
    now=now or datetime.now(timezone.utc)
    if not isinstance(now,datetime) or now.tzinfo is None: raise AdmissionDenied("ADMISSION_CLOCK_INVALID")
    now=now.astimezone(timezone.utc)
    if (issued-now).total_seconds()>clock_skew_seconds: raise AdmissionDenied("ADMISSION_NOT_YET_VALID")
    if (now-expires).total_seconds()>clock_skew_seconds: raise AdmissionDenied("ADMISSION_EXPIRED")
    return {
        "admission":copy.deepcopy(a),
        "admission_id":str(token["admission_id"]),
        "issuer_mac":str(token["issuer_mac"]),
        "authenticity":"PENDING_TRUSTED_CONTROL_PLANE_CLAIM",
    }

def consume_admission_v2(*,surface:str,operation:str,task_id:str,role:str=ROLE,raw:str|None=None,
                         claim_fn:Callable[[dict[str,Any]],Mapping[str,Any]],now:datetime|None=None,
                         clock_skew_seconds:float=CLOCK_SKEW_SECONDS)->dict[str,Any]:
    local=validate_admission_v2(
        surface=surface,operation=operation,task_id=task_id,role=role,raw=raw,
        now=now,clock_skew_seconds=clock_skew_seconds
    )
    snapshot=copy.deepcopy(local)
    payload={
        "admission_id":snapshot["admission_id"],
        "admission":copy.deepcopy(snapshot["admission"]),
        "issuer_mac":snapshot["issuer_mac"],
    }
    try: result=dict(claim_fn(payload))
    except Exception as exc: raise AdmissionUnknown(f"REPLAY_CLAIM_UNKNOWN:{exc}") from exc
    state=result.get("state")
    if state=="CLAIMED":
        if result.get("admission_id")!=snapshot["admission_id"] or result.get("nonce")!=snapshot["admission"]["nonce"]:
            raise AdmissionUnknown("REPLAY_CLAIM_IDENTITY_MISMATCH")
        snapshot["authenticity"]="TRUSTED_CONTROL_PLANE_CLAIMED"
        return {**snapshot,"replay_receipt":result}
    if state=="DENIED":
        raise AdmissionDenied(str(result.get("decision") or "TRUSTED_CONTROL_PLANE_DENIED"))
    if state=="REPLAY_DENIED":
        raise AdmissionDenied("ADMISSION_REPLAY_DENIED")
    raise AdmissionUnknown(f"REPLAY_CLAIM_UNKNOWN:{state or 'EMPTY'}")

def claim_replay_http(payload:dict[str,Any])->Mapping[str,Any]:
    url=os.environ.get("AH_EXECUTION_ADMISSION_CLAIM_URL",""); key=os.environ.get("AH_EXECUTION_ADMISSION_CLAIM_KEY","")
    if not url or not key: raise AdmissionUnknown("REPLAY_CLAIM_CONFIG_REQUIRED")
    body=json.dumps({"action":"claim",**payload},separators=(",",":")).encode()
    req=urllib.request.Request(url,data=body,method="POST",headers={
        "Content-Type":"application/json",
        "X-Execution-Admission-Key":key
    })
    with urllib.request.urlopen(req,timeout=20) as response:
        return json.loads(response.read().decode())

def read_replay_http(*,admission_id:str,nonce:str)->Mapping[str,Any]:
    url=os.environ.get("AH_EXECUTION_ADMISSION_CLAIM_URL",""); key=os.environ.get("AH_EXECUTION_ADMISSION_CLAIM_KEY","")
    if not url or not key: raise AdmissionUnknown("REPLAY_CLAIM_CONFIG_REQUIRED")
    body=json.dumps({"action":"read","admission_id":admission_id,"nonce":nonce},separators=(",",":")).encode()
    req=urllib.request.Request(url,data=body,method="POST",headers={
        "Content-Type":"application/json",
        "X-Execution-Admission-Key":key
    })
    with urllib.request.urlopen(req,timeout=20) as response:
        return json.loads(response.read().decode())
