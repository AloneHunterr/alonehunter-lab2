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

    def _run_delivery_finalizer(self, raw=None):
        env=os.environ.copy()
        env["AH_DRIVE_UPLOAD_URL"]="https://example.invalid/upload"
        env.pop("AH_EXECUTION_ADMISSION_TOKEN",None)
        env.pop("AH_EXECUTION_ADMISSION_TOKEN_DRIVE",None)
        if raw is not None:
            env["AH_EXECUTION_ADMISSION_TOKEN_DRIVE"]=raw
        return subprocess.run([sys.executable,str(HERE/"delivery_finalizer.py")],env=env,text=True,capture_output=True,timeout=20)

    def test_delivery_finalizer_missing_admission_denied_before_network_or_manifest(self):
        p=self._run_delivery_finalizer()
        self.assertNotEqual(p.returncode,0)
        combined=p.stdout+p.stderr
        self.assertIn("ADMISSION_TOKEN_REQUIRED",combined)
        self.assertNotIn("manifest not mounted",combined)

    def test_delivery_finalizer_invalid_tampered_and_wrong_scope_denied(self):
        cases=[
            ("{bad","ADMISSION_TOKEN_INVALID_JSON"),
            (json.dumps(token("KAGGLE","FRAMEPACK_ARTIFACT_DELIVERY")),"ADMISSION_SURFACE_MISMATCH"),
            (json.dumps(token("DRIVE","OTHER")),"ADMISSION_OPERATION_MISMATCH"),
        ]
        wrong_role=token("DRIVE","FRAMEPACK_ARTIFACT_DELIVERY")
        wrong_role["admission"]["role"]="TECH_VIDEO_FACTORY"
        stable=json.dumps(dict(sorted(wrong_role["admission"].items())),separators=(",",":"),ensure_ascii=False)
        wrong_role["admission_id"]=hashlib.sha256(stable.encode()).hexdigest()
        cases.append((json.dumps(wrong_role),"ADMISSION_ROLE_MISMATCH"))
        tampered=token("DRIVE","FRAMEPACK_ARTIFACT_DELIVERY")
        tampered["admission"]["evidence_digest"]="tampered"
        cases.append((json.dumps(tampered),"ADMISSION_INTEGRITY_FAILURE"))
        for raw,reason in cases:
            with self.subTest(reason=reason):
                p=self._run_delivery_finalizer(raw)
                self.assertNotEqual(p.returncode,0)
                combined=p.stdout+p.stderr
                self.assertIn(reason,combined)
                self.assertNotIn("manifest not mounted",combined)

    def test_delivery_finalizer_valid_scope_passes_gate_then_stops_at_local_preflight(self):
        p=self._run_delivery_finalizer(json.dumps(token("DRIVE","FRAMEPACK_ARTIFACT_DELIVERY")))
        self.assertNotEqual(p.returncode,0)
        combined=p.stdout+p.stderr
        self.assertIn("manifest not mounted",combined)
        self.assertNotIn("ADMISSION_",combined)

    def test_delivery_finalizer_all_network_calls_are_after_module_gate(self):
        tree=ast.parse((HERE/"delivery_finalizer.py").read_text())
        gate_lines=[]
        network_lines=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.Call):
                if isinstance(n.func,ast.Name) and n.func.id=="require_admission":
                    gate_lines.append(n.lineno)
                if isinstance(n.func,ast.Attribute) and n.func.attr in {"urlopen","post","put","request"}:
                    network_lines.append(n.lineno)
        self.assertTrue(gate_lines)
        self.assertTrue(network_lines)
        self.assertLess(min(gate_lines),min(network_lines))
        self.assertEqual(len(gate_lines),1)
        # The finalizer has a single network mutation route; every branch reaches it only after module gate.
        self.assertEqual(len(network_lines),1)

    def _run_generated(self, raw=None, path=None):
        target=path or (HERE/"inference_bootstrap_generated.py")
        env=os.environ.copy()
        env["AH_KAGGLE_WORKING"]="/tmp/ah-kaggle-working-test"
        env.pop("AH_EXECUTION_ADMISSION_TOKEN",None); env.pop("AH_EXECUTION_ADMISSION_TOKEN_KAGGLE",None)
        if raw is not None: env["AH_EXECUTION_ADMISSION_TOKEN_KAGGLE"]=raw
        harness="import runpy,urllib.request;\nclass S(Exception): pass\ndef sent(*a,**k): print('NETWORK_SENTINEL_CALLED'); raise S('NETWORK_SENTINEL')\nurllib.request.urlopen=sent\nrunpy.run_path("+repr(str(target))+",run_name='__main__')"
        return subprocess.run([sys.executable,"-c",harness],env=env,text=True,capture_output=True,timeout=20)

    def test_generated_bootstrap_denials_are_zero_network(self):
        cases=[(None,"ADMISSION_TOKEN_REQUIRED"),("{bad","ADMISSION_TOKEN_INVALID_JSON")]
        for surf,op,role,reason in [
            ("DRIVE","R020_FRAMEPACK_EXECUTION","BIG_TECH_TECH_RND","ADMISSION_SURFACE_MISMATCH"),
            ("KAGGLE","OTHER","BIG_TECH_TECH_RND","ADMISSION_OPERATION_MISMATCH"),
            ("KAGGLE","R020_FRAMEPACK_EXECUTION","TECH_VIDEO_FACTORY","ADMISSION_ROLE_MISMATCH")]:
            t=token(surf,op); t["admission"]["role"]=role
            stable=json.dumps(dict(sorted(t["admission"].items())),separators=(",",":"),ensure_ascii=False); t["admission_id"]=hashlib.sha256(stable.encode()).hexdigest()
            cases.append((json.dumps(t),reason))
        tam=token("KAGGLE","R020_FRAMEPACK_EXECUTION"); tam["admission"]["evidence_digest"]="tampered"; cases.append((json.dumps(tam),"ADMISSION_INTEGRITY_FAILURE"))
        for raw,reason in cases:
            p=self._run_generated(raw); out=p.stdout+p.stderr
            self.assertNotEqual(p.returncode,0); self.assertIn(reason,out); self.assertNotIn("NETWORK_SENTINEL_CALLED",out)

    def test_generated_bootstrap_valid_admission_allows_network_only_after_gate(self):
        p=self._run_generated(json.dumps(token("KAGGLE","R020_FRAMEPACK_EXECUTION"))); out=p.stdout+p.stderr
        self.assertNotEqual(p.returncode,0); self.assertIn("NETWORK_SENTINEL_CALLED",out); self.assertIn("NETWORK_SENTINEL",out)

    def test_generated_bootstrap_embedded_integrity_failures_are_zero_network(self):
        src=(HERE/"inference_bootstrap_generated.py").read_text()
        variants=[
            src.replace("Fail-closed Python binding","Tampered Python binding",1),
            src.replace('VERIFIER_SHA256="','VERIFIER_SHA256="00',1),
        ]
        import tempfile
        for body in variants:
            with tempfile.NamedTemporaryFile("w",suffix=".py",delete=False) as q:
                q.write(body); path=q.name
            try:
                p=self._run_generated(json.dumps(token("KAGGLE","R020_FRAMEPACK_EXECUTION")),path); out=p.stdout+p.stderr
                self.assertNotEqual(p.returncode,0); self.assertIn("EMBEDDED_VERIFIER_HASH_MISMATCH",out); self.assertNotIn("NETWORK_SENTINEL_CALLED",out)
            finally: os.unlink(path)

    def test_generated_artifact_binding_matches_authoritative_verifier(self):
        import re
        src=(HERE/"inference_bootstrap_generated.py").read_text(); verifier=(HERE/"control_plane_v1.py").read_text()
        sha=re.search(r'^VERIFIER_SHA256="([0-9a-f]{64})"',src,re.M).group(1)
        ver=re.search(r'^VERIFIER_VERSION="([^"]+)"',src,re.M).group(1)
        commit=re.search(r'^SOURCE_COMMIT="([0-9a-f]{40})"',src,re.M).group(1)
        self.assertEqual(sha,hashlib.sha256(verifier.encode()).hexdigest())
        self.assertEqual(ver,CONTROL_PLANE_VERSION); self.assertRegex(commit,r"^[0-9a-f]{40}$")
        tree=ast.parse(src); calls=[n.lineno for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="urlopen"]
        gates=[n.lineno for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="require_admission"]
        self.assertTrue(calls and gates); self.assertLess(min(gates),min(calls))

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

    def test_legacy_bootstraps_are_retired_fail_closed(self):
        for name in ["inference_bootstrap.py","inference_bootstrap_delivery_v2.py"]:
            p=subprocess.run([sys.executable,str(HERE/name)],text=True,capture_output=True,timeout=20)
            out=p.stdout+p.stderr
            self.assertNotEqual(p.returncode,0); self.assertIn("LEGACY_BOOTSTRAP_DISABLED",out)
            self.assertNotIn("urlopen", (HERE/name).read_text())

    def test_malformed_generated_artifact_fails_before_network(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w",suffix=".py",delete=False) as q:
            q.write("this is not valid python !!!"); path=q.name
        try:
            p=self._run_generated(json.dumps(token("KAGGLE","R020_FRAMEPACK_EXECUTION")),path)
            self.assertNotEqual(p.returncode,0); self.assertNotIn("NETWORK_SENTINEL_CALLED",p.stdout+p.stderr)
        finally: os.unlink(path)

if __name__=="__main__":
    unittest.main()
