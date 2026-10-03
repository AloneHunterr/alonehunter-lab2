import hashlib, unittest
from audio_intelligence.apex_runner import validate_transport_manifest,classify_terminal_receipt,reconcile_possible_submit,GateError
from governance.e104_e109_reconcile import receiver_pass_correction,resolve_receiver_by_resource_key,ReconcileError
H=lambda s: hashlib.sha256(s.encode()).hexdigest()

def pcm(): return [{"candidate_id":f"C{i:02d}","sha256":H(f"c{i}"),"bytes":100+i} for i in range(1,11)]
def manifest(kind="kaggle_task_path"):
 p=pcm(); return {"task_id":"ODIN","transport_kind":kind,"kaggle_task_path":"/kaggle/input/ah-odinokiy-c01-c10","lyrics_sha256":H("lyrics"),"ordered_pcm":[{**x,"compute_access_probe":{"readable":True,"observed_sha256":x["sha256"],"observed_bytes":x["bytes"],"compute_context":"kaggle-job-fixture"}} for x in p]}
LY={"authority_id":"DriveLyrics","sha256":H("lyrics")}
class Stabilization(unittest.TestCase):
 def test_t1_01_known_folder_admits_only_after_probe(self): self.assertEqual(validate_transport_manifest("ODIN",pcm(),LY,manifest())["transport_kind"],"kaggle_task_path")
 def test_t1_02_signed_url_rejected_before_scoring(self):
  m=manifest("signed_url"); m["signed_urls"]=["https://temp.invalid/x"]
  with self.assertRaises(GateError): validate_transport_manifest("ODIN",pcm(),LY,m)
 def test_t1_03_uncertain_submit_preserves_identity(self): self.assertEqual(reconcile_possible_submit({"provider_job_id":"K1"},[])["decision"],"PRESERVE_UNKNOWN__READBACK_REQUIRED")
 def test_t1_04_terminal_fail_has_no_top3(self): self.assertEqual(classify_terminal_receipt({"state":"TERMINAL_FAIL"}),"TERMINAL_FAIL")
 def test_t1_04_request_success_cannot_carry_top3(self):
  with self.assertRaises(GateError): classify_terminal_receipt({"state":"REQUEST_ACCEPTED","top3":[1,2,3]})
 def test_s1_01_visual_does_not_close_hq_gated_artifact(self):
  cur={"task_id":"S03","artifact_id":"D1","artifact_sha256":H("v"),"status":"QA_PENDING"}
  rec={**cur,"receiver":"Visual Studio V4","verdict":"VISUAL_QA_PASS","receipt_id":"H1"}
  self.assertIsNone(receiver_pass_correction(cur,rec))
 def test_s1_01_hq_emits_append_only_correction(self):
  cur={"task_id":"S03","artifact_id":"D1","artifact_sha256":H("v"),"status":"QA_PENDING"}
  rec={**cur,"receiver":"Producer HQ V4","verdict":"HQ_QA_PASS","receipt_id":"H2"}
  self.assertEqual(receiver_pass_correction(cur,rec)["mode"],"APPEND_ONLY_CORRECTION")
 def test_s1_wrong_sha_fails_closed(self):
  cur={"task_id":"S03","artifact_id":"D1","artifact_sha256":H("v"),"status":"QA_PENDING"}
  rec={**cur,"artifact_sha256":H("wrong"),"receiver":"Producer HQ V4","verdict":"HQ_QA_PASS"}
  with self.assertRaises(ReconcileError): receiver_pass_correction(cur,rec)
 def test_i1_01_resource_key_beats_similar_names(self):
  reg=[{"resource_key":"AH_AGENT_PROFILE_BIG_TECH","role_name":"Big Tech / TECH R&D V5","status":"CANONICAL_ACTIVE"},{"resource_key":"AH_AGENT_PROFILE_TECH","role_name":"Tech / Video Factory V5","status":"CANONICAL_ACTIVE"}]
  self.assertEqual(resolve_receiver_by_resource_key("AH_AGENT_PROFILE_BIG_TECH",reg)["role_name"],"Big Tech / TECH R&D V5")
 def test_i1_ambiguity_fails_closed(self):
  reg=[{"resource_key":"AH_AGENT_PROFILE_BIG_TECH","role_name":"A","status":"CANONICAL_ACTIVE"},{"resource_key":"AH_AGENT_PROFILE_BIG_TECH","role_name":"B","status":"CANONICAL_ACTIVE"}]
  with self.assertRaises(ReconcileError): resolve_receiver_by_resource_key("AH_AGENT_PROFILE_BIG_TECH",reg)
if __name__=="__main__": unittest.main()
