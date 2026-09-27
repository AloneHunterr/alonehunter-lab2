import hashlib,unittest
from audio_intelligence.apex_runner import *
H=lambda x: hashlib.sha256(x.encode()).hexdigest()
def src(n=3):return {"parts":[{"source_id":"D1","bytes":100,"sha256":H("s"),"duration_s":30,"candidate_count":n}]}
def good_join(t):return {"source_id":"D1","source_sha256":H("s"),"timestamp_s":t,"evidence_class":"player_transition_readback","before_frame_sha256":H("b"+str(t)),"after_frame_sha256":H("a"+str(t)),"readback_uri":"drive://proof/"+str(t),"player_reset_verified":True}
class T(unittest.TestCase):
 def test_reject_equal_split(self):
  b={"joins":[dict(good_join(10),evidence_class="equal_split"),good_join(20)]}
  with self.assertRaises(GateError):validate_boundaries(src(),b)
 def test_reject_hardcoded(self):
  b={"joins":[dict(good_join(10),evidence_class="hardcoded"),good_join(20)]}
  with self.assertRaises(GateError):validate_boundaries(src(),b)
 def test_accept_physical(self):validate_boundaries(src(),{"joins":[good_join(10),good_join(20)]})
 def test_missing_hash(self):
  j=good_join(10);j["after_frame_sha256"]=""
  with self.assertRaises(GateError):validate_boundaries(src(2),{"joins":[j]})
 def test_pcm_identity(self):
  with self.assertRaises(GateError):validate_pcm(src(2),[{"bytes":1,"duration_s":1,"sha256":H("x")},{"bytes":0,"duration_s":1,"sha256":H("y")}])
 def test_config_idempotent(self):
  b={"joins":[good_join(10),good_join(20)]};ly={"authority_id":"owner-v1","sha256":H("lyrics")}
  a=durable_config("T",src(),ly,b,"m1","f1");c=durable_config("T",src(),ly,b,"m1","f1");self.assertEqual(a["idempotency_key"],c["idempotency_key"])
 def test_resume(self):
  b={"joins":[good_join(10),good_join(20)]};cfg=durable_config("T",src(),{"authority_id":"L","sha256":H("l")},b,"m","f")
  r=[{"stage":"SOURCE_VERIFIED","idempotency_key":cfg["idempotency_key"],"artifact_sha256":H("r")}]
  self.assertEqual(reconcile_stage(r,cfg),"BOUNDARIES_VERIFIED")
 def test_mismatch_fails(self):
  b={"joins":[good_join(10),good_join(20)]};cfg=durable_config("T",src(),{"authority_id":"L","sha256":H("l")},b,"m","f")
  with self.assertRaises(GateError):reconcile_stage([{"stage":"SOURCE_VERIFIED","idempotency_key":H("wrong"),"artifact_sha256":H("r")}],cfg)
if __name__=="__main__":unittest.main()
