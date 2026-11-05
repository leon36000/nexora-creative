#!/usr/bin/env python3
"""Banc local séquentiel 12 profils NVENC vs x264, sans réseau ni écrasement."""
import argparse, csv, hashlib, json, math, os, pathlib, platform, re, shlex, shutil, subprocess, sys, time
from fractions import Fraction
def duree(s):
 v=float(s)
 if not math.isfinite(v) or v<=0: raise argparse.ArgumentTypeError('--timeout doit être un nombre positif, fini, en secondes')
 return v
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('medias',type=pathlib.Path,help='3 sources FFV1 et 12 sorties NVENC')
parser.add_argument('sortie',type=pathlib.Path,help='nouveau dossier des résultats')
parser.add_argument('--profils',nargs='+',choices=['h264-p4','h264-p7','hevc10-p4','hevc10-p7'],default=['h264-p4','h264-p7','hevc10-p4','hevc10-p7'])
parser.add_argument('--profil-x264',choices=['main','high'],default='high')
parser.add_argument('--ffmpeg',default=shutil.which('ffmpeg'),required=not shutil.which('ffmpeg'))
parser.add_argument('--ffprobe',default=shutil.which('ffprobe'),required=not shutil.which('ffprobe'))
parser.add_argument('--timeout',type=duree,default=3600.0,help='délai maximal par commande ffmpeg/ffprobe, en secondes (positif, fini)')
parser.add_argument('--correction-proportionnelle',action='store_true',help='réencode une fois le x264 avec cible = round(cible_initiale * débit_NVENC / débit_x264_mesuré), sans rien écraser')
args=parser.parse_args()
if len(args.profils)!=len(set(args.profils)): parser.error('profils répétés interdits')
M=args.medias.resolve(strict=True); O=args.sortie.resolve(); O.mkdir(parents=True,exist_ok=False)
FF=args.ffmpeg; FP=args.ffprobe
if hasattr(os,'sched_getaffinity'):
 cpus=sorted(os.sched_getaffinity(0))[:2]; os.sched_setaffinity(0,cpus)
LOG=O/'commandes.log'
def run(cmd,log=LOG):
 cmd=list(map(str,cmd)); t=time.monotonic()
 def ecrire(statut,out,err):
  with log.open('a') as f: f.write('\n$ '+shlex.join(cmd)+'\ntimeout_s='+str(args.timeout)+'\n'+out+'\n'+err+'\n'+statut+' sec='+str(round(time.monotonic()-t,3))+'\n')
 try: x=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=args.timeout)
 except subprocess.TimeoutExpired as e:
  part=lambda v:(v.decode('utf-8','replace') if isinstance(v,bytes) else (v or ''))
  ecrire('status=timeout',part(e.stdout),part(e.stderr))
  raise RuntimeError('Délai de '+str(args.timeout)+' s dépassé (sortie partielle journalisée) : '+shlex.join(cmd)) from e
 ecrire('status='+str(x.returncode),x.stdout,x.stderr)
 if x.returncode: raise RuntimeError('Commande en échec : '+shlex.join(cmd))
 return x.stdout,x.stderr,time.monotonic()-t
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
 return h.hexdigest()
def probe(path):
 out,_,_=run([FP,'-v','error','-threads','2','-select_streams','v:0','-count_frames','-show_streams','-show_packets','-show_frames','-show_entries','stream=codec_name,profile,width,height,pix_fmt,color_range,color_space,color_transfer,color_primaries,r_frame_rate,avg_frame_rate,nb_read_frames,duration,bit_rate:packet=size,duration_time:frame=best_effort_timestamp_time','-of','json',path])
 j=json.loads(out); s=j['streams'][0]; packets=[x for x in j['packets_and_frames'] if x['type']=='packet']; frames=[x for x in j['packets_and_frames'] if x['type']=='frame']; n=int(s['nb_read_frames']); rate=Fraction(s['avg_frame_rate']);
 if n!=288 or rate!=24: raise ValueError(f'Images/fps incohérents : {path} {n} {rate}')
 size=sum(int(p['size']) for p in packets); duration=Fraction(n,1)/rate
 timestamps=[Fraction(x['best_effort_timestamp_time']) for x in frames]
 if len(packets)!=n or len(timestamps)!=n or any(abs(float(t-timestamps[0]-Fraction(i,24)))>.002 for i,t in enumerate(timestamps)): raise ValueError(f'Paquets ou cadence irrégulière : {path} {len(packets)}')
 return {'sha256':digest(path),'stream':s,'packet_count':len(packets),'packet_bytes':size,'frame_duration_s':float(duration),'video_bps':round(size*8/float(duration))}
def metric(src,dst,label):
 # Aligne les images par index après validation des nombres, FPS et dimensions.
 graph='[0:v]settb=AVTB,setpts=N/(24*TB),format=yuv420p,split=2[r1][r2];[1:v]settb=AVTB,setpts=N/(24*TB),format=yuv420p,split=2[d1][d2];[d1][r1]ssim[s];[d2][r2]psnr[p]'
 _,err,_=run([FF,'-nostdin','-hide_banner','-loglevel','info','-threads','2','-i',src,'-threads','2','-i',dst,'-filter_complex_threads','2','-filter_complex',graph,'-map','[s]','-f','null','-','-map','[p]','-f','null','-'])
 ss=re.findall(r'SSIM.*?All:([0-9.]+)',err); ps=re.findall(r'PSNR.*?average:([0-9.]+|inf)',err)
 if not ss or not ps: raise ValueError('Métriques absentes '+label)
 return {'ssim':float(ss[-1]),'psnr_db':'inf' if ps[-1]=='inf' else float(ps[-1])}
def save(rows):
 (O/'mesures.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
 if rows:
  with (O/'mesures.csv').open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
version=run([FF,'-version'])[0].splitlines()[0]; probeversion=run([FP,'-version'])[0].splitlines()[0]
(O/'environnement.json').write_text(json.dumps({'ffmpeg':version,'ffprobe':probeversion,'machine':platform.machine(),'affinite':sorted(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,'script_sha256':digest(pathlib.Path(__file__))},indent=2))
meta={}; rows=[]
for clip in ['action','bureau','espace']:
 src=M/(clip+'-source.mkv'); sm=probe(src); meta[src.name]=sm
 for profile in args.profils:
  nv=M/(clip+'-'+profile+'.mp4'); nm=probe(nv); meta[nv.name]=nm
  if (sm['stream']['width'],sm['stream']['height'])!=(nm['stream']['width'],nm['stream']['height']): raise ValueError('Dimensions incompatibles')
  dst=O/(clip+'-x264-'+profile+'.mp4'); passlog=O/(clip+'-'+profile+'-pass')
  def passe(cible,out,passprefix):
   common=[FF,'-nostdin','-hide_banner','-loglevel','info','-threads','2','-i',src,'-map','0:v:0','-an','-c:v','libx264','-threads','2','-preset','medium','-pix_fmt','yuv420p','-profile:v',args.profil_x264,'-b:v',str(cible),'-passlogfile',passprefix]
   start=time.monotonic(); run(common+['-pass','1','-f','null','-']); run(common+['-pass','2','-movflags','+faststart','-n',out]); return round(time.monotonic()-start,2)
  seconds=passe(nm['video_bps'],dst,passlog)
  xm=probe(dst); meta[dst.name]=xm
  metric_nv=metric(src,nv,'NVENC'); metric_x=metric(src,dst,'x264')
  row={'clip':clip,'profil_nvenc':profile,'source_sha256':sm['sha256'],'nvenc_sha256':nm['sha256'],'x264_sha256':xm['sha256'],'nvenc_bps':nm['video_bps'],'x264_bps':xm['video_bps'],'ecart_pct':round(100*(xm['video_bps']/nm['video_bps']-1),3),'ssim_nvenc':metric_nv['ssim'],'ssim_x264':metric_x['ssim'],'psnr_nvenc_db':metric_nv['psnr_db'],'psnr_x264_db':metric_x['psnr_db'],'x264_2passes_s':seconds,'images':288,'fps':24}
  rows.append(row); save(rows); (O/'metadonnees.json').write_text(json.dumps(meta,indent=2)+'\n'); print(json.dumps(row),flush=True)
  if args.correction_proportionnelle:
   # Un unique réencodage : cible *ratio* débits mesurés (paquets). Médias initiaux, SHA et métriques ci-dessus conservés.
   cible_corrigee=round(nm['video_bps']*nm['video_bps']/xm['video_bps'])
   dst_c=O/(clip+'-x264-'+profile+'-corrige.mp4'); passlog_c=O/(clip+'-'+profile+'-corrige-pass'); LOG_C=O/'commandes-correction.log'
   if dst_c.exists() or pathlib.Path(str(passlog_c)+'-0.log').exists(): raise FileExistsError('Sortie corrective déjà présente : '+dst_c.name)
   common_c=[FF,'-nostdin','-hide_banner','-loglevel','info','-threads','2','-i',src,'-map','0:v:0','-an','-c:v','libx264','-threads','2','-preset','medium','-pix_fmt','yuv420p','-profile:v',args.profil_x264,'-b:v',str(cible_corrigee),'-passlogfile',passlog_c]
   start=time.monotonic(); run(common_c+['-pass','1','-f','null','-'],LOG_C); run(common_c+['-pass','2','-movflags','+faststart','-n',dst_c],LOG_C); sec_c=round(time.monotonic()-start,2)
   xc=probe(dst_c); meta[dst_c.name]=xc
   metric_c=metric(src,dst_c,'x264-corrige')
   trace={'clip':clip,'profil_nvenc':profile,'parametres':{'timeout_s':args.timeout,'option':'--correction-proportionnelle','preset':'medium','profil_x264':args.profil_x264,'pix_fmt':'yuv420p','formule':'round(cible_initiale * debit_NVENC / debit_x264_mesure)','debit_mesure':'paquets','type':'VBR 2 passes (x264 peut dévier de la cible)'},
    'initial':{'fichier':dst.name,'sha256':xm['sha256'],'cible_bps':nm['video_bps'],'x264_bps':xm['video_bps'],'ecart_pct':row['ecart_pct'],'ssim':metric_x['ssim'],'psnr_db':metric_x['psnr_db'],'x264_2passes_s':seconds},
    'corrige':{'fichier':dst_c.name,'sha256':xc['sha256'],'cible_bps':cible_corrigee,'x264_bps':xc['video_bps'],'ecart_pct':round(100*(xc['video_bps']/nm['video_bps']-1),3),'ssim':metric_c['ssim'],'psnr_db':metric_c['psnr_db'],'x264_2passes_s':sec_c},
    'nvenc_bps':nm['video_bps']}
   trace_c=O/'corrections.json'; existants=json.loads(trace_c.read_text()) if trace_c.exists() else []
   existants.append(trace); trace_c.write_text(json.dumps(existants,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
   (O/'metadonnees.json').write_text(json.dumps(meta,indent=2)+'\n')
   print(json.dumps(trace),flush=True)
print('TERMINE',len(rows),flush=True)
