import json
import unittest

from governance.evolution_x2 import (
    Ack, Freshness, GuardVerdict, Handoff, Lifecycle, ProviderEvent, Receipt,
    RecoveryKnowledge, SemanticDecision, WriteObservation, ack_intent,
    guarded_write_readback, reduce_snapshot, reduce_worklist, recovery_sync_intent,
)


def receipt(role="AH_AGENT_PROFILE_BIG_TECH", audit="AUDIT_R2", rid="RECEIPT_R2",
            source="DriveReceiptR2", fp="cause-110-119", **kw):
    return Receipt(role, audit, rid, source, causal_fingerprint=fp, **kw)


def handoff(r, accepted=False, discovered=True,
            receiver="AH_AGENT_PROFILE_PROGRAM_ARCHITECT"):
    return Handoff(r.role_resource_key, r.audit_id, r.receipt_id, r.source_identity,
                   receiver_resource_key=receiver, receiver_discovered=discovered,
                   receiver_accepted=accepted)


def event(r, event_hash="evt-1", receipt_id=None, fp=None, decision="NEW_EVENT"):
    return ProviderEvent(
        r.role_resource_key, event_hash, r.source_identity,
        causal_fingerprint=fp if fp is not None else r.causal_fingerprint,
        receipt_id=r.receipt_id if receipt_id is None else receipt_id,
        audit_id=r.audit_id, semantic_decision=decision,
    )


def ack(r, event_hash="evt-1", decision="NEW_EVENT"):
    return Ack(r.role_resource_key, r.audit_id, r.receipt_id, r.source_identity,
               event_hash, decision)


def rk(r, event_hash="evt-1"):
    return RecoveryKnowledge(r.role_resource_key, event_hashes=(event_hash,))


def fresh(r):
    return Freshness(r.role_resource_key, True, True, "wm-final")


class X2BehavioralHarness(unittest.TestCase):
    def one(self, r, **parts):
        return reduce_worklist([r], **parts)[0]

    def test_e01_receipt_no_receiver_is_nonterminal(self):
        r = receipt()
        x = self.one(r)
        self.assertEqual(x.lifecycle, Lifecycle.UNROUTED_OR_ORPHAN_CANDIDATE)
        self.assertFalse(x.terminal)

    def test_e02_receiver_discovered_only(self):
        r = receipt()
        x = self.one(r, handoffs=[handoff(r, accepted=False)])
        self.assertEqual(x.lifecycle, Lifecycle.RECEIVER_DISCOVERED)
        self.assertFalse(x.terminal)

    def test_e03_successful_ingestion_ack_rk_fresh_closes(self):
        r = receipt()
        e = event(r)
        x = self.one(r, handoffs=[handoff(r, accepted=True)], events=[e],
                     acks=[ack(r)], recovery_knowledge=[rk(r)], freshness=[fresh(r)])
        self.assertEqual(x.lifecycle, Lifecycle.TERMINAL_CLOSED)
        self.assertTrue(x.terminal)

    def test_e04_duplicate_byte_receipt_is_one_work_item(self):
        r = receipt(source_hash="abc123")
        xs = reduce_worklist([r, r], handoffs=[handoff(r, accepted=True)])
        self.assertEqual(len(xs), 1)
        self.assertEqual(xs[0].lifecycle, Lifecycle.PENDING_INGESTION)

    def test_e04_conflicting_same_identity_fails_closed(self):
        r1 = receipt(source_hash="abc123", semantic_hint="")
        r2 = receipt(source_hash="abc123", semantic_hint="NEW_EVENT")
        xs = reduce_worklist([r1, r2], handoffs=[handoff(r1, accepted=True)])
        self.assertEqual(len(xs), 1)
        self.assertEqual(xs[0].lifecycle, Lifecycle.NEEDS_EVIDENCE)

    def test_e05_duplicate_causal_different_receipt_links_existing(self):
        old = receipt(audit="AUDIT_R1", rid="RECEIPT_R1", source="old", fp="same-cause")
        new = receipt(audit="AUDIT_R2", rid="RECEIPT_R2", source="new", fp="same-cause")
        e = event(old, event_hash="evt-old")
        x = self.one(new, handoffs=[handoff(new, accepted=True)], events=[e])
        self.assertEqual(x.semantic_decision, SemanticDecision.LINK_EXISTING_EVENT)
        self.assertEqual(x.lifecycle, Lifecycle.INGESTED_ACK_PENDING)
        self.assertEqual(x.event_hash, "evt-old")

    def test_e06_crash_after_receipt_recovers_existing_surface(self):
        r = receipt()
        x = self.one(r)
        self.assertEqual(x.next_action, "route_existing_receipt_to_governance_receiver")

    def test_e07_crash_after_ingest_before_ack_never_reingests(self):
        r = receipt()
        e = event(r, event_hash="evt-readback")
        x = self.one(r, handoffs=[handoff(r, accepted=True)], events=[e])
        self.assertEqual(x.lifecycle, Lifecycle.INGESTED_ACK_PENDING)
        intent = ack_intent(x)
        self.assertEqual(intent["event_hash"], "evt-readback")
        self.assertIn("intent_hash", intent)

    def test_e08_ack_before_rk_is_recovery_sync_pending(self):
        r = receipt()
        e = event(r)
        x = self.one(r, handoffs=[handoff(r, accepted=True)], events=[e], acks=[ack(r)])
        self.assertEqual(x.lifecycle, Lifecycle.RECOVERY_SYNC_PENDING)
        self.assertIsNotNone(recovery_sync_intent(x))

    def test_e09_concurrent_different_roles_are_isolated(self):
        a = receipt(role="ROLE_A", audit="A1", rid="RA", source="SA", fp="same-text")
        b = receipt(role="ROLE_B", audit="B1", rid="RB", source="SB", fp="same-text")
        xs = reduce_worklist([a, b],
                             handoffs=[handoff(a, accepted=True), handoff(b, accepted=True)])
        self.assertEqual({x.role_resource_key for x in xs}, {"ROLE_A", "ROLE_B"})
        self.assertEqual(len({x.identity_key for x in xs}), 2)

    def test_e10_same_role_concurrent_receipts_keep_identities(self):
        old = receipt(audit="R1", rid="RID1", source="S1", fp="c1",
                      current_for_role=False)
        cur = receipt(audit="R2", rid="RID2", source="S2", fp="c2",
                      current_for_role=True)
        xs = reduce_worklist([old, cur])
        by_rid = {x.receipt_id: x for x in xs}
        self.assertEqual(len(xs), 2)
        self.assertFalse(by_rid["RID1"].current_for_role)
        self.assertTrue(by_rid["RID2"].current_for_role)

    def test_e11_stale_receipt_retained_but_not_current(self):
        r = receipt(current_for_role=False, superseded_by="AUDIT_R3")
        x = self.one(r)
        self.assertIn("historical_superseded_by:AUDIT_R3", x.reasons)
        self.assertFalse(x.current_for_role)

    def test_e12_already_ingested_closes_without_second_insert(self):
        r = receipt()
        e = event(r, event_hash="existing")
        x = self.one(r, handoffs=[handoff(r, accepted=True)], events=[e],
                     acks=[ack(r, "existing")], recovery_knowledge=[rk(r, "existing")],
                     freshness=[fresh(r)])
        self.assertTrue(x.terminal)
        self.assertNotEqual(x.lifecycle, Lifecycle.PENDING_INGESTION)

    def test_e13_malformed_receipt_needs_evidence(self):
        r = receipt(malformed_reason="missing causal source")
        self.assertEqual(self.one(r).lifecycle, Lifecycle.NEEDS_EVIDENCE)

    def test_e14_receiver_unavailable_remains_visible_nonterminal(self):
        r = receipt()
        x = self.one(r, handoffs=[handoff(r, accepted=False, discovered=True)])
        self.assertEqual(x.lifecycle, Lifecycle.RECEIVER_DISCOVERED)
        self.assertFalse(x.terminal)

    def test_e15_current_state_failure_is_nonterminal(self):
        r = receipt()
        e = event(r)
        x = self.one(r, handoffs=[handoff(r, accepted=True)], events=[e],
                     acks=[ack(r)], recovery_knowledge=[rk(r)], freshness=[])
        self.assertEqual(x.lifecycle, Lifecycle.CURRENT_RECONCILIATION_PENDING)

    def test_e16_recovery_knowledge_failure_is_nonterminal(self):
        r = receipt()
        e = event(r)
        x = self.one(r, handoffs=[handoff(r, accepted=True)], events=[e],
                     acks=[ack(r)], recovery_knowledge=[], freshness=[fresh(r)])
        self.assertEqual(x.lifecycle, Lifecycle.RECOVERY_SYNC_PENDING)

    def test_producer_withdrawn_e58_must_not_create_event(self):
        r = receipt(role="AH_AGENT_PROFILE_PRODUCER_HQ", audit="HQ_R19",
                    rid="HQ_R19_RECEIPT", source="DriveHQ", fp="withdrawn-e58",
                    semantic_hint="SUPERSEDED_FALSE_CLAIM",
                    superseded_by="HANDOFF109216")
        x = self.one(r, handoffs=[handoff(r, accepted=True)])
        self.assertEqual(x.semantic_decision, SemanticDecision.SUPERSEDED_FALSE_CLAIM)
        self.assertEqual(x.lifecycle, Lifecycle.INGESTED_ACK_PENDING)
        self.assertTrue(x.event_hash.startswith("decision:"))
        self.assertNotEqual(x.lifecycle, Lifecycle.PENDING_INGESTION)

    def test_audio_r20_zero_new_reuses_r19_event(self):
        r20 = receipt(role="AH_AGENT_PROFILE_MUSIC_AUDIO_QA", audit="AUDIO_R20",
                      rid="AUDIO_R20_RECEIPT", source="DriveR20",
                      fp="audio-r19-stable", has_new_causal_delta=False,
                      parent_receipt_id="AUDIO_R19_RECEIPT")
        parent = ProviderEvent(r20.role_resource_key, "audio-r19-event", "DriveR19",
                               causal_fingerprint="audio-r19-stable",
                               receipt_id="AUDIO_R19_RECEIPT", audit_id="AUDIO_R19")
        x = self.one(r20, handoffs=[handoff(r20, accepted=True)], events=[parent])
        self.assertEqual(x.semantic_decision, SemanticDecision.NO_NEW_CAUSAL_DELTA)
        self.assertEqual(x.event_hash, "audio-r19-event")
        self.assertEqual(x.lifecycle, Lifecycle.INGESTED_ACK_PENDING)

    def test_lyrics_r4_zero_new_reuses_r3_event(self):
        r4 = receipt(role="AH_AGENT_PROFILE_LYRICS_SUNO", audit="LYRICS_R4",
                     rid="LYRICS_R4_RECEIPT", source="DriveLR4",
                     fp="lyrics-r3-stable", has_new_causal_delta=False,
                     parent_receipt_id="LYRICS_R3_RECEIPT")
        parent = ProviderEvent(r4.role_resource_key, "lyrics-r3-event", "DriveLR3",
                               causal_fingerprint="lyrics-r3-stable",
                               receipt_id="LYRICS_R3_RECEIPT", audit_id="LYRICS_R3")
        x = self.one(r4, handoffs=[handoff(r4, accepted=True)], events=[parent])
        self.assertEqual(x.semantic_decision, SemanticDecision.NO_NEW_CAUSAL_DELTA)
        self.assertNotEqual(x.lifecycle, Lifecycle.PENDING_INGESTION)

    def test_social_zero_new_links_existing(self):
        r = receipt(role="AH_AGENT_PROFILE_SOCIAL_SYSTEMS_ARCHITECT", audit="SOCIAL_R4",
                    rid="SOCIAL_R4_RECEIPT", source="DriveSocialR4",
                    fp="social-existing-cause", has_new_causal_delta=False)
        old = ProviderEvent(r.role_resource_key, "social-event", "old-social",
                            causal_fingerprint="social-existing-cause",
                            receipt_id="SOCIAL_R1_RECEIPT", audit_id="SOCIAL_R1")
        x = self.one(r, handoffs=[handoff(r, accepted=True)], events=[old])
        self.assertEqual(x.semantic_decision, SemanticDecision.NO_NEW_CAUSAL_DELTA)
        self.assertEqual(x.event_hash, "social-event")

    def test_tech_missing_distinct_receipt_is_missing_evidence(self):
        r = receipt(role="AH_AGENT_PROFILE_TECH_VIDEO_FACTORY", audit="TECH_R4",
                    rid="TECH_E60_RECEIPT_EXPECTED", source="DriveMissing",
                    physical_receipt=False)
        x = self.one(r, handoffs=[handoff(r, accepted=True)])
        self.assertEqual(x.lifecycle, Lifecycle.MISSING_EVIDENCE)

    def test_unknown_semantic_hint_fails_closed(self):
        r = receipt(semantic_hint="INVENTED_DECISION")
        x = self.one(r, handoffs=[handoff(r, accepted=True)])
        self.assertEqual(x.lifecycle, Lifecycle.NEEDS_EVIDENCE)


    def test_unregistered_receipt_with_full_downstream_evidence_is_nonterminal(self):
        r = receipt(registered=False)
        h = handoff(r, accepted=True)
        e = event(r)
        x = self.one(
            r,
            handoffs=[h],
            events=[e],
            acks=[ack(r)],
            recovery_knowledge=[rk(r)],
            freshness=[fresh(r)],
        )
        self.assertEqual(x.lifecycle, Lifecycle.UNROUTED_OR_ORPHAN_CANDIDATE)
        self.assertNotEqual(x.lifecycle, Lifecycle.TERMINAL_CLOSED)
        self.assertEqual(
            x.next_action,
            "register_existing_receipt_on_canonical_surface_then_readback",
        )
        self.assertIn("canonical_registration_not_verified", x.reasons)


class X3ConcurrentReadbackGuard(unittest.TestCase):
    def test_pass_exact_same_watermark(self):
        obs = WriteObservation(True, "w1", "w1", "row109220", "abc", "abc", False)
        self.assertEqual(guarded_write_readback(obs), GuardVerdict.PASS)

    def test_429_or_unavailable_is_unknown(self):
        obs = WriteObservation(False, "w1", "", "", "abc", "", False)
        self.assertEqual(guarded_write_readback(obs), GuardVerdict.UNKNOWN)

    def test_payload_mismatch_fails_closed(self):
        obs = WriteObservation(True, "w1", "w1", "row", "abc", "def", False)
        self.assertEqual(guarded_write_readback(obs), GuardVerdict.PAYLOAD_MISMATCH)

    def test_concurrent_evidence_forces_reread(self):
        obs = WriteObservation(True, "w1", "w2", "row", "abc", "abc", True)
        self.assertEqual(guarded_write_readback(obs), GuardVerdict.ABORT_REREAD_RECONCILE)


class SnapshotContract(unittest.TestCase):
    def test_snapshot_output_stable_and_read_only(self):
        snapshot = {
            "watermark": {"TASK_REGISTRY": 125949, "HANDOFF_LOG": 109219},
            "receipts": [{
                "role_resource_key": "ROLE", "audit_id": "AUDIT",
                "receipt_id": "REC", "source_identity": "DriveRec",
                "causal_fingerprint": "cause",
            }],
            "handoffs": [],
        }
        a = reduce_snapshot(snapshot)
        b = reduce_snapshot(json.loads(json.dumps(snapshot)))
        self.assertEqual(a["schema"], "AH_EVOLUTION_X2_WORKLIST_V1")
        self.assertEqual(a["authority"], "READ_ONLY_PROJECTION__NO_NEW_STORE")
        self.assertEqual(a["worklist_hash"], b["worklist_hash"])
        self.assertFalse(a["items"][0]["terminal"])


if __name__ == "__main__":
    unittest.main()
