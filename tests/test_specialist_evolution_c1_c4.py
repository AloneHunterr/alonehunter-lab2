import unittest
from specialist_evolution.c1_c4 import *
class Eval(unittest.TestCase):
 def test_c1_e01_02_03_04_05_11_13_17_19(self):
  old={"id":"R13","family":"visual","timestamp":"2026-09-20","row":13,"current":True}
  new={"id":"R15","family":"visual","timestamp":"2026-09-21","row":15,"current":True,"supersedes":"R13"}
  self.assertEqual(current_authority_view([old,new])["authority"]["id"],"R15")
  self.assertEqual(current_authority_view([old],scan_complete=False)["state"],UNKNOWN)
 def test_c2_e09_10_13_15_16_20(self):
  i={"task_id":"T1","receipt_id":"R1","artifact_id":"A1"}; j={"task_id":"T1","receipt_id":"R1","artifact_id":"A2"}
  self.assertFalse(validate_transition("PRODUCED","RECEIVER_ACCEPTED",{"receiver_acceptance":True,**i}))
  self.assertTrue(validate_transition("PRODUCED","PHYSICAL_READBACK",{"artifact_readback":True,**i}))
  self.assertFalse(validate_transition("PHYSICAL_READBACK","RECEIVER_DISCOVERED",i))
  self.assertTrue(validate_transition("PHYSICAL_READBACK","RECEIVER_DISCOVERED",{"receiver_discovery":True,**i},i))
  self.assertFalse(validate_transition("RECEIVER_DISCOVERED","RECEIVER_ACCEPTED",{"receiver_acceptance":True,**j},i))
  self.assertTrue(validate_transition("RECEIVER_DISCOVERED","RECEIVER_ACCEPTED",{"receiver_acceptance":True,**i},i))
  self.assertFalse(validate_transition("RECEIVER_ACCEPTED","HQ_ACCEPTED",{"hq_acceptance":True,**j},i))
  self.assertTrue(validate_transition("RECEIVER_ACCEPTED","HQ_ACCEPTED",{"hq_acceptance":True,**i},i))
 def test_c3_e06_07_12_14_19(self):
  self.assertEqual(validate_claim_scope("PROVIDER_RESULT_VERIFIED",{"request":True}),"UNKNOWN")
  self.assertEqual(validate_claim_scope("PERCEPTUAL_HEARD",{"machine_top1":True}),"UNKNOWN")
  self.assertEqual(validate_claim_scope("BUILD_PASS",{"build":True}),"BUILD_PASS")
  legacy={"receipt_id":"old","status":"SUCCESS"}
  self.assertTrue(validate_terminal_receipt(legacy,{})["legacy"]); self.assertEqual(validate_terminal_receipt(legacy,{})["status"],"SUCCESS")
  over={"receipt_id":"n1","status":"SUCCESS","claim_scope":"PROVIDER_RESULT_VERIFIED"}
  self.assertFalse(validate_terminal_receipt(over,{"build":True})["valid"]); self.assertFalse(validate_terminal_receipt(over,{"request":True})["valid"]); self.assertTrue(validate_terminal_receipt(over,{"provider_result":True})["valid"])
  pub={"receipt_id":"n2","status":"SUCCESS","claim_scope":"PUBLISHED"}
  self.assertFalse(validate_terminal_receipt(pub,{"provider_result":True})["valid"]); self.assertTrue(validate_terminal_receipt(pub,{"publication":True})["valid"])
 def test_c4_e17_18(self):
  rows=[{"row":140,"scenario_id":6116180,"function_key":"KAGGLE_TERMINAL_RECEIPT_READBACK","verified_at":"2026-09-20"},{"row":163,"scenario_id":6116180,"function_key":"KAGGLE_TERMINAL_RECEIPT_READBACK","verified_at":"2026-09-21"}]
  x=resolve_registry(rows)[0]
  self.assertEqual(x["state"],"REGISTRY_DUPLICATE_IDENTITY"); self.assertEqual(len(x["references"]),2); self.assertEqual(x["identity"],("6116180","KAGGLE_TERMINAL_RECEIPT_READBACK"))
if __name__=="__main__": unittest.main()
