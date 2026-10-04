# Holodny frozen APEX one-submit runbook

Task: AH_HOLODNY_RASCHET_C01_C10_AUDIO_INTELLIGENCE_APEX_20260927

## Preconditions
- Program Architect private-Dataset ingress acceptance: HANDOFF109297.
- Exact transport ZIPs 9/9 exist in private Google Drive staging folder:
  /ALONEHUNTER — MASTER/.TECH_STAGING_HOLODNY_20261004
- Execution packet branch:
  tech/holodny-frozen-apex-execution-v1-20261004
- Runner blob: 02d76c56c3a0ca40621ccd8b50ec27c3e9ea3f0b
- Exact PCM10 manifest: audio_apex/holodny_raschet_pcm10_manifest.json
- Owner lyrics authority: Drive 1buWFtoFw5NBIbs1bnfdOgLCH_py_nOgx / section ХОЛОДНЫЙ РАСЧЁТ.
- No current provider job/dataset collision.

## Provider actions — exactly once
1. Collision-check dataset slug:
   alonehunter/ah-holodny-pcm10-private-20261004
2. If absent, place this file as dataset-metadata.json beside the 9 transport ZIPs and create exactly one PRIVATE Dataset.
3. Read back provider dataset metadata and require private=true.
4. Collision-check kernel slug:
   alonehunter/ah-holodny-raschet-pcm10-dual-axis-final
5. Stage exactly:
   - holodny_raschet_pcm10_private_dataset_runner.py
   - holodny_kernel-metadata.json renamed kernel-metadata.json
6. Push exactly one kernel version.
7. Preserve dataset/kernel IDs and version.
8. Do not poll legacy Kaggle status/output endpoints for Audio Intelligence; reconcile canonical callback 6075795 / exact terminal receipt.
9. Terminal PASS requires:
   - transport_manifest.state = PASS_EXACT_TRANSPORT_9_OF_9
   - split_manifest.state = PASS_EXACT_PCM10
   - state = PASS_DUAL_AXIS_COMBINED_10
   - exact MUSIC / LYRICS / BALANCED rankings and rows.
10. On UNKNOWN, reconcile same identity before any retry.

## Hard prohibitions
- No public Dataset.
- No signed/public source URL.
- No new scorer/model/weights.
- No lyrics substitution.
- No re-extraction.
- No duplicate Dataset/kernel after UNKNOWN.
- No Make6176635 mutation: live scenario is hard-coded to R008.
