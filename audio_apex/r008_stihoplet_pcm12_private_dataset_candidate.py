import os,sys,json,subprocess,urllib.request,hashlib,re,difflib,gc,traceback
os.environ["USE_TORCH"]="1"
os.environ["USE_TF"]="0"
T="AH_YA_RUSSKIY_STIHOPLET_C01_C12_AUDIO_INTELLIGENCE_APEX_20260927"
D=["score_streams","score_likes","coherence","musicality","memorability","clarity","naturalness"]
LYRICS="""Мыслей водоворот. Событий переплёт. Поехали. Мыслей водоворот, событий переплёт, Мой разум — это цех, где плавится мой лёд. Ночных падений круговорот — Я падаю вглубь, чтоб сделать новый взлёт. Ломаю ритм пополам, крушу стандартный такт, В моих словах не золото, там собран антидот. От ядов ваших СМИ, от фальши соцсетей, Я строю свой ковчег из собственных костей. Вы ищете хайп, я ищу глубину, Бросая строки прямо на войну С самим собой, с системой, с тишиной, Я русский стихоплёт, мне ведом путь иной. Мыслей водоворот! Событий переплёт! Система зависает, когда мой трек идёт! Ночных падений круговорот! Я — русский стихоплёт! Я — русский стихоплёт! Калёным словом жгу гнилую медь, Мне наплевать на то, что вы хотите петь. Мои чернила — ночь, моя бумага — страх, Я выбиваю искры в этих четырёх стенах. Ты хочешь баттл? Что ж, давай начнём, Я выжгу твою душу ледяным огнём. Не ради славы, не за лайки, не за чек, Я просто выпускаю боль свою в набег. Изнанка мира здесь, смотри в мои глаза, В них отражается грядущая гроза. Круговорот. Переплёт. Водоворот. И снова взлёт. Я записываю код. Прямо в подкорку. Год за годом. Мыслей водоворот! Событий переплёт! Система падает, когда мой флоу идёт! Ночных падений круговорот! Я — русский стихоплёт! Я — русский стихоплёт!"""
P=[
("C01.wav",15563286,"211656ae423436e1d3bce0cbaae10c3b19684795161fb55378d7e1a441043274"),
("C02.wav",15567378,"d7653b221bc0a3b1c71655ba23ec6540fa3d376168a8bfba171f865f2e514b1c"),
("C03.wav",15192528,"40155bbe7939511c7ff3aabcde2668ee674884efe226af389d99e13341e300ef"),
("C04.wav",16758078,"b2a1a48c84590c4bf0d769b290eb120d8f53289fe9347057aedc29dfc3eb715a"),
("C05.wav",16515528,"45e5698c3cd581e2f21a3573f944a940d0605d7fb0f2e4cc276fbf7359a45165"),
("C06.wav",16383228,"9bdf6fef1812231d2196fa7f2041c36c222408684f353eb73943ef59a71d8b29"),
("C07.wav",16206828,"c4b72807c445596a2007110a29a3712575f92e9754b9185da6d23bcd114099fa"),
("C08.wav",16868328,"4280505e6f6151c8ed9a68234ad9b906f30ab1152b5e43b9a06b1cf918e376d9"),
("C09.wav",16383228,"d40245ba44ab3928b610ce5291163085c9ad9c341cb757f5ba287d03308d5603"),
("C10.wav",16052478,"3c56261b98d891bb248ead4c0a71e499e58f5f93d3faa02fed707147b917aaea"),
("C11.wav",15677628,"3c7576bd811a16db8e2ba32b26482a57ef8a07123e87f15739a56943bf308019"),
("C12.wav",17244942,"2e298409dd5d029432fd501a68996dd79357fbcd410b1aabc6d25b4e85f93b55")]
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def norm(s):return re.findall(r"[0-9a-zа-я]+",s.lower().replace("ё","е"))
def match(a,b):
 sm=difflib.SequenceMatcher(a=a,b=b,autojunk=False);m=sum(i2-i1 for tag,i1,i2,j1,j2 in sm.get_opcodes() if tag=="equal");r=m/len(a) if a else 0;p=m/len(b) if b else 0;return 2*r*p/(r+p) if r+p else 0
def pct(v):
 n=len(v);return [((sum(x<q for x in v)+(sum(x==q for x in v)-1)/2)/(n-1)) for q in v]
out={"task_id":T,"state":"STARTED","human_heard":False,"owner_preference_used":False,"ingress":"PRIVATE_KAGGLE_DATASET_ATTACHED_EXACT_PCM12","transport_only_successor":True}
try:
 W={}
 from pathlib import Path
 root=Path("/kaggle/input")
 for i,(name,sz,h) in enumerate(P,1):
  matches=sorted(root.rglob(name))
  if len(matches)!=1:
   raise RuntimeError(f"PCM_DATASET_IDENTITY_AMBIGUOUS_C{i:02d}_COUNT_{len(matches)}")
  p=str(matches[0])
  if os.path.getsize(p)!=sz or sha(p)!=h:
   raise RuntimeError(f"PCM_IDENTITY_FAIL_C{i:02d}")
  W[i]=p
 out["split_manifest"]={"state":"PASS_EXACT_PCM12","rows":[{"candidate":i,"bytes":os.path.getsize(W[i]),"sha256":sha(W[i])} for i in W]}
 if os.environ.get("APEX_ENV")!="1":
  subprocess.check_call([sys.executable,"-m","pip","uninstall","-y","torchvision"])
  subprocess.check_call([sys.executable,"-m","pip","-q","install","--force-reinstall","numpy==1.26.4","scipy==1.15.3","soundfile==0.13.1","transformers==4.47.1","stable-ts"])
  os.environ["APEX_ENV"]="1";os.execvpe(sys.executable,[sys.executable,__file__],os.environ)
 import numpy as np,torch,stable_whisper
 from transformers import AutoModel
 am=AutoModel.from_pretrained("amaai-lab/apex",trust_remote_code=True,device_map=None,low_cpu_mem_usage=False,ignore_mismatched_sizes=True)
 for o in [am,getattr(am,"audio_encoder",None),getattr(am,"mert",None),getattr(am,"encoder",None)]:
  if o is not None and hasattr(o,"config"):o.config.output_hidden_states=True
 am=am.to("cuda" if torch.cuda.is_available() else "cpu");mr=[]
 for c in W:
  q=f"/kaggle/working/m{c:02d}.wav";subprocess.check_call(["ffmpeg","-y","-i",W[c],"-t","60","-ac","2","-ar","24000",q],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  rr=am.predict(q);s={k:float(v) for k,v in rr.items() if isinstance(v,(int,float))};mr.append({"candidate":c,"scores":s});gc.collect()
  if torch.cuda.is_available():torch.cuda.empty_cache()
 st={d:(float(np.mean([x["scores"][d] for x in mr])),float(np.std([x["scores"][d] for x in mr]))) for d in D}
 if any(v[1]<=1e-6 for v in st.values()):raise RuntimeError("APEX_SEMANTIC_ADMISSION_FAIL")
 for x in mr:x["z"]=float(np.mean([(x["scores"][d]-st[d][0])/(st[d][1]+1e-12) for d in D]))
 for rank,x in enumerate(sorted(mr,key=lambda z:z["z"])):x["MusicPct"]=rank/11
 music=[x["candidate"] for x in sorted(mr,key=lambda z:z["z"],reverse=True)]
 del am;gc.collect()
 if torch.cuda.is_available():torch.cuda.empty_cache()
 wm=stable_whisper.load_model("base");ref=norm(LYRICS);lr=[]
 for c in W:
  q=f"/kaggle/working/l{c:02d}.wav";subprocess.check_call(["ffmpeg","-y","-i",W[c],"-ac","1","-ar","16000",q],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  tr=wm.transcribe(q,language="ru",verbose=False);txt=getattr(tr,"text","") or "";f=match(ref,norm(txt));al=wm.align(q,LYRICS,language="ru").to_dict()
  probs=[float(w["probability"]) for s in al.get("segments",[]) for w in(s.get("words")or[]) if w.get("probability") is not None]
  lr.append({"candidate":c,"asr_f1":f,"mean_p":sum(probs)/len(probs) if probs else 0.0})
 pf=pct([x["asr_f1"] for x in lr]);pp=pct([x["mean_p"] for x in lr])
 for i,x in enumerate(lr):x["LyricsPct"]=(pf[i]+pp[i])/2
 lyrics=[x["candidate"] for x in sorted(lr,key=lambda z:z["LyricsPct"],reverse=True)]
 bm={x["candidate"]:x for x in mr};bl={x["candidate"]:x for x in lr}
 fused=[{"candidate":c,"MusicPct":bm[c]["MusicPct"],"LyricsPct":bl[c]["LyricsPct"],"BalancedPct":0.5*bm[c]["MusicPct"]+0.5*bl[c]["LyricsPct"]} for c in W]
 balanced=[x["candidate"] for x in sorted(fused,key=lambda z:z["BalancedPct"],reverse=True)]
 out.update(state="PASS_DUAL_AXIS_COMBINED_12",music={"ranking":music,"top3":music[:3]},lyrics={"ranking":lyrics,"top3":lyrics[:3]},balanced={"ranking":balanced,"top3":balanced[:3],"rows":fused})
except Exception as e:out.update(state="FAIL_DUAL_AXIS_COMBINED_12",error=repr(e),trace=traceback.format_exc(limit=20))
open("/kaggle/working/r008_stihoplet12_dual_axis_final.json","w").write(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False))
try:
 data=json.dumps(out,ensure_ascii=False).encode();req=urllib.request.Request("https://hook.us2.make.com/i6xte0qlwrf5z3ocrrl3bz8lxhcppkd9",data=data,headers={"Content-Type":"application/json"},method="POST");urllib.request.urlopen(req,timeout=30).read()
except Exception as e:print("CALLBACK_FAIL",repr(e))
