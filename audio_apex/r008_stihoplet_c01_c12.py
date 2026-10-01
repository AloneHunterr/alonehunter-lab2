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
try:
 src="/kaggle/working/source.bin"
 print("AH_R008_SOURCE_DOWNLOAD_START",flush=True)
 SOURCE_URL=os.environ.get("AH_R008_SOURCE_URL","").strip()
 if not SOURCE_URL: raise RuntimeError("SOURCE_URL_REQUIRED")
 urllib.request.urlretrieve(SOURCE_URL,src)
 if not os.path.exists(src) or os.path.getsize(src)!=203515870: raise RuntimeError(f"SOURCE_BYTES_FAIL:{os.path.getsize(src) if os.path.exists(src) else -1}")
 W={}
 for i,(a,b) in enumerate(BOUNDARIES,1):
  p=f"/kaggle/working/C{i:02d}.wav"; subprocess.check_call(["ffmpeg","-y","-ss",str(a),"-to",str(b),"-i",src,"-vn","-acodec","pcm_s16le",p],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); W[i]=p
 out["split_manifest"]={"state":"PASS_BOUNDARY12","rows":[{"candidate":i,"bytes":os.path.getsize(W[i]),"sha256":hashlib.sha256(open(W[i],"rb").read()).hexdigest()} for i in W]}
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
