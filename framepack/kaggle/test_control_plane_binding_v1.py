#!/usr/bin/env python3
import ast, hashlib, json, os, subprocess, sys, unittest
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

    def test_invalid_json_denied(self):
        with self.assertRaisesRegex(AdmissionDenied,"ADMISSION_TOKEN_INVALID_JSON"):
            require_admission(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",raw="{bad")

    def test_surface_and_operation_are_strictly_scoped(self):
        raw=json.dumps(token("KAGGLE","R020_FRAMEPACK_EXECUTION"))
        with self.assertRaisesRegex(AdmissionDenied,"ADMISSION_SURFACE_MISMATCH"):
            require_admission(surface="DRIVE",operation="R020_FRAMEPACK_EXECUTION",raw=raw)
        with self.assertRaisesRegex(AdmissionDenied,"ADMISSION_OPERATION_MISMATCH"):
            require_admission(surface="KAGGLE",operation="OTHER",raw=raw)

    def test_make_callback_cannot_use_kaggle_admission(self):
        raw=json.dumps(token("KAGGLE","R020_FRAMEPACK_EXECUTION"))
        with self.assertRaisesRegex(AdmissionDenied,"ADMISSION_SURFACE_MISMATCH"):
            require_admission(surface="MAKE",operation="FRAMEPACK_CALLBACK",raw=raw)

    def test_drive_delivery_cannot_use_kaggle_admission(self):
        raw=json.dumps(token("KAGGLE","R020_FRAMEPACK_EXECUTION"))
        with self.assertRaisesRegex(AdmissionDenied,"ADMISSION_SURFACE_MISMATCH"):
            require_admission(surface="DRIVE",operation="FRAMEPACK_ARTIFACT_DELIVERY",raw=raw)

    def test_callback_and_delivery_require_own_valid_admissions(self):
        self.assertTrue(require_admission(surface="MAKE",operation="FRAMEPACK_CALLBACK",raw=json.dumps(token("MAKE","FRAMEPACK_CALLBACK"))))
        self.assertTrue(require_admission(surface="DRIVE",operation="FRAMEPACK_ARTIFACT_DELIVERY",raw=json.dumps(token("DRIVE","FRAMEPACK_ARTIFACT_DELIVERY"))))

    def test_runtime_mutation_calls_are_dominated_by_admission_checks(self):
        tree=ast.parse((HERE/"framepack_inference.py").read_text())
        funcs={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        for name,needle in [("callback","MAKE"),("direct_drive_upload","DRIVE")]:
            fn=funcs[name]
            calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call)]
            gate_lines=[n.lineno for n in calls if isinstance(n.func,ast.Name) and n.func.id=="require_admission"]
            side_lines=[n.lineno for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr in {"post","put","request","urlopen"}]
            self.assertTrue(gate_lines, f"{name} missing admission gate")
            self.assertTrue(side_lines, f"{name} missing expected side effect call")
            self.assertLess(min(gate_lines),min(side_lines),f"{name} side effect precedes admission")

    def test_no_unguarded_http_mutation_outside_gated_functions(self):
        tree=ast.parse((HERE/"framepack_inference.py").read_text())
        parent={}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node): parent[child]=node
        allowed={"callback","direct_drive_upload"}
        offenders=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in {"post","put","request","urlopen"}:
                p=n
                while p in parent and not isinstance(p,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    p=parent[p]
                if not isinstance(p,(ast.FunctionDef,ast.AsyncFunctionDef)) or p.name not in allowed:
                    offenders.append((getattr(n,"lineno",0),getattr(p,"name","<module>")))
        self.assertEqual(offenders,[])

    def test_replay_not_claimed_by_canonical_v1(self):
        # Canonical requireAdmissionToken V1 has integrity/scope checks only.
        # Replay/freshness is therefore NOT an implemented acceptance property.
        raw=json.dumps(token("KAGGLE","R020_FRAMEPACK_EXECUTION"))
        require_admission(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",raw=raw)
        require_admission(surface="KAGGLE",operation="R020_FRAMEPACK_EXECUTION",raw=raw)

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
