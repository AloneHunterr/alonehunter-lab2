#!/usr/bin/env python3
import copy,hashlib,hmac,inspect,json,threading,unittest
from datetime import datetime,timezone
import control_plane_v2
from control_plane_v2 import *
from control_plane_v2 import _digest, _stable

NOW=datetime(2026,10,3,13,0,0,tzinfo=timezone.utc)
KEY="0123456789abcdef0123456789abcdef"
TASK="AH_EXECUTION_ADMISSION_REPLAY_HARDENING_20260926"

def sign(value):
    return hmac.new(KEY.encode(),_stable(value).encode(),hashlib.sha256).hexdigest()

def mk(overrides=None):
    a={
        "gateway_version":GATEWAY_VERSION,"control_plane_version":CONTROL_PLANE_VERSION,
        "surface":"KAGGLE","operation":"R020_FRAMEPACK_EXECUTION","role":ROLE,"task_id":TASK,
        "issued_at":"2026-10-03T12:55:00+00:00","expires_at":"2026-10-03T13:10:00+00:00",
        "nonce":"00112233445566778899aabbccddeeff","evidence_digest":"evidence","issuer_id":"TEST_ISSUER"
    }
    a.update(overrides or {})
    aid=_digest(a)
    return {"admission":a,"admission_id":aid,"issuer_mac":sign({"admission_id":aid,"admission":a})}

class TrustedStore:
    def __init__(self):
        self.nonces={}; self.admissions={}; self.lock=threading.Lock()
    def claim(self,p):
        a=p["admission"]; aid=p["admission_id"]; n=a["nonce"]
        want=sign({"admission_id":aid,"admission":a})
        if not hmac.compare_digest(want,str(p.get("issuer_mac") or "")):
            return {"state":"DENIED","decision":"ISSUER_AUTHENTICATION_FAILURE","admission_id":aid,"nonce":n}
        with self.lock:
            if n in self.nonces or aid in self.admissions:
                return {"state":"REPLAY_DENIED","admission_id":aid,"nonce":n}
            self.nonces[n]=aid; self.admissions[aid]=n
            return {"state":"CLAIMED","admission_id":aid,"nonce":n}

class V2(unittest.TestCase):
    def raw(self,t): return json.dumps(t)
    def validate(self,t,**kw):
        return validate_admission_v2(
            surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",task_id=TASK,
            raw=self.raw(t),now=NOW,**kw
        )
    def consume(self,t,claim,**kw):
        return consume_admission_v2(
            surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",task_id=TASK,
            raw=self.raw(t),claim_fn=claim,now=NOW,**kw
        )

    def test_workload_has_no_issuer_verifier_secret_capability(self):
        source=inspect.getsource(control_plane_v2)
        self.assertNotIn("AH_EXECUTION_ADMISSION_VERIFY_KEY_V2",source)
        self.assertNotIn("import hmac",source)
        self.assertNotIn("def _mac",source)
        self.assertNotIn("verifier_key",source)

    def test_recursive_nested_digest(self):
        self.assertNotEqual(_digest({"a":{"x":1,"y":2}}),_digest({"a":{"x":1,"y":3}}))

    def test_local_validation_is_not_authenticity_authority(self):
        out=self.validate(mk())
        self.assertEqual(out["authenticity"],"PENDING_TRUSTED_CONTROL_PLANE_CLAIM")

    def test_fresh_authenticated_claim(self):
        s=TrustedStore()
        out=self.consume(mk(),s.claim)
        self.assertEqual(out["replay_receipt"]["state"],"CLAIMED")
        self.assertEqual(out["authenticity"],"TRUSTED_CONTROL_PLANE_CLAIMED")

    def test_forged_fresh_token_reaches_local_integrity_but_trusted_claim_denies(self):
        t=mk()
        t["admission"]["nonce"]="ffeeddccbbaa99887766554433221100"
        t["admission_id"]=_digest(t["admission"])
        self.assertEqual(self.validate(t)["authenticity"],"PENDING_TRUSTED_CONTROL_PLANE_CLAIM")
        with self.assertRaisesRegex(AdmissionDenied,"ISSUER_AUTHENTICATION_FAILURE"):
            self.consume(t,TrustedStore().claim)

    def test_cross_task_denied_locally(self):
        with self.assertRaisesRegex(AdmissionDenied,"TASK"):
            self.validate(mk({"task_id":"OTHER"}))

    def test_mutated_after_verify_uses_snapshot(self):
        t=mk(); seen=[]
        store=TrustedStore()
        def claim(p):
            t["admission"]["task_id"]="MUTATED"
            return store.claim(p)
        out=self.consume(t,claim)
        seen.append(out["admission"]["task_id"])
        self.assertEqual(seen,[TASK])

    def test_claim_payload_carries_issuer_mac_but_not_verifier_key(self):
        t=mk(); seen={}
        store=TrustedStore()
        def claim(p):
            seen.update(p)
            return store.claim(p)
        out=self.consume(t,claim)
        self.assertEqual(out["replay_receipt"]["state"],"CLAIMED")
        self.assertEqual(seen["issuer_mac"],t["issuer_mac"])
        self.assertNotIn("verifier_key",seen)

    def test_crosswired_claim_receipt_unknown(self):
        with self.assertRaisesRegex(AdmissionUnknown,"IDENTITY"):
            self.consume(mk(),lambda p:{
                "state":"CLAIMED","admission_id":"wrong","nonce":"wrong"
            })

    def test_invalid_clock_inputs(self):
        with self.assertRaisesRegex(AdmissionDenied,"CLOCK"):
            self.consume(mk(),TrustedStore().claim,clock_skew_seconds=float("nan"))
        with self.assertRaisesRegex(AdmissionDenied,"CLOCK"):
            self.consume(mk(),TrustedStore().claim,clock_skew_seconds=-1)

    def test_concurrent_duplicate_exactly_one(self):
        s=TrustedStore(); t=mk(); states=[]; lock=threading.Lock()
        p={"admission_id":t["admission_id"],"admission":copy.deepcopy(t["admission"]),"issuer_mac":t["issuer_mac"]}
        def w():
            st=s.claim(copy.deepcopy(p))["state"]
            with lock: states.append(st)
        th=[threading.Thread(target=w) for _ in range(24)]
        [x.start() for x in th]; [x.join() for x in th]
        self.assertEqual(states.count("CLAIMED"),1)
        self.assertEqual(states.count("REPLAY_DENIED"),23)

if __name__=="__main__":
    unittest.main()
