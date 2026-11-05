#!/usr/bin/env python3
"""Mesures additionnelles 10 bits du banc Finish après validation des images."""
import argparse, hashlib, json, math, os, pathlib, re, shutil
from execution_bornee import executer
def duree(s):
 v=float(s)
 if not math.isfinite(v) or v<=0: raise argparse.ArgumentTypeError('--timeout doit être un nombre positif, fini, en secondes')
 return v
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('medias',type=pathlib.Path)
parser.add_argument('resultats',type=pathlib.Path)
parser.add_argument('--ffmpeg',default=shutil.which('ffmpeg'),required=not shutil.which('ffmpeg'))
parser.add_argument('--timeout',type=duree,default=3600.0,help='délai maximal par commande ffmpeg, en secondes (positif, fini)')
args=parser.parse_args()
M=args.medias.resolve(strict=True); O=args.resultats.resolve(strict=True)
rows=json.loads((O/'mesures.json').read_text())
if not rows: raise ValueError('Banc vide')
if (O/'mesures-10bits.json').exists(): raise FileExistsError('Mesures 10 bits déjà présentes')
FF=args.ffmpeg
if hasattr(os,'sched_getaffinity'):
 cpus=sorted(os.sched_getaffinity(0))[:2]; os.sched_setaffinity(0,cpus)
out=[]
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
 return h.hexdigest()
def metrics(src,dst):
 graph='[0:v]settb=AVTB,setpts=N/(24*TB),format=yuv420p10le,split=2[r1][r2];[1:v]settb=AVTB,setpts=N/(24*TB),format=yuv420p10le,split=2[d1][d2];[d1][r1]ssim[s];[d2][r2]psnr[p]'
 cmd=[FF,'-nostdin','-hide_banner','-loglevel','info','-threads','2','-i',str(src),'-threads','2','-i',str(dst),'-filter_complex_threads','2','-filter_complex',graph,'-map','[s]','-f','null','-','-map','[p]','-f','null','-']
 _,err,_=executer(cmd,args.timeout,O/'commandes-10bits.log')
 ss=re.findall(r'SSIM.*?All:([0-9.]+)',err); ps=re.findall(r'PSNR.*?average:([0-9.]+|inf)',err)
 if not ss or not ps: raise ValueError('Métriques absentes')
 return float(ss[-1]),'inf' if ps[-1]=='inf' else float(ps[-1])
for row in rows:
 clip=row['clip']; profile=row['profil_nvenc']; src=M/(clip+'-source.mkv'); nv=M/(clip+'-'+profile+'.mp4'); x=O/(clip+'-x264-'+profile+'.mp4')
 if (digest(src),digest(nv),digest(x)) != (row['source_sha256'],row['nvenc_sha256'],row['x264_sha256']): raise ValueError('SHA différent du banc : '+clip+' '+profile)
 sn,pn=metrics(src,nv); sx,px=metrics(src,x)
 record={'clip':clip,'profil_nvenc':profile,'ssim_nvenc_10bits':sn,'ssim_x264_10bits':sx,'psnr_nvenc_10bits_db':pn,'psnr_x264_10bits_db':px}
 out.append(record); (O/'mesures-10bits.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n'); print(json.dumps(record),flush=True)
print('TERMINE',len(out),flush=True)
