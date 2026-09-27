import math,tempfile,unittest,wave
from array import array
from pathlib import Path
from unittest.mock import patch
from audio_intelligence.multimodal_boundary_verifier import verify
class M(unittest.TestCase):
 def makewav(self,p):
  sr=16000;a=array("h")
  for sec,amp,f in [(3,500,220),(3,6000,880),(3,800,330)]:
   for n in range(sec*sr):a.append(int(amp*math.sin(2*math.pi*f*n/sr)))
  with wave.open(str(p),"wb") as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(a.tobytes())
 def test_requires_independent_video_evidence(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.wav";self.makewav(p)
   with patch("audio_intelligence.multimodal_boundary_verifier.video_scene_times",return_value=[]):
    with self.assertRaises(RuntimeError):verify(str(p),3,Path(d)/"o")
 def test_multimodal_yields_pcm_and_readback(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.wav";self.makewav(p)
   with patch("audio_intelligence.multimodal_boundary_verifier.video_scene_times",return_value=[3.0,6.0]):
    m=verify(str(p),3,Path(d)/"o",1.0)
   self.assertEqual(len(m["joins"]),2);self.assertEqual(len(m["pcm"]),3)
   self.assertTrue(all(j["player_reset_verified"] and j["readback_uri"].startswith("manifest://") for j in m["joins"]))
   self.assertTrue(all(x["bytes"]>0 and len(x["sha256"])==64 for x in m["pcm"]))
if __name__=="__main__":unittest.main()
