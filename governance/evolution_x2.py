#!/usr/bin/env python3
"""ALONEHUNTER X2 Evolution pending-ingestion reducer.

Read-only projection over existing canonical surfaces. It creates no provider
events and writes no canonical state. Mutation-capable callers must use the
returned plans together with existing authorized adapters, then feed exact
readback evidence into a fresh reduction.

Authority contract:
AH_EVOLUTION_X2_PENDING_INGESTION_REDUCER_IMPLEMENTATION_20261002
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping, Sequence

PROGRAM_ARCHITECT = "AH_AGENT_PROFILE_PROGRAM_ARCHITECT"


class Lifecycle(str, Enum):
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    UNROUTED_OR_ORPHAN_CANDIDATE = "UNROUTED_OR_ORPHAN_CANDIDATE"
    RECEIVER_DISCOVERED = "RECEIVER_DISCOVERED"
    PENDING_INGESTION = "PENDING_INGESTION"
    INGESTED_ACK_PENDING = "INGESTED_ACK_PENDING"
    RECOVERY_SYNC_PENDING = "RECOVERY_SYNC_PENDING"
    CURRENT_RECONCILIATION_PENDING = "CURRENT_RECONCILIATION_PENDING"
    TERMINAL_CLOSED = "TERMINAL_CLOSED"


class SemanticDecision(str, Enum):
    NEW_EVENT = "NEW_EVENT"
    LINK_EXISTING_EVENT = "LINK_EXISTING_EVENT"
    RECURRENCE = "RECURRENCE"
    NO_NEW_CAUSAL_DELTA = "NO_NEW_CAUSAL_DELTA"
    SUPERSEDED_FALSE_CLAIM = "SUPERSEDED_FALSE_CLAIM"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"


class GuardVerdict(str, Enum):
    PASS = "PASS"
    UNKNOWN = "UNKNOWN"
    PAYLOAD_MISMATCH = "PAYLOAD_MISMATCH"
    ABORT_REREAD_RECONCILE = "ABORT_REREAD_RECONCILE"


@dataclass(frozen=True)
class Receipt:
    role_resource_key: str
    audit_id: str
    receipt_id: str
    source_identity: str
    source_hash: str = ""
    causal_fingerprint: str = ""
    physical_receipt: bool = True
    registered: bool = True
    current_for_role: bool = True
    has_new_causal_delta: bool = True
    parent_receipt_id: str = ""
    superseded_by: str = ""
    malformed_reason: str = ""
    semantic_hint: str = ""


@dataclass(frozen=True)
class Handoff:
    role_resource_key: str
    audit_id: str
    receipt_id: str
    source_identity: str
    receiver_resource_key: str = PROGRAM_ARCHITECT
    exact_readback: bool = True
    receiver_discovered: bool = True
    receiver_accepted: bool = False


@dataclass(frozen=True)
class ProviderEvent:
    role_resource_key: str
    event_hash: str
    source_identity: str
    causal_fingerprint: str = ""
    receipt_id: str = ""
    audit_id: str = ""
    semantic_decision: str = SemanticDecision.NEW_EVENT.value
    exact_readback: bool = True


@dataclass(frozen=True)
class Ack:
    role_resource_key: str
    audit_id: str
    receipt_id: str
    source_identity: str
    event_hash: str
    semantic_decision: str
    exact_readback: bool = True


@dataclass(frozen=True)
class RecoveryKnowledge:
    role_resource_key: str
    event_hashes: tuple[str, ...] = ()
    causal_fingerprints: tuple[str, ...] = ()
    receipt_ids: tuple[str, ...] = ()
    exact_readback: bool = True
    semantically_current: bool = True


@dataclass(frozen=True)
class Freshness:
    role_resource_key: str
    current_state_reduced: bool = False
    exact_readback: bool = False
    source_watermark: str = ""


@dataclass(frozen=True)
class WorkItem:
    identity_key: str
    role_resource_key: str
    audit_id: str
    receipt_id: str
    source_identity: str
    lifecycle: Lifecycle
    semantic_decision: SemanticDecision
    receiver_resource_key: str
    event_hash: str = ""
    linked_receipt_id: str = ""
    next_action: str = ""
    reasons: tuple[str, ...] = ()
    current_for_role: bool = True

    @property
    def terminal(self) -> bool:
        return self.lifecycle is Lifecycle.TERMINAL_CLOSED

    def to_dict(self) -> dict:
        out = asdict(self)
        out["lifecycle"] = self.lifecycle.value
        out["semantic_decision"] = self.semantic_decision.value
        out["terminal"] = self.terminal
        return out


@dataclass(frozen=True)
class WriteObservation:
    source_available: bool
    pre_watermark: str
    post_watermark: str
    assigned_row_identity: str
    expected_payload_hash: str
    readback_payload_hash: str
    concurrent_same_family_evidence: bool = False


def _canon(value: str) -> str:
    return (value or "").strip()


def identity_key(receipt: Receipt) -> str:
    """Exact X2 key: role + audit + receipt + causal/source identity."""
    parts = (
        _canon(receipt.role_resource_key),
        _canon(receipt.audit_id),
        _canon(receipt.receipt_id),
        _canon(receipt.source_hash) or _canon(receipt.source_identity),
    )
    return "|".join(parts)


def canonical_hash(payload: Mapping | Sequence | str) -> str:
    if isinstance(payload, str):
        raw = payload
    else:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def semantic_fingerprint(receipt: Receipt) -> str:
    if _canon(receipt.causal_fingerprint):
        return _canon(receipt.causal_fingerprint)
    return canonical_hash({
        "role_resource_key": _canon(receipt.role_resource_key),
        "source_identity": _canon(receipt.source_identity),
        "source_hash": _canon(receipt.source_hash),
        "receipt_id": _canon(receipt.receipt_id),
    })


def candidate_event_hash(receipt: Receipt, decision: SemanticDecision) -> str:
    """Deterministic idempotency candidate; never substitutes provider readback."""
    return canonical_hash({
        "role_resource_key": receipt.role_resource_key,
        "audit_id": receipt.audit_id,
        "receipt_id": receipt.receipt_id,
        "source_identity": receipt.source_identity,
        "source_hash": receipt.source_hash,
        "causal_fingerprint": semantic_fingerprint(receipt),
        "decision": decision.value,
    })


def _valid_receipt(r: Receipt) -> tuple[bool, tuple[str, ...]]:
    required = {
        "role_resource_key": r.role_resource_key,
        "audit_id": r.audit_id,
        "receipt_id": r.receipt_id,
        "source_identity": r.source_identity,
    }
    missing = tuple(k for k, v in required.items() if not _canon(v))
    reasons: list[str] = []
    if missing:
        reasons.append("missing_required:" + ",".join(missing))
    if _canon(r.malformed_reason):
        reasons.append("malformed:" + _canon(r.malformed_reason))
    return not reasons, tuple(reasons)


def _same_exact_identity(r: Receipt, x: object) -> bool:
    return (
        getattr(x, "role_resource_key", "") == r.role_resource_key
        and getattr(x, "audit_id", "") == r.audit_id
        and getattr(x, "receipt_id", "") == r.receipt_id
        and getattr(x, "source_identity", "") == r.source_identity
    )


def _find_handoff(r: Receipt, handoffs: Sequence[Handoff]) -> Handoff | None:
    candidates = [h for h in handoffs if _same_exact_identity(r, h)]
    for h in candidates:
        if h.exact_readback:
            return h
    return candidates[0] if candidates else None


def _exact_event(r: Receipt, events: Sequence[ProviderEvent]) -> ProviderEvent | None:
    for e in events:
        if not e.exact_readback or e.role_resource_key != r.role_resource_key:
            continue
        if e.receipt_id and e.receipt_id == r.receipt_id:
            if not e.audit_id or e.audit_id == r.audit_id:
                return e
        if e.source_identity and e.source_identity == r.source_identity and e.audit_id == r.audit_id:
            return e
    return None


def _semantic_event(r: Receipt, events: Sequence[ProviderEvent]) -> ProviderEvent | None:
    fp = semantic_fingerprint(r)
    if not fp:
        return None
    for e in events:
        if (
            e.exact_readback
            and e.role_resource_key == r.role_resource_key
            and _canon(e.causal_fingerprint)
            and e.causal_fingerprint == fp
        ):
            return e
    return None


def _parent_event(r: Receipt, events: Sequence[ProviderEvent]) -> ProviderEvent | None:
    if not r.parent_receipt_id:
        return None
    for e in events:
        if e.exact_readback and e.role_resource_key == r.role_resource_key and e.receipt_id == r.parent_receipt_id:
            return e
    return None


def _find_ack(r: Receipt, event_hash: str, acks: Sequence[Ack]) -> Ack | None:
    for a in acks:
        if _same_exact_identity(r, a) and a.exact_readback and a.event_hash == event_hash:
            return a
    return None


def _rk_covers(r: Receipt, event_hash: str, rks: Sequence[RecoveryKnowledge]) -> bool:
    fp = semantic_fingerprint(r)
    for rk in rks:
        if rk.role_resource_key != r.role_resource_key or not rk.exact_readback or not rk.semantically_current:
            continue
        if event_hash and event_hash in rk.event_hashes:
            return True
        if fp and fp in rk.causal_fingerprints:
            return True
        if r.receipt_id in rk.receipt_ids:
            return True
    return False


def _freshness_ok(r: Receipt, freshness: Sequence[Freshness]) -> bool:
    return any(
        f.role_resource_key == r.role_resource_key
        and f.current_state_reduced
        and f.exact_readback
        for f in freshness
    )


def _decision_for(
    r: Receipt,
    exact: ProviderEvent | None,
    semantic: ProviderEvent | None,
    parent: ProviderEvent | None,
) -> tuple[SemanticDecision, ProviderEvent | None]:
    hint = _canon(r.semantic_hint)
    if hint:
        try:
            hinted = SemanticDecision(hint)
        except ValueError:
            return SemanticDecision.NEEDS_EVIDENCE, None
        if hinted in (SemanticDecision.SUPERSEDED_FALSE_CLAIM, SemanticDecision.NEEDS_EVIDENCE):
            return hinted, None

    if not r.has_new_causal_delta:
        link = parent or semantic or exact
        if link:
            return SemanticDecision.NO_NEW_CAUSAL_DELTA, link
        return SemanticDecision.NEEDS_EVIDENCE, None

    if exact:
        try:
            return SemanticDecision(exact.semantic_decision), exact
        except ValueError:
            return SemanticDecision.LINK_EXISTING_EVENT, exact

    if semantic:
        return SemanticDecision.LINK_EXISTING_EVENT, semantic

    return SemanticDecision.NEW_EVENT, None


def reduce_worklist(
    receipts: Sequence[Receipt],
    handoffs: Sequence[Handoff] = (),
    events: Sequence[ProviderEvent] = (),
    acks: Sequence[Ack] = (),
    recovery_knowledge: Sequence[RecoveryKnowledge] = (),
    freshness: Sequence[Freshness] = (),
) -> list[WorkItem]:
    """Produce a deterministic read-only X2 worklist."""
    unique: dict[str, Receipt] = {}
    for r in receipts:
        key = identity_key(r)
        prior = unique.get(key)
        if prior is None:
            unique[key] = r
        elif asdict(prior) != asdict(r):
            unique[key] = Receipt(
                **{**asdict(r), "malformed_reason": "conflicting_duplicate_identity"}
            )

    out: list[WorkItem] = []
    for key, r in sorted(unique.items(), key=lambda kv: kv[0]):
        valid, validation_reasons = _valid_receipt(r)
        h = _find_handoff(r, handoffs)

        if not r.physical_receipt:
            state = Lifecycle.MISSING_EVIDENCE if h else Lifecycle.UNROUTED_OR_ORPHAN_CANDIDATE
            out.append(WorkItem(
                key, r.role_resource_key, r.audit_id, r.receipt_id, r.source_identity,
                state, SemanticDecision.NEEDS_EVIDENCE, PROGRAM_ARCHITECT,
                next_action="recover_physical_receipt_before_ingestion",
                reasons=("physical_receipt_not_verified",),
                current_for_role=r.current_for_role,
            ))
            continue

        if not valid:
            out.append(WorkItem(
                key, r.role_resource_key, r.audit_id, r.receipt_id, r.source_identity,
                Lifecycle.NEEDS_EVIDENCE, SemanticDecision.NEEDS_EVIDENCE, PROGRAM_ARCHITECT,
                next_action="repair_or_supply_receipt_evidence",
                reasons=validation_reasons,
                current_for_role=r.current_for_role,
            ))
            continue

        if r.superseded_by and r.semantic_hint != SemanticDecision.SUPERSEDED_FALSE_CLAIM.value:
            current_reasons = ("historical_superseded_by:" + r.superseded_by,)
        elif not r.current_for_role:
            current_reasons = ("historical_not_current_for_role",)
        else:
            current_reasons = ()

        if not h or not h.exact_readback or not h.receiver_discovered:
            out.append(WorkItem(
                key, r.role_resource_key, r.audit_id, r.receipt_id, r.source_identity,
                Lifecycle.UNROUTED_OR_ORPHAN_CANDIDATE, SemanticDecision.NEEDS_EVIDENCE, PROGRAM_ARCHITECT,
                next_action="route_existing_receipt_to_governance_receiver",
                reasons=current_reasons + ("receiver_handoff_not_read_back",),
                current_for_role=r.current_for_role,
            ))
            continue

        receiver = h.receiver_resource_key or PROGRAM_ARCHITECT
        if receiver != PROGRAM_ARCHITECT:
            out.append(WorkItem(
                key, r.role_resource_key, r.audit_id, r.receipt_id, r.source_identity,
                Lifecycle.NEEDS_EVIDENCE, SemanticDecision.NEEDS_EVIDENCE, receiver,
                next_action="reconcile_receiver_authority",
                reasons=current_reasons + ("receiver_is_not_program_architect",),
                current_for_role=r.current_for_role,
            ))
            continue

        exact = _exact_event(r, events)
        sem = _semantic_event(r, events)
        parent = _parent_event(r, events)
        decision, linked = _decision_for(r, exact, sem, parent)

        if decision is SemanticDecision.SUPERSEDED_FALSE_CLAIM:
            event_hash = "decision:" + candidate_event_hash(r, decision)
        elif decision is SemanticDecision.NEEDS_EVIDENCE:
            out.append(WorkItem(
                key, r.role_resource_key, r.audit_id, r.receipt_id, r.source_identity,
                Lifecycle.NEEDS_EVIDENCE, decision, receiver,
                linked_receipt_id=linked.receipt_id if linked else "",
                next_action="governance_semantic_evidence_required",
                reasons=current_reasons + ("semantic_decision_not_safely_resolved",),
                current_for_role=r.current_for_role,
            ))
            continue
        else:
            event_hash = linked.event_hash if linked else ""

        if not h.receiver_accepted:
            out.append(WorkItem(
                key, r.role_resource_key, r.audit_id, r.receipt_id, r.source_identity,
                Lifecycle.RECEIVER_DISCOVERED, decision, receiver,
                event_hash=event_hash,
                linked_receipt_id=linked.receipt_id if linked else "",
                next_action="receiver_claim_exact_identity",
                reasons=current_reasons,
                current_for_role=r.current_for_role,
            ))
            continue

        if decision is SemanticDecision.NEW_EVENT and not linked:
            out.append(WorkItem(
                key, r.role_resource_key, r.audit_id, r.receipt_id, r.source_identity,
                Lifecycle.PENDING_INGESTION, decision, receiver,
                next_action="authorized_governance_ingest_then_exact_event_readback",
                reasons=current_reasons,
                current_for_role=r.current_for_role,
            ))
            continue

        if decision is SemanticDecision.SUPERSEDED_FALSE_CLAIM:
            linked_hash = event_hash
        elif linked:
            linked_hash = linked.event_hash
        else:
            linked_hash = exact.event_hash if exact else ""

        if not linked_hash:
            out.append(WorkItem(
                key, r.role_resource_key, r.audit_id, r.receipt_id, r.source_identity,
                Lifecycle.NEEDS_EVIDENCE, SemanticDecision.NEEDS_EVIDENCE, receiver,
                next_action="exact_provider_event_or_parent_link_readback_required",
                reasons=current_reasons + ("no_read_back_event_identity",),
                current_for_role=r.current_for_role,
            ))
            continue

        ack = _find_ack(r, linked_hash, acks)
        if not ack:
            out.append(WorkItem(
                key, r.role_resource_key, r.audit_id, r.receipt_id, r.source_identity,
                Lifecycle.INGESTED_ACK_PENDING, decision, receiver,
                event_hash=linked_hash,
                linked_receipt_id=linked.receipt_id if linked else "",
                next_action="append_one_existing_surface_ack_after_event_readback",
                reasons=current_reasons,
                current_for_role=r.current_for_role,
            ))
            continue

        if not _rk_covers(r, linked_hash, recovery_knowledge):
            out.append(WorkItem(
                key, r.role_resource_key, r.audit_id, r.receipt_id, r.source_identity,
                Lifecycle.RECOVERY_SYNC_PENDING, decision, receiver,
                event_hash=linked_hash,
                linked_receipt_id=linked.receipt_id if linked else "",
                next_action="update_or_link_role_recovery_knowledge_then_readback",
                reasons=current_reasons,
                current_for_role=r.current_for_role,
            ))
            continue

        if not _freshness_ok(r, freshness):
            out.append(WorkItem(
                key, r.role_resource_key, r.audit_id, r.receipt_id, r.source_identity,
                Lifecycle.CURRENT_RECONCILIATION_PENDING, decision, receiver,
                event_hash=linked_hash,
                linked_receipt_id=linked.receipt_id if linked else "",
                next_action="re_reduce_current_state_and_freshness_then_readback",
                reasons=current_reasons,
                current_for_role=r.current_for_role,
            ))
            continue

        out.append(WorkItem(
            key, r.role_resource_key, r.audit_id, r.receipt_id, r.source_identity,
            Lifecycle.TERMINAL_CLOSED, decision, receiver,
            event_hash=linked_hash,
            linked_receipt_id=linked.receipt_id if linked else "",
            next_action="none",
            reasons=current_reasons,
            current_for_role=r.current_for_role,
        ))
    return out


def ack_intent(item: WorkItem) -> dict | None:
    """Return append intent only after provider/link readback; never writes itself."""
    if item.lifecycle is not Lifecycle.INGESTED_ACK_PENDING or not item.event_hash:
        return None
    payload = {
        "task_family": "AH_EVOLUTION_X2_PENDING_INGESTION_REDUCER_IMPLEMENTATION_20261002",
        "role_resource_key": item.role_resource_key,
        "audit_id": item.audit_id,
        "receipt_id": item.receipt_id,
        "source_identity": item.source_identity,
        "event_hash": item.event_hash,
        "semantic_decision": item.semantic_decision.value,
        "receiver_resource_key": PROGRAM_ARCHITECT,
    }
    payload["intent_hash"] = canonical_hash(payload)
    return payload


def recovery_sync_intent(item: WorkItem) -> dict | None:
    if item.lifecycle is not Lifecycle.RECOVERY_SYNC_PENDING or not item.event_hash:
        return None
    payload = {
        "role_resource_key": item.role_resource_key,
        "audit_id": item.audit_id,
        "receipt_id": item.receipt_id,
        "event_hash": item.event_hash,
        "required_state": "RECOVERY_KNOWLEDGE_UPDATED",
    }
    payload["intent_hash"] = canonical_hash(payload)
    return payload


def guarded_write_readback(obs: WriteObservation) -> GuardVerdict:
    """X3 merged guard: prestate -> write -> exact readback -> concurrent reread."""
    if not obs.source_available:
        return GuardVerdict.UNKNOWN
    if not _canon(obs.assigned_row_identity):
        return GuardVerdict.UNKNOWN
    if obs.expected_payload_hash != obs.readback_payload_hash:
        return GuardVerdict.PAYLOAD_MISMATCH
    if obs.concurrent_same_family_evidence or (
        obs.pre_watermark and obs.post_watermark and obs.pre_watermark != obs.post_watermark
    ):
        return GuardVerdict.ABORT_REREAD_RECONCILE
    return GuardVerdict.PASS


def _load_dataclasses(rows: Iterable[dict], cls):
    return [cls(**row) for row in rows]


def reduce_snapshot(snapshot: Mapping) -> dict:
    items = reduce_worklist(
        _load_dataclasses(snapshot.get("receipts", []), Receipt),
        _load_dataclasses(snapshot.get("handoffs", []), Handoff),
        _load_dataclasses(snapshot.get("events", []), ProviderEvent),
        _load_dataclasses(snapshot.get("acks", []), Ack),
        _load_dataclasses(snapshot.get("recovery_knowledge", []), RecoveryKnowledge),
        _load_dataclasses(snapshot.get("freshness", []), Freshness),
    )
    watermark = snapshot.get("watermark", {})
    return {
        "schema": "AH_EVOLUTION_X2_WORKLIST_V1",
        "authority": "READ_ONLY_PROJECTION__NO_NEW_STORE",
        "source_watermark": watermark,
        "items": [i.to_dict() for i in items],
        "worklist_hash": canonical_hash([i.to_dict() for i in items]),
    }


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Read-only ALONEHUNTER X2 Evolution worklist reducer")
    p.add_argument("snapshot", nargs="?", help="JSON snapshot path; stdin if omitted")
    args = p.parse_args(argv)
    if args.snapshot:
        raw = Path(args.snapshot).read_text(encoding="utf-8")
    else:
        import sys
        raw = sys.stdin.read()
    snapshot = json.loads(raw)
    print(json.dumps(reduce_snapshot(snapshot), ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
