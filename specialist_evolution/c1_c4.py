from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

UNKNOWN="UNKNOWN_RECONCILIATION_REQUIRED"

def current_authority_view(candidates: List[Dict[str,Any]], scan_complete=True, freshness=True):
    if not scan_complete or not freshness: return {"state":UNKNOWN,"candidates":candidates}
    if not candidates: return {"state":UNKNOWN,"candidates":[]}
    ordered=sorted(candidates,key=lambda x:(x.get("timestamp",""),x.get("row",0)))
    latest=ordered[-1]
    conflicts=[x for x in ordered if x.get("current") and x.get("family")==latest.get("family") and x.get("id")!=latest.get("id")]
    if conflicts and not latest.get("supersedes"): return {"state":UNKNOWN,"candidates":ordered}
    return {"state":"RESOLVED","authority":latest,"candidates":ordered,"freshness_watermark":latest.get("timestamp")}

STATES=("PRODUCED","PHYSICAL_READBACK","RECEIVER_DISCOVERED","RECEIVER_ACCEPTED","RETURNED","HQ_ACCEPTED")
ALLOWED={None:{"PRODUCED"},"PRODUCED":{"PHYSICAL_READBACK"},"PHYSICAL_READBACK":{"RECEIVER_DISCOVERED"},"RECEIVER_DISCOVERED":{"RECEIVER_ACCEPTED","RETURNED"},"RECEIVER_ACCEPTED":{"HQ_ACCEPTED"},"RETURNED":set(),"HQ_ACCEPTED":set()}
def validate_transition(old,new,evidence=None):
    if new not in ALLOWED.get(old,set()): return False
    evidence=evidence or {}
    if new=="PHYSICAL_READBACK" and not evidence.get("artifact_readback"): return False
    if new=="RECEIVER_ACCEPTED" and not evidence.get("receiver_acceptance"): return False
    if new=="HQ_ACCEPTED" and not evidence.get("hq_acceptance"): return False
    return True

CLAIMS=("BUILD_PASS","DEVICE_PASS","REQUEST_ACCEPTED","PROVIDER_STARTED","PROVIDER_RESULT_VERIFIED","PERCEPTUAL_HEARD","OWNER_APPROVED","PUBLISHED")
REQUIRED={"BUILD_PASS":"build","DEVICE_PASS":"device","REQUEST_ACCEPTED":"request","PROVIDER_STARTED":"provider_started","PROVIDER_RESULT_VERIFIED":"provider_result","PERCEPTUAL_HEARD":"human_heard","OWNER_APPROVED":"owner","PUBLISHED":"publication"}
def validate_claim_scope(claim,evidence):
    if claim not in CLAIMS: return "UNKNOWN"
    return claim if evidence.get(REQUIRED[claim]) else "UNKNOWN"

def resolve_registry(rows: List[Dict[str,Any]]):
    groups={}
    for r in rows:
        k=(str(r.get("scenario_id")),str(r.get("function_key")))
        groups.setdefault(k,[]).append(r)
    out=[]
    for k,rs in groups.items():
        rs=sorted(rs,key=lambda x:(x.get("verified_at",""),x.get("row",0)))
        out.append({"identity":k,"state":"REGISTRY_DUPLICATE_IDENTITY" if len(rs)>1 else "UNIQUE","canonical":rs[-1],"references":rs})
    return out
