# AH_AUDIO_INTELLIGENCE_RANKING_CONTRACT_V1

Status: CANONICAL ADDITIVE ANTI-REGRESSION CONTRACT
Owner: AloneHunter
Date: 2026-09-16
Applies to: Music / Audio QA, Tech, Producer HQ, downstream Video Factory consumers

## Authority consumed before this patch
- MUSIC AUDIO QA — AGENT PROFILE V7 — CANONICAL_ACTIVE, Drive 1I7T-mxnCaV9-AI797C0ieX8fVVSdEGknnce-FscYu_c
- MUSIC AUDIO QA — FULL-HISTORY CUMULATIVE DEEP AUDIT — 2026-09-14, Drive 12JBgYyvTkpayHEEu5a7gL9z4jl8OSfHB5MLgCiiu3Zg
- Standard V2, Drive 1YkCNZPRSJ_1dUj4d5H1cED3Q752qBoyqsSYfIqISHnM

This document does not replace V7 or Standard V2. It makes the previously proven multi-axis Audio Intelligence output contract explicit so Tech cannot collapse it into a single convenience score after recovery.

## Proven precedent
The Sep-14 cumulative audit records a terminal machine Audio Intelligence run for a ten-candidate set with separate outputs: Balanced machine winner C04; machine TOP3 C04/C07/C02; Music top C07; Lyrics top C08; human_heard=false; owner_preference_used=false. It also preserves the rule that machine metrics are MEASURED_PROXY and cannot be promoted to HEARD/perceptual truth.

## Mandatory ranking architecture
For multi-candidate song selection, do NOT emit only one generic Fit/Quality score.

Required decision surfaces are separate:

### 1. MUSIC ranking
Evaluate music/production independently of lyric-performance preference where technically possible. Produce at minimum:
- MUSIC_TOP_1
- MUSIC_TOP_2
- machine evidence/features used
- evidence class

### 2. LYRICS / VOCAL-TEXT ranking
Evaluate the relationship of the supplied lyrics to the realized vocal-text performance: structural/section alignment, vocal-text timing proxies, intelligibility evidence when measurable, phrasing/section behavior and other supported evidence. Produce at minimum:
- LYRICS_VOCAL_TEXT_TOP_1
- LYRICS_VOCAL_TEXT_TOP_2
- evidence/features used
- evidence class

Never claim diction, emotional credibility, naturalness, catchiness, intimacy, flow quality or other perceptual facts as HEARD when the execution surface did not actually hear the audio. Those fields remain MEASURED_PROXY or INFERRED unless OWNER_CONFIRMED/HEARD evidence exists.

### 3. BALANCE ranking
Run a separate combined decision surface for music + vocal-text relationship. Produce:
- BALANCE_TOP_1
- BALANCE_TOP_2 when useful for decision safety
- BALANCE_TOP3 machine shortlist for Owner listening when perceptual winner is unresolved

BALANCE_TOP_1 is not automatically the release winner. If HEARD is unavailable, it is explicitly BALANCED_MACHINE_WINNER / MEASURED_PROXY and the irreducible creative winner remains Owner-gated.

## Required output schema
Every multi-candidate Audio Intelligence report must include:
- exact source identity and candidate-boundary evidence;
- candidate count and exact candidate mapping;
- technical QA status per candidate;
- MUSIC TOP-2;
- LYRICS/VOCAL-TEXT TOP-2;
- BALANCE TOP-1 and preferably TOP-3 shortlist;
- evidence class on every perceptual-sounding assertion;
- HUMAN_HEARD true/false;
- OWNER_PREFERENCE_USED true/false;
- PERCEPTUAL_WINNER or OWNER_REQUIRED;
- uncertainty / invalid-comparison flags;
- downstream recommendation separated from measured facts.

## Candidate segmentation gate
Never equal-split a concatenated source merely because it contains N candidates. Proven path is UI/player reset or other physical boundary evidence -> non-equal candidate boundaries -> lossless extraction -> machine QA -> ranking. If exact alignment/boundaries are not proven, status is COMPARISON_PREP_NOT_VALIDATED.

## Comparison fairness
When asking Owner to compare candidates, excerpts must contain the same lyric words and same musical section, use equivalent semantic boundaries, and be loudness-matched where technically feasible. Blind labels are required for ranking tests. A ranking from a later-proven misaligned comparison becomes INVALID_EVIDENCE and must be superseded.

## Evidence semantics
Allowed classes remain atomic:
- HEARD
- MEASURED_PROXY
- OWNER_CONFIRMED
- INFERRED

Never collapse MEASURED_PROXY into HEARD. A spectrum cannot hear darkness; onset counts cannot hear flow; loudness cannot hear emotional force. Technical suitability and perceptual winner are separate outputs.

## Anti-simplification rule
PROHIBITED after recovery:
- replacing the multi-axis system with one generic Fit score;
- using one aggregate score as if it were MUSIC, LYRICS and BALANCE simultaneously;
- declaring a release winner from machine proxies when HEARD=false and Owner has not confirmed;
- equal splitting concatenated candidates;
- inventing scoring coefficients from chat memory;
- changing the proven scorer merely because exact canonical coefficients were not immediately found.

If scorer implementation/weights are not physically recovered, preserve the output architecture and evidence semantics, mark coefficients/implementation UNKNOWN, then resolve the canonical implementation before claiming a canonical run.

## Recovery ingestion requirement
Before any Audio Intelligence execution, Tech / Audio QA must consume, in order:
1. current SYSTEM STATE / RESOURCE_DIRECTORY pointer;
2. sole CANONICAL_ACTIVE Music Audio QA profile;
3. Standard V2;
4. latest cumulative Music Audio QA audit and newer corrections;
5. this ranking contract;
6. exact source/candidate evidence and current task receipt.

A search miss is not proof that the Audio Intelligence system does not exist. Do not rebuild a simplified scorer from memory.

## Downstream Video Factory contract
Video Factory may consume the BALANCE shortlist and later hook/window analysis, but must preserve the distinction between machine shortlist and Owner-confirmed creative winner. Audio-derived short-form windows must retain exact candidate identity, source time mapping, lyric/section mapping and evidence class.

## Current track application
For the current ten-version track «Цена любви», any earlier single Fit ranking is NONCANONICAL_PRELIMINARY. The canonical rerun must return MUSIC TOP-2, LYRICS/VOCAL-TEXT TOP-2, BALANCE machine winner/shortlist, evidence classes, and Owner gate if HEARD remains unavailable.