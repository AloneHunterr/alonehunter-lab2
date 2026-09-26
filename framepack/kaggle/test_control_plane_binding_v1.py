#!/usr/bin/env python3
import hashlib, json, os, subprocess, sys, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from control_plane_v1 import require_admission, AdmissionDenied, GATEWAY_VERSION, CONTROL_PLANE_VERSION

def token(surface, operation):
    admission={
        "gateway_version":GATEWAY_VERSION,
        "control_plane_version":CONTROL_PLANE_VERSION,
        "surface":surface,
        "operation":operation,
        "role":"BIG_TECH_TECH_RND",
        "task_id":"AH_EXECUTION_CONTROL_PLANE_RUNTIME_BINDING_CLOSURE_20260921",
        "issued_at":"2026-09-26T00:00:00.000Z",
        "evidence_digest":"test"
    }
    stable=json.dumps(dict(sorted(admission.items())),separators=(",",":"),ensure_ascii=False)
    return {"admission":admission,"admission_id":hashlib.sha256(stable.encode()).hexdigest()}

class ControlPlaneBindingTest(unittest.TestCase):
    def test_missing_token_fails_closed(self):
        old=os.environ.pop("AH_EXECUTION_ADMISSION_TOKEN_KAGGLE",None)
        try:
            with self.assertRaisesRegex(AdmissionDenied,"ADMISSION_TOKEN_REQUIRED"):
                require_admission(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION")
        finally:
            if old is not None: os.environ["AH_EXECUTION_ADMISSION_TOKEN_KAGGLE"]=old

    def test_valid_scoped_token_passes(self):
        raw=json.dumps(token("KAGGLE","R020_FRAMEPACK_EXECUTION"))
        self.assertEqual(require_admission(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",raw=raw)["admission"]["role"],"BIG_TECH_TECH_RND")

    def test_tampered_token_fails(self):
        t=token("KAGGLE","R020_FRAMEPACK_EXECUTION")
        t["admission"]["operation"]="OTHER"
        with self.assertRaisesRegex(AdmissionDenied,"ADMISSION_OPERATION_MISMATCH"):
            require_admission(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",raw=json.dumps(t))

    def test_real_r020_bootstrap_cannot_reach_ingress_without_token(self):
        env=os.environ.copy()
        env.pop("AH_EXECUTION_ADMISSION_TOKEN",None)
        env.pop("AH_EXECUTION_ADMISSION_TOKEN_KAGGLE",None)
        p=subprocess.run([sys.executable,str(HERE/"inference_bootstrap_delivery_v2.py")],env=env,text=True,capture_output=True,timeout=20)
        self.assertNotEqual(p.returncode,0)
        combined=p.stdout+p.stderr
        self.assertIn("ADMISSION_TOKEN_REQUIRED",combined)
        self.assertNotIn("canonical_source_size_mismatch",combined)

if __name__=="__main__":
    unittest.main()
