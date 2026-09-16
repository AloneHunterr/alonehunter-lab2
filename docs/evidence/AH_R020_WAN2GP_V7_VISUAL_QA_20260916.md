# AH_R020_WAN2GP_V7_VISUAL_QA_20260916

Status: RECEIVER_QA_VERIFIED
Date: 2026-09-16
Role writer: Big Tech / Tech R&D (durable materialization of independent Visual QA verdict)
Task family: R020 / SHOT001

## Exact artifact
- Name: `AH_R020_WAN2GP_PROOF_V7.mp4`
- Drive ID: `1-syCvLvkxd9Vl0yd82PpUIYfG9Gp6HQx`
- Bytes: `3231808`
- SHA-256: `83891b320c88f421a21c8848bf33f465a4659f81c97907f1fda79f5bc4a74ad1`
- Video: H.264 MP4, 832x480, 16 fps, 49 frames, 3.0625 s
- Binary decode: PASS

## Independent Visual QA verdict
- `BINARY_QA_PASS`
- `CAMERA_CONTROL_PROOF_PASS`
- `SHOT001_VISUAL_QA_FAIL`

The failure is **semantic/source binding**, not camera-control failure. Relative to the previous LTX V2 failure, critical zoom/reframe is practically eliminated. V7 therefore proves a materially better camera-lock/control behavior.

The generated scene does not preserve the approved SHOT001 scene/source contract: instead of near-black cold worn plaster + copper pipe + faint practical spill, the result presents a wet/blue/rain-like surface and loses the required wall/pipe identity.

## Production admission
V7 is **not admitted as production SHOT001**. Do not promote binary/provider PASS to Visual/HQ/Owner PASS.

## Proven causal delta
`LTX V2`: camera push/zoom/reframe failure.

`Wan V7`: camera-control problem materially solved, but exact source/semantic binding failed.

Therefore the entire Wan V7 route must NOT be classified as failed. It has proven one required control dimension and isolated the next causal failure.

## Frozen successor contract
Preserve/freeze the V7 camera-control behavior. Change only the source-binding/ingress dimension needed to bind the exact canonical SHOT001 source:

- Canonical source Drive ID: `1q32iMeLG-u0gvxhGcL142Z7-ol4qk2gF`
- Required scene: near-black cold worn plaster + copper pipe + faint practical spill
- Do not return to the old LTX lane.
- Do not blind-retry the same V7 semantic configuration.
- Do not reopen solved Kaggle->Drive transport work.

## Exact resume point
`V7_CONTROL_FROZEN + EXACT_SHOT001_SOURCE_BOUND successor microproof`

Then require:
1. provider receipt/reconciliation;
2. durable Drive artifact + exact bytes/SHA-256;
3. binary QA;
4. independent Visual QA for both source/semantic preservation and camera behavior;
5. only then any R020 production/HQ promotion.

## Recovery requirement
Fresh-chat recovery must surface this causal split. A generic `V7 FAIL` is incorrect and loses proven camera-control knowledge. A generic `V7 PASS` is also incorrect because SHOT001 semantic/source preservation failed.
