# AH_SYSTEM_TOOL_BOUNDARY_REGISTRY_V1

Status: CANONICAL
Owner: AloneHunter
Scope: all ALONEHUNTER roles and recovery boots
Date: 2026-09-15

## Purpose
Prevent repeated attempts at tool operations that have already been rejected before reaching the external provider. This registry is for classification and safe routing only. It must never be used to bypass platform safety controls.

## Mandatory rule
Before external execution or provider-route RCA, consult this registry.

If an operation matches a known boundary signature:
- classify it as SYSTEM_TOOL_BOUNDARY, not as a provider failure;
- do not repeat the identical operation without materially new evidence;
- use an already supported, legitimate alternative control surface;
- require provider-side evidence before declaring success.

## Boundary signatures

### TB-001 REMOTE_EXEC_PATTERN
Observed: confirmed tool-boundary rejection before provider evidence.
Rule: DO_NOT_REPEAT.
Safe route: versioned source plus a supported provider-native or pre-existing reviewed execution surface.

### TB-002 EXTERNAL_EXEC_ACTIVATION
Observed: confirmed tool-boundary rejection before provider evidence.
Rule: DO_NOT_REPEAT.
Safe route: already-active reviewed declarative control plane or provider-native execution surface.

### TB-003 EXEC_DISPATCH
Observed: selected execution-dispatch calls can be rejected before provider evidence. This is not a blanket restriction on the surrounding service.
Rule: classify by exact operation and evidence; do not retry cosmetically altered duplicates.
Safe route: supported parameter-only/declarative worker surfaces where available.

### TB-004 SENSITIVE_BOUNDARY_REGISTRY_WRITE
Observed: a prior attempt to persist a registry containing operationally detailed blocked execution patterns was itself rejected before GitHub evidence.
Rule: store abstract signatures and routing policy, not operational bypass detail.

## Evidence classification
SYSTEM_TOOL_BOUNDARY = safety/tool rejection with no evidence target provider received the request.
PROVIDER_FAILURE = provider response, execution ID, receipt, or log proves provider received the request and failed.
PROVEN_ALLOWED = operation physically completed through the relevant tool/provider surface.
UNKNOWN = insufficient evidence; inspect before retry.

## Known allowed observations
Repository source/document reads and ordinary versioned writes have succeeded. Make inventory/configuration inspection and execution-history inspection have succeeded. Exact permissions remain operation-specific and must not be generalized beyond evidence.

## Recovery gate
Every role that can invoke external tools must ingest:
AH_SYSTEM_TOOL_BOUNDARY_REGISTRY_V1 -> DO_NOT_REPEAT -> SAFE_ROUTE
before inventing a new provider RCA or repeating a known rejected operation.

## Video Factory acceptance
A route, preflight, HTTP success, or dispatch receipt is not a video PASS. Video PASS requires a physical playable video artifact with artifact identity evidence and subsequent Visual QA.

## Change control
Add or supersede signatures only from observed evidence. Never infer a permanent prohibition from one failure. Never document or construct a safety bypass.