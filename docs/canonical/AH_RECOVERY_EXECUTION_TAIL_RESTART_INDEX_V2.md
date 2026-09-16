# AH_RECOVERY_EXECUTION_TAIL_RESTART_INDEX_V2

Status: CANONICAL_CORRECTION
Owner: AloneHunter
Governance owner: Program Architect / Audit Control V4
Date: 2026-09-16
Supersedes: AH_RECOVERY_EXECUTION_TAIL_RESTART_INDEX_V1

## Purpose
Prevent T3 cold-start divergence where two roles recover different CURRENT_PRIMARY values for the same causal production family because stale role-local prompt/audit prose competes with newer canonical current-slot evidence.

## Authoritative CURRENT_PRIMARY reducer
Before any provider mutation, benchmark, R&D branch, or resume-point selection, recovery MUST resolve CURRENT_PRIMARY in this order:

1. Current canonical SYSTEM STATE material current-slot evidence: ACTIVE_TASK_INDEX plus newer exact TASK_REGISTRY/HANDOFF_LOG/LIVE_STATE corrections for the role/task family.
2. Exact physical provider/artifact/job evidence that is causally newer and materially changes the same task family.
3. Current RESOURCE_DIRECTORY correction/supersession resources and current full-history audit only as reducers/evidence, never as permission to revive older current-state prose.
4. Recovery prompt/profile dated CURRENT_* prose is advisory/historical whenever a newer canonical current-slot/correction exists.

A role MUST NOT execute a secondary/background/benchmark/provider branch merely because its own recovery prompt says "current front" or because an older audit named that branch. If canonical SYSTEM STATE already names a different CURRENT_PRIMARY, the role-local branch is non-primary unless a newer explicit canonical handoff/current-slot event reactivates it.

## Required restart tuple
CURRENT_PRIMARY -> ROLE/WRITER -> TASK_FAMILY -> REPO/REF/COMMIT when applicable -> PROVIDER/JOB observed state when applicable -> LAST_PHYSICAL_ARTIFACT identity/hash/bytes/format -> RECEIPT -> EXACT_SOLE_RESUME_POINT -> EVIDENCE_TIMESTAMP.
UNKNOWN remains UNKNOWN and is reconciled before retry.

## Cross-role consensus gate
For a shared production family, if HQ and the executing specialist recover different CURRENT_PRIMARY values, execution FAILS CLOSED before provider mutation. Reconcile against canonical SYSTEM STATE and newer physical evidence. Do not choose either role's prompt prose as tie-breaker. The corrected tuple must be written to SYSTEM STATE and discoverable by both roles before execution resumes.

## T3 regression fixture — 2026-09-16
Canonical causal truth before the regression:
- R020 / SHOT001 Wan V7 artifact: Drive `1-syCvLvkxd9Vl0yd82PpUIYfG9Gp6HQx`, SHA-256 `83891b320c88f421a21c8848bf33f465a4659f81c97907f1fda79f5bc4a74ad1`.
- GitHub causal receipt: `992a763fca6c9005c606961ad6ac4e7171525a38`.
- Binary PASS; CAMERA_CONTROL_PROOF_PASS; SHOT001_VISUAL_QA_FAIL due semantic/source binding.
- Exact resume: `V7_CONTROL_FROZEN + EXACT_SHOT001_SOURCE_BOUND successor microproof` using canonical source Drive `1q32iMeLG-u0gvxhGcL142Z7-ol4qk2gF`.
- Do not return to old LTX lane; do not blind retry V7 semantic configuration.

T3 observed divergence:
- HQ recovered the canonical Wan V7 -> exact-source-bound successor CURRENT_PRIMARY.
- Big Tech instead executed the older LTX duration branch.
- Provider readback proves the LTX duration/control branch is terminally non-admitted for this benchmark: 20s `R020_LTX_DURATION_20S_V1` FAILED with `drive_id=null` / `LTX_EVENT_ERROR`; 10s `R020_LTX_REVEAL_10S_V2` FAILED; 4s `R020_LTX_REVEAL_4S_V2_DIAG` FAILED; 4s known-good `R020_LTX_KNOWNGOOD_4S_CONTROL_20260914` FAILED, no artifact. Canonical duration-capable Make control scenario already exists as `6269386`; no new scenario is required. Repeated same-causal provider failure means no further blind LTX submit until a materially changed provider/control route is admitted.

The causal recovery defect is not absence of canonical SYSTEM STATE: ACTIVE_TASK_INDEX already carried the corrected Big Tech and HQ current slots. The defect is precedence leakage from stale role-local recovery prose (including older "current front: R020 upstream duration/opening-quality R&D" wording) combined with a generic V1 restart rule that did not explicitly forbid stale prompt CURRENT_* prose from competing with a newer canonical current slot.

## Acceptance
PASS requires both HQ and Big Tech, from physical canonical evidence, to independently resolve the same current R020 causal tuple: Wan V7 camera-control PASS -> semantic/source-binding FAIL -> exact-SHOT001-source-bound successor. LTX duration is TERMINAL_BENCHMARK_EVIDENCE / NO_ADMITTED_LTX_DURATION_TIER, not CURRENT_PRIMARY.

## Closure
Write correction to POLICY_BASELINE + SYSTEM STATE current-slot surfaces + affected recovery prompts; physically read back all; run a bounded regression verification that searches the affected prompt for stale conflicting current-state prose and proves it is explicitly superseded/non-executable.