#!/usr/bin/env python3
import hashlib,json,threading,unittest
from datetime import datetime,timezone
from control_plane_v2 import *

NOW=datetime(2026,10,3,13,0,0,tzinfo=timezone.utc)
def mk(overrides=None):
    a={
      "gateway_version":GATEWAY_VERSION,"control_plane_version":CONTROL_PLANE_VERSION,
      "surface":"KAGGLE","operation":"R020_FRAMEPACK_EXECUTION","role":ROLE,
      "task_id":"AH_EXECUTION_ADMISSION_REPLAY_HARDENING_20260926",
      "issued_at":"2026-10-03T12:55:00+00:00","expires_at":"2026-10-03T13:10:00+00:00",
      "nonce":"00112233445566778899aabbccddeeff","evidence_digest":"evidence","issuer_id":"TEST_ISSUER"}
    a.update(overrides or {})
    stable=json.dumps(dict(sorted(a.items())),separators=(",",":"),ensure_ascii=False)
    return {"admission":a,"admission_id":hashlib.sha256(stable.encode()).hexdigest()}

class Store:
    def __init__(self):
        self.nonces={}; self.admissions={}; self.lock=threading.Lock()
    def claim(self,payload):
        a=payload["admission"]; aid=payload["admission_id"]; n=a["nonce"]
        with self.lock:
            if n in self.nonces or aid in self.admissions: return {"state":"REPLAY_DENIED","admission_id":aid}
            self.nonces[n]=aid; self.admissions[aid]=n
            return {"state":"CLAIMED","admission_id":aid,"nonce":n}

class V2(unittest.TestCase):
    def raw(self,t): return json.dumps(t)
    def test_fresh_first_claim_then_replay_denied(self):
        s=Store(); t=mk()
        out=consume_admission_v2(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",raw=self.raw(t),claim_fn=s.claim,now=NOW)
        self.assertEqual(out["replay_receipt"]["state"],"CLAIMED")
        with self.assertRaisesRegex(AdmissionDenied,"REPLAY"):
            consume_admission_v2(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",raw=self.raw(t),claim_fn=s.claim,now=NOW)
    def test_same_nonce_modified_payload_denied_before_claim_if_digest_stale(self):
        t=mk(); t["admission"]["task_id"]="OTHER"
        called=0
        def claim(_):
            nonlocal called; called+=1; return {"state":"CLAIMED"}
        with self.assertRaisesRegex(AdmissionDenied,"INTEGRITY"):
            consume_admission_v2(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",raw=self.raw(t),claim_fn=claim,now=NOW)
        self.assertEqual(called,0)
    def test_different_nonce_same_admission_id_denied_offline(self):
        t=mk(); t["admission"]["nonce"]="ffeeddccbbaa99887766554433221100"
        with self.assertRaisesRegex(AdmissionDenied,"INTEGRITY"):
            validate_admission_v2(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",raw=self.raw(t),now=NOW)
    def test_expired_future_ttl_scope_role_and_tamper(self):
        cases=[
          ({"issued_at":"2026-10-03T12:30:00+00:00","expires_at":"2026-10-03T12:40:00+00:00"},"EXPIRED"),
          ({"issued_at":"2026-10-03T13:02:00+00:00","expires_at":"2026-10-03T13:12:00+00:00"},"NOT_YET"),
          ({"issued_at":"2026-10-03T12:50:00+00:00","expires_at":"2026-10-03T13:06:00+00:00"},"TTL"),
        ]
        for o,msg in cases:
            with self.assertRaisesRegex(AdmissionDenied,msg):
                validate_admission_v2(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",raw=self.raw(mk(o)),now=NOW)
        with self.assertRaisesRegex(AdmissionDenied,"SURFACE"):
            validate_admission_v2(surface="DRIVE",operation="R020_FRAMEPACK_EXECUTION",raw=self.raw(mk()),now=NOW)
        with self.assertRaisesRegex(AdmissionDenied,"ROLE"):
            validate_admission_v2(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",role="OTHER",raw=self.raw(mk()),now=NOW)
    def test_timeout_unknown_no_blind_second_claim(self):
        calls=0
        def timeout(_):
            nonlocal calls; calls+=1; raise TimeoutError("timeout")
        with self.assertRaisesRegex(AdmissionUnknown,"UNKNOWN"):
            consume_admission_v2(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",raw=self.raw(mk()),claim_fn=timeout,now=NOW)
        self.assertEqual(calls,1)
    def test_crash_after_claim_consumes_token(self):
        s=Store(); t=mk(); s.claim({"admission_id":t["admission_id"],"admission":t["admission"]})
        with self.assertRaisesRegex(AdmissionDenied,"REPLAY"):
            consume_admission_v2(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",raw=self.raw(t),claim_fn=s.claim,now=NOW)
    def test_concurrent_duplicate_exactly_one_claimed(self):
        s=Store(); t=mk(); states=[]; lock=threading.Lock()
        def worker():
            state=s.claim({"admission_id":t["admission_id"],"admission":t["admission"]})["state"]
            with lock: states.append(state)
        threads=[threading.Thread(target=worker) for _ in range(24)]
        [x.start() for x in threads]; [x.join() for x in threads]
        self.assertEqual(states.count("CLAIMED"),1); self.assertEqual(states.count("REPLAY_DENIED"),23)
    def test_invalid_token_does_not_call_security_control(self):
        calls=0; t=mk({"surface":"DRIVE"})
        def claim(_):
            nonlocal calls; calls+=1; return {"state":"CLAIMED"}
        with self.assertRaisesRegex(AdmissionDenied,"SURFACE"):
            consume_admission_v2(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",raw=self.raw(t),claim_fn=claim,now=NOW)
        self.assertEqual(calls,0)

if __name__=="__main__": unittest.main()
