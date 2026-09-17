import subprocess,sys,urllib.request
from pathlib import Path
u='https://raw.githubusercontent.com/AloneHunterr/alonehunter-lab2/main/framepack/kaggle/r020_shot001_inference_v1.py';p=Path('/kaggle/working/r020_shot001_inference_v1.py');p.write_bytes(urllib.request.urlopen(u,timeout=30).read());raise SystemExit(subprocess.call([sys.executable,str(p)]))