#!/usr/bin/env python3
"""Fail-closed Python binding for ALONEHUNTER EXECUTION_CONTROL_PLANE_V1.

This mirrors the canonical admission-token integrity contract used by
alonehunter-lab/evolution-engine/src/enforcer/control-plane-interceptor-v1.mjs.
Production executors consume a token; they do not mint one.
"""
from __future__ import annotations
import hashlib, json, os
from typing import Any, Mapping

GATEWAY_VERSION = "ROLE_EXECUTION_GATEWAY_V1"
CONTROL_PLANE_VERSION = "EXECUTION_CONTROL_PLANE_V1"
ROLE = "BIG_TECH_TECH_RND"
SURFACES = {"MAKE","KAGGLE","PROVIDER","DRIVE","GITHUB","SUPABASE","SOCIAL"}

class AdmissionDenied(RuntimeError):
    pass

def _stable(value: Mapping[str, Any]) -> str:
    # Match JSON.stringify(payload, Object.keys(payload).sort()) for the flat
    # canonical admission payload.
    return json.dumps(dict(sorted(value.items())), separators=(",",":"), ensure_ascii=False)

def _digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_stable(value).encode("utf-8")).hexdigest()

def parse_token(raw: str | None = None) -> dict[str, Any]:
    raw = raw if raw is not None else os.environ.get("AH_EXECUTION_ADMISSION_TOKEN", "")
    if not raw:
        raise AdmissionDenied("ADMISSION_TOKEN_REQUIRED")
    try:
        token = json.loads(raw)
    except Exception as exc:
        raise AdmissionDenied("ADMISSION_TOKEN_INVALID_JSON") from exc
    if not isinstance(token, dict) or not isinstance(token.get("admission"), dict) or not token.get("admission_id"):
        raise AdmissionDenied("ADMISSION_TOKEN_REQUIRED")
    return token

def require_admission(*, surface: str, operation: str, role: str = ROLE, raw: str | None = None) -> dict[str, Any]:
    token = parse_token(raw)
    admission = token["admission"]
    expected_surface = surface.upper()
    if expected_surface not in SURFACES:
        raise AdmissionDenied("UNKNOWN_MUTATION_SURFACE")
    if admission.get("gateway_version") != GATEWAY_VERSION:
        raise AdmissionDenied("ADMISSION_GATEWAY_VERSION_MISMATCH")
    if admission.get("control_plane_version") != CONTROL_PLANE_VERSION:
        raise AdmissionDenied("ADMISSION_CONTROL_PLANE_VERSION_MISMATCH")
    if admission.get("surface") != expected_surface:
        raise AdmissionDenied("ADMISSION_SURFACE_MISMATCH")
    if admission.get("operation") != operation:
        raise AdmissionDenied("ADMISSION_OPERATION_MISMATCH")
    if admission.get("role") != role:
        raise AdmissionDenied("ADMISSION_ROLE_MISMATCH")
    if _digest(admission) != token.get("admission_id"):
        raise AdmissionDenied("ADMISSION_INTEGRITY_FAILURE")
    return token

def require_terminal_admission(*, operation: str, raw: str | None = None) -> dict[str, Any]:
    return require_admission(surface="PROVIDER", operation=operation, raw=raw)
