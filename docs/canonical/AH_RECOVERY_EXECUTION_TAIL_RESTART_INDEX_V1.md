# AH_RECOVERY_EXECUTION_TAIL_RESTART_INDEX_V1

Status: CONTROLLED_IMPLEMENTATION
Owner: AloneHunter
Governance owner: Program Architect / Audit Control V4
Task: AH_RECOVERY_EXECUTION_TAIL_RESTART_INDEX_FIX_20260916
Date: 2026-09-16

## Purpose
Prevent fresh-chat recovery from selecting a stale role-local task tail when a newer cross-role physical execution tail exists.

## Required restart tuple
Recovery must resolve one evidence-bound tuple before CURRENT_PRIMARY or resume-point selection:

CURRENT_PRIMARY
-> ROLE / WRITER
-> REPOSITORY + REF + COMMIT_SHA (when code-backed)
-> PROVIDER + JOB/EXECUTION_ID + observed state (when provider-backed)
-> LAST_PHYSICAL_ARTIFACT + identity/hash/bytes/format as applicable
-> TERMINAL/PROGRESS RECEIPT
-> EXACT_SOLE_RESUME_POINT
-> EVIDENCE_TIMESTAMP

UNKNOWN fields remain UNKNOWN. They must not be silently filled from older task prose.

## Freshness and cross-role negative proof
Before selecting an older tail, declaring MISSING/BLOCKED/NEW_ROUTE_REQUIRED, or restarting R&D, perform bounded checks for newer evidence on all applicable surfaces:
1. SYSTEM STATE: LIVE_STATE, TASK_REGISTRY, HANDOFF_LOG, ACTIVE_TASK_INDEX.
2. RESOURCE_DIRECTORY and applicable capability/service/provider/known-error registries.
3. Code surface: repository/ref/recent commits tied to the task or execution family.
4. Provider surface: existing job/execution IDs and current status/readback.
5. Artifact surface: physical output identity, hash/bytes/format/duration/resolution where applicable.
6. Receipt/finalizer surface and receiver discoverability.

A role-local latest row is not sufficient evidence that no newer cross-role execution tail exists.

## Selection rule
Select the newest causally coherent evidence chain, not the newest isolated timestamp. Resolve conflicts by exact task/output identity, timestamp, physical/provider evidence, correction/supersession, and Owner decisions. Physical/provider evidence outranks reports and chat memory.

## Unknown/timeout rule
UNKNOWN != FAILED. Preserve existing job/artifact IDs and read back before retry. Never duplicate a state-changing action without evidence that the prior action did not execute.

## Regression fixture: FramePack 2026-09-16
Observed recovery regression: recovery selected an older R020/LTX/Architect tail while a newer cross-role FramePack implementation existed in `AloneHunterr/alonehunter-lab2`.

Required code evidence includes the FramePack chain through commit `3fa09d0cee9ec1c660a0e3bdac76a6ec38bce2af` (`feat(video-factory): add physical FramePack MP4 inference gate`) plus its dispatcher/finalizer/manifest predecessors. Later unrelated repository commits do not supersede the FramePack execution tail merely because their timestamps are newer.

This fixture proves why recovery needs causal task-family matching plus cross-role negative proof.

## Fresh-chat recovery acceptance test
PASS requires a new chat, without Owner hints, to answer from physical evidence:
1. What work was being executed immediately before restart?
2. Which repository/ref/commit contains the relevant implementation?
3. What is the last real provider/job identity and observed state, or physically justified UNKNOWN?
4. What is the last physical artifact and its identity/hash/receipt, or physically justified UNKNOWN?
5. What is the single exact resume point?
6. What bounded evidence proves no fresher applicable execution tail was missed?

If any answer requires Owner memory, status is PARTIAL/FAIL, not recovery closure.

## Registration and synchronization
This resource must be registered in RESOURCE_DIRECTORY under a stable RESOURCE_KEY and included by applicable recovery prompts/TEAM PROMTS after material correction. Current-state provider/job/artifact values must remain dynamic SYSTEM STATE evidence and must not be hardcoded as timeless policy.

## Closure contract
Task closure requires: implementation -> physical readback -> semantic QA -> RESOURCE_DIRECTORY discoverability -> receiver discoverability -> fresh-chat recovery simulation -> correction if needed -> final readback -> TEAM PROMTS sync -> latest recovery snapshot/manifest pointers -> post-final-write backup verification.
