#!/usr/bin/env python3
"""Code-only T01-T11/T14-T15 gate for additive Replay V2 caller binding."""
from __future__ import annotations
import inspect, json, os, pathlib, unittest
from datetime import datetime, timezone

import control_plane_v2 as cp
import framepack_inference_v2_microproof as rt

NOW=datetime(2026,10,4,13,0,0,tzinfo=timezone.utc)

def mk(overrides=None, *, issuer_mac="trusted-mac"):
    a={
        "gateway_version":cp.GATEWAY_VERSION,
        "control_plane_version":cp.CONTROL_PLANE_VERSION,
        "surface":"KAGGLE",
        "operation":"R020_FRAMEPACK_EXECUTION",
        "role":cp.ROLE,
        "task_id":rt.TASK_ID,
        "issued_at":"2026-10-04T12:55:00+00:00",
        "expires_at":"2026-10-04T13:10:00+00:00",
        "nonce":"00112233445566778899aabbccddeeff",
        "evidence_digest":"code-only-microproof",
        "issuer_id":"TEST_ISSUER",
    }
    a.update(overrides or {})
    return {"admission":a,"admission_id":cp._digest(a),"issuer_mac":issuer_mac}

def raw(token):
    return json.dumps(token,separators=(",",":"))

class Sentinel:
    def __init__(self): self.count=0
    def __call__(self, receipt):
        self.count+=1
        return {"count":self.count,"admission_id":receipt["admission_id"]}

class TrustedClaims:
    def __init__(self): self.seen=set()
    def claim(self,payload):
        a=payload["admission"]; aid=payload["admission_id"]; nonce=a["nonce"]
        if payload.get("issuer_mac")!="trusted-mac":
            return {"state":"DENIED","decision":"ISSUER_AUTHENTICATION_FAILURE","admission_id":aid,"nonce":nonce}
        key=(aid,nonce)
        if key in self.seen:
            return {"state":"REPLAY_DENIED","admission_id":aid,"nonce":nonce}
        self.seen.add(key)
        return {"state":"CLAIMED","admission_id":aid,"nonce":nonce}

class CallerBinding(unittest.TestCase):
    def run(self, token, claim, sentinel, *, now=NOW):
        return rt.run_microproof(raw=raw(token) if token is not None else None,claim_fn=claim,now=now,target_fn=sentinel)

    def test_T01_missing_token_zero_target(self):
        s=Sentinel()
        old={k:os.environ.pop(k,None) for k in ("AH_EXECUTION_ADMISSION_TOKEN_KAGGLE","AH_EXECUTION_ADMISSION_TOKEN")}
        try:
            with self.assertRaisesRegex(cp.AdmissionDenied,"TOKEN_REQUIRED"):
                self.run(None,TrustedClaims().claim,s)
            self.assertEqual(s.count,0)
        finally:
            for k,v in old.items():
                if v is not None: os.environ[k]=v

    def test_T02_malformed_token_zero_target(self):
        s=Sentinel()
        with self.assertRaises(cp.AdmissionDenied):
            rt.run_microproof(raw="{bad-json",claim_fn=TrustedClaims().claim,now=NOW,target_fn=s)
        self.assertEqual(s.count,0)

    def test_T03_wrong_task_zero_target(self):
        s=Sentinel()
        with self.assertRaisesRegex(cp.AdmissionDenied,"TASK"):
            self.run(mk({"task_id":"OTHER_TASK"}),TrustedClaims().claim,s)
        self.assertEqual(s.count,0)

    def test_T04_expired_zero_target(self):
        s=Sentinel()
        t=mk({"issued_at":"2026-10-04T12:00:00+00:00","expires_at":"2026-10-04T12:10:00+00:00"})
        with self.assertRaisesRegex(cp.AdmissionDenied,"EXPIRED"):
            self.run(t,TrustedClaims().claim,s)
        self.assertEqual(s.count,0)

    def test_T05_future_zero_target(self):
        s=Sentinel()
        t=mk({"issued_at":"2026-10-04T13:05:00+00:00","expires_at":"2026-10-04T13:10:00+00:00"})
        with self.assertRaisesRegex(cp.AdmissionDenied,"NOT_YET_VALID"):
            self.run(t,TrustedClaims().claim,s)
        self.assertEqual(s.count,0)

    def test_T06_missing_claim_config_unknown_zero_target(self):
        s=Sentinel()
        old={k:os.environ.pop(k,None) for k in ("AH_EXECUTION_ADMISSION_CLAIM_URL","AH_EXECUTION_ADMISSION_CLAIM_KEY")}
        try:
            with self.assertRaises(cp.AdmissionUnknown):
                self.run(mk(),cp.claim_replay_http,s)
            self.assertEqual(s.count,0)
        finally:
            for k,v in old.items():
                if v is not None: os.environ[k]=v

    def test_T07_forged_denied_zero_target(self):
        s=Sentinel()
        with self.assertRaisesRegex(cp.AdmissionDenied,"ISSUER_AUTHENTICATION_FAILURE"):
            self.run(mk(issuer_mac="forged"),TrustedClaims().claim,s)
        self.assertEqual(s.count,0)

    def test_T08_crosswired_claim_unknown_zero_target(self):
        s=Sentinel()
        with self.assertRaisesRegex(cp.AdmissionUnknown,"IDENTITY"):
            self.run(mk(),lambda p:{"state":"CLAIMED","admission_id":"wrong","nonce":"wrong"},s)
        self.assertEqual(s.count,0)

    def test_T09_claim_timeout_unknown_zero_target(self):
        s=Sentinel()
        def timeout(_): raise TimeoutError("simulated")
        with self.assertRaises(cp.AdmissionUnknown):
            self.run(mk(),timeout,s)
        self.assertEqual(s.count,0)

    def test_T10_valid_claim_target_exactly_once(self):
        s=Sentinel(); claims=TrustedClaims()
        out=self.run(mk(),claims.claim,s)
        self.assertEqual(s.count,1)
        self.assertEqual(out["count"],1)

    def test_T11_replay_zero_second_target(self):
        s=Sentinel(); claims=TrustedClaims(); token=mk()
        self.run(token,claims.claim,s)
        self.assertEqual(s.count,1)
        with self.assertRaisesRegex(cp.AdmissionDenied,"REPLAY"):
            self.run(token,claims.claim,s)
        self.assertEqual(s.count,1)

    def test_T14_no_issuer_verifier_secret_capability(self):
        source=inspect.getsource(cp)+"\n"+inspect.getsource(rt)
        self.assertNotIn("AH_EXECUTION_ADMISSION_VERIFY_KEY_V2",source)
        self.assertNotIn("EXECUTION_ADMISSION_CLAIM_SECRET",source)
        self.assertNotIn("import hmac",source)
        self.assertNotIn("verifier_key",source)

    def test_T15_generated_bootstrap_v2_identity_and_target(self):
        h=pathlib.Path(__file__).resolve().parent
        generated=(h/"inference_bootstrap_v2_generated.py").read_text(encoding="utf-8")
        self.assertIn('VERIFIER_VERSION="EXECUTION_CONTROL_PLANE_V2"',generated)
        self.assertIn('WORK/"control_plane_v2.py"',generated)
        self.assertIn("EMBEDDED_V2_CONSUMER_HASH_MISMATCH",generated)
        self.assertIn("V2_RUNTIME_HASH_MISMATCH",generated)
        self.assertIn('WORK/"framepack_inference_v2_microproof.py"',generated)
        self.assertIn("/framepack/kaggle/framepack_inference_v2_microproof.py",generated)
        self.assertNotIn('WORK/"control_plane_v1.py"',generated)
        self.assertNotIn('WORK/"framepack_inference.py"',generated)

if __name__=="__main__":
    unittest.main()
