# ALONEHUNTER X2 Evolution pending-ingestion reducer V1

Authority task: `AH_EVOLUTION_X2_PENDING_INGESTION_REDUCER_IMPLEMENTATION_20261002`.

This package is the material implementation for the Program Architect-admitted X2 receiver lifecycle. It is deliberately **not** a second Evolution database, queue, authority, provider client, or writer.

## Boundary

The reducer consumes snapshots from existing authoritative surfaces only:

- RESOURCE_DIRECTORY / physical Evolution receipt evidence;
- HANDOFF_LOG receiver routing/claim evidence;
- TASK_REGISTRY/current governance evidence supplied by the caller;
- `evolution_shadow.events` exact provider readback;
- existing HANDOFF/TASK ACK evidence;
- role Recovery Knowledge readback;
- current-state/freshness readback.

It emits a deterministic read-only worklist. It never inserts an Evolution event, appends a HANDOFF/TASK row, rewrites Recovery Knowledge, changes production state, launches a provider job, or creates a new canonical store.

Any mutation-capable adapter must execute the returned intent through an already-authorized existing surface, then provide exact readback to a **fresh** reduction. The reducer cannot self-certify independent PASS.

## Exact identity

Each receipt is keyed by:

`role_resource_key + audit_id + receipt_id + source_hash/source_identity`.

Byte-duplicate and semantic-causal duplicate checks are separate. Same prose/title never merges different exact identities.

## Lifecycle

The implementation enforces the admitted nonterminal phases:

- `UNROUTED_OR_ORPHAN_CANDIDATE`
- `MISSING_EVIDENCE`
- `NEEDS_EVIDENCE`
- `RECEIVER_DISCOVERED`
- `PENDING_INGESTION`
- `INGESTED_ACK_PENDING`
- `RECOVERY_SYNC_PENDING`
- `CURRENT_RECONCILIATION_PENDING`
- `TERMINAL_CLOSED`

No partial transition can emit `TERMINAL_CLOSED`. Terminal requires event/link-or-no-new-delta identity, ACK exact readback, Recovery Knowledge semantic coverage/readback, and current-state/freshness readback.

Allowed semantic decisions:

- `NEW_EVENT`
- `LINK_EXISTING_EVENT`
- `RECURRENCE`
- `NO_NEW_CAUSAL_DELTA`
- `SUPERSEDED_FALSE_CLAIM`
- `NEEDS_EVIDENCE`

A provider event hash is trusted only when supplied as exact provider readback. The deterministic candidate hash is an idempotency/decision key, never a substitute for provider evidence.

## Crash recovery

- Receipt exists, receiver handoff absent: stay `UNROUTED_OR_ORPHAN_CANDIDATE`.
- Handoff exists, physical receipt missing: `MISSING_EVIDENCE`.
- Receiver claimed, provider event absent: `PENDING_INGESTION`; do not infer success.
- Provider event exists, ACK absent: `INGESTED_ACK_PENDING`; do not insert the event again.
- ACK exists, Recovery Knowledge not current: `RECOVERY_SYNC_PENDING`.
- Recovery Knowledge exists, current reduction/freshness not read back: `CURRENT_RECONCILIATION_PENDING`.
- Only complete readback chain closes.

## X3 shared closure guard

`guarded_write_readback()` implements the admitted X3 merge point:

prestate watermark -> authorized write -> exact assigned-row readback -> payload hash comparison -> bounded same-family/current watermark reread.

Results:

- `PASS`
- `UNKNOWN`
- `PAYLOAD_MISMATCH`
- `ABORT_REREAD_RECONCILE`

No global lock is introduced.

## Executable CLI

The module accepts one JSON snapshot from a file or stdin and emits deterministic JSON:

```bash
python -m governance.evolution_x2 snapshot.json
cat snapshot.json | python -m governance.evolution_x2
```

Output schema: `AH_EVOLUTION_X2_WORKLIST_V1`.
Authority label: `READ_ONLY_PROJECTION__NO_NEW_STORE`.
A `worklist_hash` gives deterministic replay evidence.

## Behavioral harness

`python -m unittest governance.test_evolution_x2 -v`

The harness covers admitted E01-E16 plus exact counterexamples:

- duplicate byte receipt;
- duplicate causal event across receipts;
- crash after ingest before ACK;
- concurrent different/same-role receipts;
- stale receipt after newer audit;
- already-ingested receipt;
- malformed receipt;
- Producer withdrawn E58;
- Audio R20 and Lyrics R4 zero-new-delta parent reuse;
- Social zero-new-delta link;
- Tech missing distinct receipt;
- X3 429/unavailable, payload mismatch, concurrent-write reconciliation.

Independent Program Architect verification is still required after CI. Passing this harness proves implementation behavior only; it does not ingest the Oct02 backlog or close governance state.
