import hashlib,math,tempfile,unittest,wave
from array import array
from pathlib import Path
from audio_intelligence.real_media_boundary_extractor import frames,candidates
class X(unittest.TestCase):
 def test_detects_physical_discontinuity_without_equal_split(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.wav";sr=16000;a=array("h")
   for sec,amp,f in [(3,500,220),(3,5000,880),(3,900,330)]:
    for n in range(sec*sr):a.append(int(amp*math.sin(2*math.pi*f*n/sr)))
   with wave.open(str(p),"wb") as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(a.tobytes())
   cs=candidates(frames(str(p)),min_gap=1.5)
   top=sorted(cs,reverse=True)[:2];ts=sorted(x[2] for x in top)
   self.assertTrue(any(abs(t-3)<.5 for t in ts));self.assertTrue(any(abs(t-6)<.5 for t in ts))
 def test_hashes_are_physical_pcm(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.wav";a=array("h",[1,-1]*16000)
   with wave.open(str(p),"wb") as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(16000);w.writeframes(a.tobytes())
   fs=frames(str(p));self.assertEqual(len(fs[0][3]),64);self.assertNotEqual(fs[0][3],"0"*64)
if __name__=="__main__":unittest.main()
