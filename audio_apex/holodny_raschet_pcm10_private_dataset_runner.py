import os,sys,json,subprocess,urllib.request,hashlib,re,difflib,gc,traceback,zipfile
os.environ["USE_TORCH"]="1"
os.environ["USE_TF"]="0"
os.environ["USE_FLAX"]="0"
T="AH_HOLODNY_RASCHET_C01_C10_AUDIO_INTELLIGENCE_APEX_20260927"
D=["score_streams","score_likes","coherence","musicality","memorability","clarity","naturalness"]
LYRICS="В приложении — перевод.\nВ сообщении — сердечко.\nЯ почему-то долго считал,\nчто это одно и то же.\nСначала всё было мелочью: такси, доставка, «выручишь до пятницы?»\nЯ не считал — когда любишь, неудобно вести бухгалтерию.\nПотом заметил странную вещь: тепло появлялось вовремя,\nобычно сразу после фразы: «Мне тут немного не хватает».\nЯ сам приучил нас к этому — не буду делать вид, что нет.\nМне нравилось решать проблемы, будто так я становился нужней.\nНовый телефон, поездка, бронь — я называл это заботой,\nа сам всё чаще ждал в ответ хотя бы обычного «как ты?».\nНа столе чек из ресторана. Ты листаешь экран и молчишь.\nЯ говорю про тяжёлый день — ты спрашиваешь, оплатил ли отель.\nИ вот в эту секунду без крика, без сцены и чужих советов\nя впервые слышу, как близость превращается в прайс-лист.\nНе деньги болят.\nДеньги вернутся.\nБолит другое:\nя слишком долго путал «нужен»\nи «удобен».\nХолодный расчёт — не цифры в моём телефоне.\nЭто когда «люблю» почему-то всегда после «помоги».\nХолодный расчёт — я платил не за вещи,\nя платил за надежду, что если дам больше — останешься ты.\nТеперь счёт закрыт.\nБез мести. Без долга.\nНе надо возвращать мне прошлые суммы назад.\nЯ просто больше не покупаю\nто, что должно было быть между нами бесплатно.\nЯ пересмотрел переводы — не чтобы собрать компромат.\nХотел понять, где именно начал платить за собственный страх.\nВот здесь ты просила. Вот здесь я сам предложил вдвое больше.\nВот здесь обиделся, что вечером ты не стала теплее.\nНеприятная правда: я тоже участвовал в этом контракте.\nТы привыкла получать. Я привык доказывать ценность делами.\nИ пока каждый получал своё, это даже походило на пару,\nтолько разговор без покупки становился всё короче и реже.\nТы сказала: «Ты всё считаешь» — и, наверное, была права.\nНо я считаю не деньги. Я считаю моменты без ценника.\nСколько раз ты была рядом, когда мне нечего было предложить?\nСколько раз я был собой, а не картой, водителем, решением?\nОтвет оказался короче выписки.\nЯ закрыл приложение.\nНичего не удалял.\nПросто впервые не сделал следующий перевод.\nЛюбовь не обязана быть бедной.\nИ щедрость — не ошибка.\nОшибка — когда без неё\nтебя перестают замечать.\nХолодный расчёт — теперь я вижу его без злости.\nНе «ты плохая». Не «я дурак». Просто так больше нельзя.\nЯ слишком долго покупал себе место рядом,\nпока не понял: место, которое покупают, — уже не дом.\nСчёт закрыт.\nЯ не требую сдачи.\nПусть каждый заберёт то, что выбрал тогда.\nТы — свои вещи.\nЯ — привычку доказывать любовь\nсуммой в конце сообщения.\nЭкран погас.\nНа кухне тихо.\nИ впервые эта тишина\nничего мне не стоит."
P=[
("C01.wav",16798086,"b177bcd7ccc90ded65b4088c326066e836b37e9abcb23ea62fc8d25deddb8638"),
("C02.wav",16956528,"193b45121d8bcf63eb824f5565e17fec3b364756f8b8d7ab7467b454cc04a8c9"),
("C03.wav",16383228,"90326e35686ad502fccc56cfa34e05adfe3117de0c745ccff09c403e8b5d6fa5"),
("C04.wav",16052478,"c5e594f0013cb340071af0cf508cf4ff3bd95db4f9e7edf06d82c665328629cb"),
("C05.wav",17822034,"a04bdeffad975a38cacec2b970543595e3d4ef75776966acf7cd5cbecd060457"),
("C06.wav",16617628,"0d23d23e30ff722bb923f67f3fe5895396a122786988b4f5aa754ebdc2416a4c"),
("C07.wav",16395136,"d9030072a9a206521675c07ddb79fde566a030a4143d1b1e32e2a0eb08d7c0e1"),
("C08.wav",16732500,"07f1273f96bdf991c7774375bbe8a83e720e69640e3b43c23341fdc054ea96b3"),
("C09.wav",16801914,"f7cf2923b622b5f6e4645c905553b32cc3f4fd984ac2df887f069976cf135fd0"),
("C10.wav",12035320,"9586fe534e830d5244d676e8102a0cf21868cf3628bc23937522b5ce92abdd7e")]
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()
def norm(s): return re.findall(r"[0-9a-zа-я]+",s.lower().replace("ё","е"))
def match(a,b):
 sm=difflib.SequenceMatcher(a=a,b=b,autojunk=False);m=sum(i2-i1 for tag,i1,i2,j1,j2 in sm.get_opcodes() if tag=="equal");r=m/len(a) if a else 0;p=m/len(b) if b else 0;return 2*r*p/(r+p) if r+p else 0
def pct(v):
 n=len(v);return [((sum(x<q for x in v)+(sum(x==q for x in v)-1)/2)/(n-1)) for q in v]
out={"task_id":T,"state":"STARTED","human_heard":False,"owner_preference_used":False,"ingress":"PRIVATE_KAGGLE_DATASET_ATTACHED_EXACT_PCM10"}
try:
 W={}
 from pathlib import Path
 root=Path("/kaggle/input")
 zip_sha=[
  "9cea19ef5732400209228545a94a78fb51d6c7edb32a6fa140a0e76ed9d8ba34",
  "40f4f6d64603be964e5e7f42a9dd15533da1819851981706679d4b951320bf12",
  "6e8587cfa74735e056885b5a4fb236717702c412577ee88e5fb219c9d083cfae",
  "d33c6a3382cc70c707de45d465681c7fbdc04e3ff4a0f6bf8c06cd48f9b2deec",
  "b43fa68af0168fc187cc26c0744617a2d9f17385914bf325f56e0dc76da24e52",
  "70443d8d104c913a78b21aedff265a6389ac671aec644717c28f2c4039d8bccb",
  "2a6afa8d5f404f6fb4fbf8b745bbb1c00bc617c212c869201d95bfd53d00a5ae",
  "ace7931abd67b9048a0892654a8d9b7f62e507e77caef5d3ff30dc68ba543c64",
  "e28cd096568a1cfe6623f1283105b3df001c9aa561c25fa0bf8eef541e955e86"]
 inner_sha=[
  "b2739b98793fcbe9fccbe9c3dc558859e7e6e7d54cae1a4da1b096272dcf74e8",
  "b40a26211f80e523dfc4adcc0b063650f2e907d100e9823c5f9d316f197da93a",
  "fcf08e0f694092742472cc67e284e4ce03dd2984b0f2a6948f9f1c76fa20f0fd",
  "418ccc7ac9dd5b3591d511223288eaf284e86f0a19a5f889a9d58a75ea61a386",
  "e0fba732edf3290c2363ebdbc1db7129c35efbd55b93d4dbd0fa5c731e089e99",
  "0f641a8c2c215dd5398054c049e8368b40cf655676856c90684380fb1c0b27d2",
  "dfa9a7eabb60bc62a553a71750fa5eb224bfd3b1499442c5262fe862faf5a8b3",
  "0d4ea29ff53dbf8c38931f4c2c18d5ac33e2dcde4e00b78cec5b992b4f0288c1",
  "88883e1b26e47a79ddc8248ca8f2ac02805067b5aac0874907377776e3d075f6"]
 full=Path("/kaggle/working/AH_HOLODNY_RASCHET_PCM10_R1.zip")
 with open(full,"wb") as dst:
  for i in range(9):
   name=f"AH_HOLODNY_PCM10_R1.part{i:02d}.zip"
   matches=sorted(root.rglob(name))
   if len(matches)!=1: raise RuntimeError(f"TRANSPORT_ZIP_IDENTITY_AMBIGUOUS_{i:02d}_COUNT_{len(matches)}")
   zp=matches[0]
   if sha(zp)!=zip_sha[i]: raise RuntimeError(f"TRANSPORT_ZIP_SHA_FAIL_{i:02d}")
   with zipfile.ZipFile(zp) as z:
    names=z.namelist()
    if len(names)!=1: raise RuntimeError(f"TRANSPORT_ZIP_MEMBER_COUNT_FAIL_{i:02d}")
    raw=z.read(names[0])
   if hashlib.sha256(raw).hexdigest()!=inner_sha[i]: raise RuntimeError(f"TRANSPORT_PART_SHA_FAIL_{i:02d}")
   dst.write(raw)
 if sha(full)!="25a24e542a72b0b93555b5152fb86939759cdbb1636a6e97b436107e73c47ba8":
  raise RuntimeError("TRANSPORT_FULL_ZIP_SHA_FAIL")
 pcmroot=Path("/kaggle/working/pcm10_exact"); pcmroot.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(full) as z: z.extractall(pcmroot)
 for i,(name,sz,h) in enumerate(P,1):
  p=pcmroot/name
  if not p.exists() or os.path.getsize(p)!=sz or sha(p)!=h: raise RuntimeError(f"PCM_IDENTITY_FAIL_C{i:02d}")
  W[i]=str(p)
 out["transport_manifest"]={"state":"PASS_EXACT_TRANSPORT_9_OF_9","full_zip_sha256":sha(full)}
 out["split_manifest"]={"state":"PASS_EXACT_PCM10","rows":[{"candidate":i,"bytes":os.path.getsize(W[i]),"sha256":sha(W[i])} for i in W]}
 if os.environ.get("APEX_ENV")!="1":
  subprocess.check_call([sys.executable,"-m","pip","uninstall","-y","torchvision"])
  subprocess.check_call([sys.executable,"-m","pip","-q","install","--force-reinstall","numpy==1.26.4","scipy==1.15.3","soundfile==0.13.1","transformers==4.47.1","stable-ts"])
  os.environ["APEX_ENV"]="1"; os.execvpe(sys.executable,[sys.executable,__file__],os.environ)
 import numpy as np,torch,stable_whisper
 from transformers import AutoModel
 am=AutoModel.from_pretrained("amaai-lab/apex",trust_remote_code=True,device_map=None,low_cpu_mem_usage=False,ignore_mismatched_sizes=True)
 for o in [am,getattr(am,"audio_encoder",None),getattr(am,"mert",None),getattr(am,"encoder",None)]:
  if o is not None and hasattr(o,"config"): o.config.output_hidden_states=True
 am=am.to("cuda" if torch.cuda.is_available() else "cpu"); mr=[]
 for c in W:
  q=f"/kaggle/working/m{c:02d}.wav"; subprocess.check_call(["ffmpeg","-y","-i",W[c],"-t","60","-ac","2","-ar","24000",q],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  rr=am.predict(q); s={k:float(v) for k,v in rr.items() if isinstance(v,(int,float))}; mr.append({"candidate":c,"scores":s}); gc.collect()
  if torch.cuda.is_available(): torch.cuda.empty_cache()
 st={d:(float(np.mean([x["scores"][d] for x in mr])),float(np.std([x["scores"][d] for x in mr]))) for d in D}
 if any(v[1]<=1e-6 for v in st.values()): raise RuntimeError("APEX_SEMANTIC_ADMISSION_FAIL")
 for x in mr: x["z"]=float(np.mean([(x["scores"][d]-st[d][0])/(st[d][1]+1e-12) for d in D]))
 for rank,x in enumerate(sorted(mr,key=lambda z:z["z"])): x["MusicPct"]=rank/9
 music=[x["candidate"] for x in sorted(mr,key=lambda z:z["z"],reverse=True)]
 del am; gc.collect()
 if torch.cuda.is_available(): torch.cuda.empty_cache()
 wm=stable_whisper.load_model("base"); ref=norm(LYRICS); lr=[]
 for c in W:
  q=f"/kaggle/working/l{c:02d}.wav"; subprocess.check_call(["ffmpeg","-y","-i",W[c],"-ac","1","-ar","16000",q],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  tr=wm.transcribe(q,language="ru",verbose=False); txt=getattr(tr,"text","") or ""; f=match(ref,norm(txt)); al=wm.align(q,LYRICS,language="ru").to_dict()
  probs=[float(w["probability"]) for s in al.get("segments",[]) for w in(s.get("words")or[]) if w.get("probability") is not None]
  lr.append({"candidate":c,"asr_f1":f,"mean_p":sum(probs)/len(probs) if probs else 0.0})
 pf=pct([x["asr_f1"] for x in lr]); pp=pct([x["mean_p"] for x in lr])
 for i,x in enumerate(lr): x["LyricsPct"]=(pf[i]+pp[i])/2
 lyrics=[x["candidate"] for x in sorted(lr,key=lambda z:z["LyricsPct"],reverse=True)]
 bm={x["candidate"]:x for x in mr}; bl={x["candidate"]:x for x in lr}
 fused=[{"candidate":c,"MusicPct":bm[c]["MusicPct"],"LyricsPct":bl[c]["LyricsPct"],"BalancedPct":0.5*bm[c]["MusicPct"]+0.5*bl[c]["LyricsPct"]} for c in W]
 balanced=[x["candidate"] for x in sorted(fused,key=lambda z:z["BalancedPct"],reverse=True)]
 out.update(state="PASS_DUAL_AXIS_COMBINED_10",music={"ranking":music,"top3":music[:3]},lyrics={"ranking":lyrics,"top3":lyrics[:3]},balanced={"ranking":balanced,"top3":balanced[:3],"rows":fused})
except Exception as e:
 out.update(state="FAIL_DUAL_AXIS_COMBINED_10",error=repr(e),trace=traceback.format_exc(limit=20))
open("/kaggle/working/holodny10_dual_axis_final.json","w").write(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False))
try:
 data=json.dumps(out,ensure_ascii=False).encode(); req=urllib.request.Request("https://hook.us2.make.com/i6xte0qlwrf5z3ocrrl3bz8lxhcppkd9",data=data,headers={"Content-Type":"application/json"},method="POST"); urllib.request.urlopen(req,timeout=30).read()
except Exception as e: print("CALLBACK_FAIL",repr(e))
