import os,sys,json,subprocess,urllib.request,hashlib,re,difflib,gc,traceback
TASK="AH_YA_RUSSKIY_STIHOPLET_C01_C12_AUDIO_INTELLIGENCE_APEX_20260927"; SOURCE="15CmWqvNmVQ6CmkAtH_MMXAOKBWqqE6C6"
BOUNDARIES=[(0,176.5),(176.5,353),(353,525.25),(525.25,715.25),(715.25,902.5),(902.5,1088.25),(1088.25,1272),(1272,1463.25),(1463.25,1649),(1649,1831),(1831,2008.75),(2008.75,2204.270)]
LYRICS="Мыслей водоворот.\nСобытий переплёт.\nКак назвать красивее — не знаю.\nЯ просто связываю слова.\nНа полях снова стрелки, помарки, круги,\nРучка вдавила строку — даже сзади видны следы.\nПолфразы на чеке, одно слово — на сгибе листа,\nМысль приходит не вовремя. В этом и вся красота.\nПоменяю два слова местами — и смысл уже врёт,\nСтавлю ударение — слышу, где фраза живёт.\nНе хочу за терминами прятать обычный рассказ,\nМне бы точно назвать то, что раньше застряло во мне без названья.\nЯ знаю язык, где «держись» иногда означает «люблю»,\nГде «нормально» звучит, когда всё разлетелось к нулю.\nГде мужчина молчит, а потом на четырёх строках\nГоворит то, что год не решался сказать на словах.\nНе поэт на портрете.\nНе голос эпох.\nЕсли долго молчу — внутри остаётся узел из слов.\nМыслей водоворот. Событий переплёт.\nЯ русский стихоплёт — вот и весь мой почёт.\nНе за громкость строки, не за правильный вид —\nЯ связываю то, что болело, в слова, с которыми можно жить.\nМыслей водоворот. Событий переплёт.\nГде другой промолчит — у меня остаётся блокнот.\nЕсли слово попало туда, где ещё не зажило,\nЗначит, я не зря до утра подбирал ему точный глагол.\nВ русском слове бывает и камень, и тёплая ткань,\nМожно резко отрезать, а можно сказать: «Не пропадай».\nИ одной этой фразой оставить для близкого дверь,\nЯ учился писать так, чтоб сам написанному мог поверить.\nРаньше строил из строк доказательство: «вот я какой»,\nДобавлял больше стали, огня — лишь бы выглядеть бронёй.\nА теперь вычёркиваю всё, чего не было в жизни моей:\nОдна точная деталь говорит убедительней сотни речей.\nЯ не спорю с системой, не меряюсь флоу с чужаками,\nУ меня свой экзамен — прочесть и не спрятать глаза.\nЕсли строчка звучит так, как я бы сказал это близкому,\nЯ оставлю её. Остальное — обратно в поля.\nСтихоплёт.\nСлово будто несерьёзное.\nМне подходит.\nПотому что я правда плету:\nиз «держись»,\nиз «прости»,\nиз «я рядом».\nТо, что трудно сказать напрямую,\nиногда легче сначала\nнаписать.\nМыслей водоворот. Событий переплёт.\nЯ русский стихоплёт — не медаль, не почёт.\nПросто русский язык у меня под рукой,\nЯ на слух проверяю им каждую строчку: моя или роль.\nМыслей водоворот. Событий переплёт.\nЕсли жизнь разорвёт — я свяжу, что ещё не прошло.\nНе для славы. Не чтобы остаться великим потом.\nМне бы честно сказать.\nВот и всё.\nЯ — стихоплёт.\nНа полях — ещё место.\nЗначит, продолжим."
def norm(s): return re.findall(r"[0-9a-zа-я]+",s.lower().replace("ё","е"))
def f1(a,b):
 sm=difflib.SequenceMatcher(a=a,b=b,autojunk=False); m=sum(i2-i1 for tag,i1,i2,j1,j2 in sm.get_opcodes() if tag=="equal"); r=m/len(a) if a else 0;p=m/len(b) if b else 0;return 2*r*p/(r+p) if r+p else 0
def pct(v):
 n=len(v);return [((sum(x<q for x in v)+(sum(x==q for x in v)-1)/2)/(n-1)) for q in v]
out={"task_id":TASK,"state":"STARTED","human_heard":False,"owner_preference_used":False}
print("AH_R008_RUNNER_START",flush=True)
P=[['1SndR3DouiAEsnuSyLh6gFvul1fkTLi1t',15563286,'211656ae423436e1d3bce0cbaae10c3b19684795161fb55378d7e1a441043274'],['1T-4aVeQhx4bp8EszRIOBYJg5RAqHt6bh',15567378,'d7653b221bc0a3b1c71655ba23ec6540fa3d376168a8bfba171f865f2e514b1c'],['1DCPNh0z0QDT2qB4D-IGIGqR2vGRATSQt',15192528,'40155bbe7939511c7ff3aabcde2668ee674884efe226af389d99e13341e300ef'],['1BEcG3XWe8QZS03I6OTSHhnvXNF1w6uux',16758078,'b2a1a48c84590c4bf0d769b290eb120d8f53289fe9347057aedc29dfc3eb715a'],['1yuvCoN09wTI6tGYqvG1ZDC_dqnAWtG2B',16515528,'45e5698c3cd581e2f21a3573f944a940d0605d7fb0f2e4cc276fbf7359a45165'],['1ghO9L5s4a266DjhmtCuhyis2Y7Jo8gAg',16383228,'9bdf6fef1812231d2196fa7f2041c36c222408684f353eb73943ef59a71d8b29'],['1eo8o4rcC-nGxICQ1OXfQIAIfhEz8UUlu',16206828,'c4b72807c445596a2007110a29a3712575f92e9754b9185da6d23bcd114099fa'],['1bfcu3MOkvA-XeEv4VLXE4nS3_3sAxqdo',16868328,'4280505e6f6151c8ed9a68234ad9b906f30ab1152b5e43b9a06b1cf918e376d9'],['12K-4_jMmh-A3YKThLhV1vNuTNyinOXyv',16383228,'d40245ba44ab3928b610ce5291163085c9ad9c341cb757f5ba287d03308d5603'],['13Cqyt2fwuoTTq3TfQglQ4c5u23t1VkTG',16052478,'3c56261b98d891bb248ead4c0a71e499e58f5f93d3faa02fed707147b917aaea'],['1oTBhNCOLSrjgLilLFxXGvqojg90E_VpR',15677628,'3c7576bd811a16db8e2ba32b26482a57ef8a07123e87f15739a56943bf308019'],['1SUvPzP3qfAN_24Ug2wg8gLeBDlnnm2IZ',17244942,'2e298409dd5d029432fd501a68996dd79357fbcd410b1aabc6d25b4e85f93b55']]
try:
 W={}
 for i,(fid,sz,h) in enumerate(P,1):
  p=f"/kaggle/working/C{i:02d}.wav"
  urllib.request.urlretrieve(f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t",p)
  got=hashlib.sha256(open(p,"rb").read()).hexdigest()
  if os.path.getsize(p)!=sz or got!=h: raise RuntimeError(f"PCM_IDENTITY_FAIL_C{i:02d}:{os.path.getsize(p)}:{got}")
  W[i]=p
 out["split_manifest"]={"state":"PASS_EXACT_PCM12","rows":[{"candidate":i,"bytes":os.path.getsize(W[i]),"sha256":hashlib.sha256(open(W[i],"rb").read()).hexdigest()} for i in W]}
 if os.environ.get("APEX_ENV")!="1":
  subprocess.check_call([sys.executable,"-m","pip","uninstall","-y","torchvision"])
  subprocess.check_call([sys.executable,"-m","pip","-q","install","--force-reinstall","numpy==1.26.4","scipy==1.15.3","soundfile==0.13.1","transformers==4.47.1","stable-ts"])
  os.environ["APEX_ENV"]="1"; os.execvpe(sys.executable,[sys.executable,__file__],os.environ)
 import numpy as np,torch,stable_whisper
 from transformers import AutoModel
 dims=["score_streams","score_likes","coherence","musicality","memorability","clarity","naturalness"]
 am=AutoModel.from_pretrained("amaai-lab/apex",trust_remote_code=True,device_map=None,low_cpu_mem_usage=False,ignore_mismatched_sizes=True)
 for o in [am,getattr(am,"audio_encoder",None),getattr(am,"mert",None),getattr(am,"encoder",None)]:
  if o is not None and hasattr(o,"config"): o.config.output_hidden_states=True
 am=am.to("cuda" if torch.cuda.is_available() else "cpu"); mr=[]
 for c in W:
  q=f"/kaggle/working/m{c:02d}.wav";subprocess.check_call(["ffmpeg","-y","-i",W[c],"-t","60","-ac","2","-ar","24000",q],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);rr=am.predict(q);s={k:float(v) for k,v in rr.items() if isinstance(v,(int,float))};mr.append({"candidate":c,"scores":s})
 st={d:(float(np.mean([x["scores"][d] for x in mr])),float(np.std([x["scores"][d] for x in mr]))) for d in dims}
 if any(v[1]<=1e-6 for v in st.values()): raise RuntimeError("APEX_SEMANTIC_ADMISSION_FAIL")
 for x in mr:x["z"]=float(np.mean([(x["scores"][d]-st[d][0])/(st[d][1]+1e-12) for d in dims]))
 for rank,x in enumerate(sorted(mr,key=lambda z:z["z"])):x["MusicPct"]=rank/11
 music=[x["candidate"] for x in sorted(mr,key=lambda z:z["z"],reverse=True)];del am;gc.collect()
 wm=stable_whisper.load_model("base");ref=norm(LYRICS);lr=[]
 for c in W:
  q=f"/kaggle/working/l{c:02d}.wav";subprocess.check_call(["ffmpeg","-y","-i",W[c],"-ac","1","-ar","16000",q],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);tr=wm.transcribe(q,language="ru",verbose=False);txt=getattr(tr,"text","") or "";ff=f1(ref,norm(txt));al=wm.align(q,LYRICS,language="ru").to_dict();probs=[float(w["probability"]) for s in al.get("segments",[]) for w in(s.get("words")or[]) if w.get("probability") is not None];lr.append({"candidate":c,"asr_f1":ff,"mean_p":sum(probs)/len(probs) if probs else 0.0})
 pf=pct([x["asr_f1"] for x in lr]);pp=pct([x["mean_p"] for x in lr])
 for i,x in enumerate(lr):x["LyricsPct"]=(pf[i]+pp[i])/2
 lyrics=[x["candidate"] for x in sorted(lr,key=lambda z:z["LyricsPct"],reverse=True)];bm={x["candidate"]:x for x in mr};bl={x["candidate"]:x for x in lr};fused=[{"candidate":c,"MusicPct":bm[c]["MusicPct"],"LyricsPct":bl[c]["LyricsPct"],"BalancedPct":.5*bm[c]["MusicPct"]+.5*bl[c]["LyricsPct"]} for c in W];balanced=[x["candidate"] for x in sorted(fused,key=lambda z:z["BalancedPct"],reverse=True)]
 out.update(state="PASS_DUAL_AXIS_COMBINED_12",music={"ranking":music,"top3":music[:3]},lyrics={"ranking":lyrics,"top3":lyrics[:3]},balanced={"ranking":balanced,"top3":balanced[:3],"rows":fused})
except Exception as e: out.update(state="FAIL_DUAL_AXIS_COMBINED_12",error=repr(e),trace=traceback.format_exc(limit=20))
print(json.dumps(out,ensure_ascii=False))
try:
 req=urllib.request.Request("https://hook.us2.make.com/i6xte0qlwrf5z3ocrrl3bz8lxhcppkd9",data=json.dumps(out,ensure_ascii=False).encode(),headers={"Content-Type":"application/json"},method="POST");urllib.request.urlopen(req,timeout=30).read()
except Exception as e: print("CALLBACK_FAIL",repr(e))
