"""Tests unittest complémentaires des refus de sync_rnd.py, fixtures synthétiques, sans réseau."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('sync_rnd_add',Path(__file__).with_name('sync_rnd.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


class RefusSyncRndTest(unittest.TestCase):
    """Mêmes types de refus : contrats, preuves, reçu professeur, candidat."""

    def setUp(self):
        self.n=0
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.roots=[self.root]
        self.video=self.f('video',b'video-synthetique');self.audio=self.f('audio',b'mp3-synthetique')
        self.pcm=self.f('pcm',b'pcm-synthetique');self.mr=self.f('mr.py',b'# runner m\n');self.hr=self.f('hr.py',b'# runner h\n')
        self.out_m=self.f('out_m',b'sortie m');self.ev_m=self.f('ev_m',json.dumps({'status':'completed_av_validated','run_id':'synthetique-m','av_validation':{'valide':True},'final_output':{'sha256':digest(self.out_m)}}).encode())
        self.out_h=self.f('out_h',b'sortie h');self.man_h=self.f('man_h',json.dumps({'statut':'canonique_valide','validation_av':{'valide':True},'brut_sha256':digest(self.out_h),'audio_sha256':digest(self.pcm),'canonique_sha256':digest(self.out_h)}).encode())
        self.gpu_h=self.f('gpu_h',json.dumps({'validation_av':{'valide':False}}).encode())
        self.descriptor={'schema':s.DESC,'episodes':[{'id':'m1','engine':'musetalk','trajectory':self.ref(self.write('m.json',self.muse())),'artifacts':self.arts(self.mr)},
                                                    {'id':'h1','engine':'highsync','trajectory':self.ref(self.write('h.json',self.high())),'artifacts':self.arts(self.hr)}]}
        self.desc=self.write('descriptor.json',self.descriptor)

    # --- utilitaires ---
    def f(self,name,content):
        self.n+=1;p=self.root/('f%02d-%s'%(self.n,name));p.write_bytes(content);return p
    def ref(self,p):return {'path':str(p),'sha256':digest(p),'bytes':p.stat().st_size}
    def write(self,name,value):
        self.n+=1;p=self.root/('j%02d-%s'%(self.n,name));p.write_text(json.dumps(value));return p
    def arts(self,code):return {'video':self.ref(self.video),'audio_original':self.ref(self.audio),'audio_pcm':self.ref(self.pcm),'runner':self.ref(code)}
    def muse(self):
        return {'schema':s.SCHEMAS['musetalk'],'memory_promotion':'none','human_review_status':'pending_founder','amd2_brief_id':None,
                'run':{'run_id':'synthetique-m','status':'completed_av_validated','musetalk_version':'test','runner_sha256':digest(self.mr),
                       'source_video':self.ref(self.video),'output':self.ref(self.out_m),
                       'voice_input':{'mp3_sha256':digest(self.audio),'model_input_wav_sha256':digest(self.pcm)}},
                'evidence':{'run_result':self.ref(self.ev_m)},'observations':[{'text':'observation m'}],'proposed_correction':{'status':'proposee'}}
    def high(self):
        return {'schema':s.SCHEMAS['highsync'],'memory_promotion':'none','human_review_status':'pending_founder','amd2_brief_id':None,
                'inputs':{'video_sha256':digest(self.video),'audio_mp3_sha256':digest(self.audio),'audio_pcm_sha256':digest(self.pcm)},
                'raw':{'av_status':'failed','output':self.ref(self.out_h),'video_frames':27,'fps':25,'video_duration_seconds':1.08},
                'canonical_export':{'status':'av_validated','output':self.ref(self.out_h),'export_manifest':self.ref(self.man_h),'fps':25},
                'run':{'run_id':'synthetique-h','source_commit':'synthetique','seed':77,'runner':self.ref(self.hr),'gpu_execution_result':self.ref(self.gpu_h)},
                'observations':{'scope':'synthetique'}}
    def data(self):return s.importer(self.desc,digest(self.desc),self.roots)
    def obs(self):return self.write('obs.json',self.data())
    def answer(self,sources=('m1',)):
        return {'workflow':[{'texte':'Conserver les sources.','sources':list(sources)}],'sous_taches':[],'indices_fonction':[]}
    def receipt(self,payload,alias='gemini-eleve',**over):
        r={'type':'result','subtype':'success','is_error':False,'num_turns':1,'modelUsage':{'eco-'+alias:{}},
           'result':payload if isinstance(payload,str) else json.dumps(payload)}
        r.update(over);return self.write('receipt.json',r)
    def valid_candidate(self):
        obs=self.obs();ans=self.answer();res=self.write('response.json',ans);rec=self.receipt(ans)
        return obs,res,rec,s.valider_reponse(obs,res,rec,self.roots,'gemini-eleve')
    def refuse(self,fn,*args):
        with self.assertRaises(s.ContratErreur):fn(*args)

    # --- descripteur / statuts ---
    def test_descripteur_non_dict_ou_schema_proche(self):
        for value in ([], 'texte', {'schema':s.DESC}, {'schema':s.DESC,'episodes':{},'extra':1},
                      {'schema':s.SCHEMAS['musetalk'],'episodes':self.descriptor['episodes']}):
            with self.subTest(value=value):
                p=self.write('bad-desc.json',value);self.refuse(s.importer,p,digest(p),self.roots)

    def test_trop_d_episodes_refuses(self):
        a=self.descriptor['episodes'][0]
        d={'schema':s.DESC,'episodes':[dict(a,id='e%d'%i) for i in range(101)]}
        p=self.write('many.json',d);self.refuse(s.importer,p,digest(p),self.roots)

    def test_episode_et_identite_invalides(self):
        for mutation in ('cle','id','moteur','trajectoire'):
            with self.subTest(mutation=mutation):
                d=json.loads(json.dumps(self.descriptor));e=d['episodes'][0]
                if mutation=='cle':e['inconnue']=1
                elif mutation=='id':e['id']='-mauvais id'
                elif mutation=='moteur':e['engine']='autre'
                else:e['trajectory']=self.ref(self.video)
                p=self.write('ep.json',d);self.refuse(s.importer,p,digest(p),self.roots)

    def test_statuts_trajectoire_non_conformes(self):
        for key,value in (('memory_promotion','promoted'),('human_review_status','approved'),
                          ('amd2_brief_id','AMD2-7'),('schema','nexora.sync.autre.v1')):
            with self.subTest(key=key):
                d=json.loads(json.dumps(self.descriptor));m=self.muse();m[key]=value
                d['episodes'][0]['trajectory']=self.ref(self.write('m-statut.json',m))
                p=self.write('statut.json',d);self.refuse(s.importer,p,digest(p),self.roots)

    # --- preuves absentes ou incohérentes ---
    def test_artefacts_absents_inconnus_ou_mal_cibles(self):
        for mutation in ('absent','inconnu','sha'):
            with self.subTest(mutation=mutation):
                d=json.loads(json.dumps(self.descriptor))
                if mutation=='absent':d['episodes'][1]['artifacts'].pop('runner')
                elif mutation=='inconnu':d['episodes'][1]['artifacts']['secret']=self.ref(self.gpu_h)
                else:d['episodes'][1]['artifacts']['video']=self.ref(self.audio)
                p=self.write('arts.json',d);self.refuse(s.importer,p,digest(p),self.roots)

    def test_preuve_hors_racine_ou_absente(self):
        d=json.loads(json.dumps(self.descriptor));d['episodes'][0]['artifacts']['video']['path']='/etc/passwd'
        p=self.write('hors.json',d);self.refuse(s.importer,p,digest(p),self.roots)
        d=json.loads(json.dumps(self.descriptor));d['episodes'][0]['artifacts']['video']={'path':str(self.root/'inexistant'),'sha256':'0'*64}
        p=self.write('absent.json',d);self.refuse(s.importer,p,digest(p),self.roots)

    def test_preuve_alteree_apres_construction(self):
        d=json.loads(json.dumps(self.descriptor));p=self.write('altere.json',d)
        self.ev_m.write_text('pas le bon JSON')
        self.refuse(s.importer,p,digest(p),self.roots)

    def test_preuves_absentes_en_entree(self):
        obs,prompt,req=self.answer()[ 'workflow' ][0]['texte'],None,None
        with self.assertRaises((s.ContratErreur,FileNotFoundError)):
            s.prompt(self.root/'obs-absent.json',self.roots)
        with self.assertRaises((s.ContratErreur,FileNotFoundError)):
            s.consulter(self.root/'candidat-absent.json',self.roots)

    def test_musetalk_succes_sans_receipt_ou_statut_different(self):
        d=json.loads(json.dumps(self.descriptor));m=self.muse();m.pop('evidence')
        d['episodes'][0]['trajectory']=self.ref(self.write('m-noev.json',m))
        p=self.write('noev.json',d);self.refuse(s.importer,p,digest(p),self.roots)
        self.ev_m.write_text(json.dumps({'status':'failed'}))
        p=self.write('statut-ev.json',json.loads(json.dumps(self.descriptor)))
        self.refuse(s.importer,p,digest(p),self.roots)

    def test_highsync_export_valide_sans_preuve(self):
        d=json.loads(json.dumps(self.descriptor));h=self.high();h['canonical_export'].pop('export_manifest')
        d['episodes'][1]['trajectory']=self.ref(self.write('h-noman.json',h))
        p=self.write('noman.json',d);self.refuse(s.importer,p,digest(p),self.roots)

    def test_highsync_export_valide_manifeste_non_attestant(self):
        for man in ({'statut':'incomplet','validation_av':{'valide':True}},{'statut':'canonique_valide','validation_av':{}}):
            with self.subTest(man=man):
                self.man_h.write_text(json.dumps(man))
                p=self.write('man.json',json.loads(json.dumps(self.descriptor)))
                self.refuse(s.importer,p,digest(p),self.roots)
        self.man_h.write_text(json.dumps({'statut':'canonique_valide','validation_av':{'valide':True}}))

    def test_code_export_sans_manifeste_ou_signature(self):
        code=self.f('export.py',b'def autre():\n    pass\n')
        d=json.loads(json.dumps(self.descriptor));d['episodes'][1]['artifacts']['export_code']=self.ref(code)
        p=self.write('export.json',d);self.refuse(s.importer,p,digest(p),self.roots)
        d=json.loads(json.dumps(self.descriptor));h=self.high();h.pop('canonical_export')
        d['episodes'][1]['trajectory']=self.ref(self.write('h-nocanon.json',h));d['episodes'][1]['artifacts']['export_code']=self.ref(code)
        p=self.write('export2.json',d);self.refuse(s.importer,p,digest(p),self.roots)

    # --- reçu professeur falsifié ---
    def test_recu_professeur_non_conforme(self):
        obs=self.obs();ans=self.answer();res=self.write('response.json',ans)
        for over in ({'type':'system'},{'subtype':'error'},{'is_error':None},{'num_turns':0},{'num_turns':True},{'modelUsage':{}},
                     {'modelUsage':{'eco-muse':{}}},{'result':'pas du json'},{'result':''}):
            with self.subTest(over=over):
                self.refuse(s.valider_reponse,obs,res,self.receipt(ans,**over),self.roots,'gemini-eleve')

    def test_recu_avec_resultat_falsifie(self):
        obs=self.obs();ans=self.answer();res=self.write('response.json',ans)
        autre=self.answer(('h1',))
        self.refuse(s.valider_reponse,obs,res,self.receipt(autre),self.roots,'gemini-eleve')
        # espaces de formatage admis : la comparaison se fait sur l'objet JSON relu
        self.assertEqual(s.valider_reponse(obs,res,self.receipt(' '+json.dumps(ans)+'\n'),self.roots,'gemini-eleve')['hypotheses'],ans)
        self.refuse(s.valider_reponse,obs,res,self.receipt(json.dumps(ans)+'{}'),self.roots,'gemini-eleve')
        # clé dupliquée dans le résultat : refus, pas de dernière-valeur-gagne
        dup=json.dumps(ans)[:-1]+',"workflow":[]}'
        self.refuse(s.valider_reponse,obs,res,self.receipt(dup),self.roots,'gemini-eleve')

    def test_reponse_contractuellement_invalide(self):
        obs=self.obs()
        for bad in ({'workflow':[],'sous_taches':[]}, {'workflow':[{'texte':'','sources':['m1']}],'sous_taches':[],'indices_fonction':[]},
                    {'workflow':[{'texte':'x'*501,'sources':['m1']}],'sous_taches':[],'indices_fonction':[]},
                    {'workflow':[{'texte':'x','sources':['m1','m1']}],'sous_taches':[],'indices_fonction':[]},
                    {'workflow':[{'texte':'x','sources':[]}],'sous_taches':[],'indices_fonction':[]},
                    {'workflow':[{'texte':'x','sources':['m1'],'note':'extra'}],'sous_taches':[],'indices_fonction':[]},
                    {'workflow':[{'texte':'x','sources':['m1']}]*4,'sous_taches':[],'indices_fonction':[]},
                    [{'texte':'x','sources':['m1']}],
                    {'workflow':[{'texte':'x','sources':['m1']}],'sous_taches':[],'indices_fonction':[],'extra':[]}):
            with self.subTest(bad=bad):
                res=self.write('bad-answer.json',bad);self.refuse(s.valider_reponse,obs,res,self.receipt(bad),self.roots,'gemini-eleve')

    # --- candidat falsifié ---
    def test_candidat_modifie_est_refuse(self):
        obs,res,rec,cand=self.valid_candidate()
        self.assertEqual(s.consulter(self.write('ok.json',cand),self.roots)['statut'],'lecture_rnd_non_promue')
        mutations={'promotion':('memory_promotion','promoted'),'revue':('human_review','approved'),'brief':('amd2_brief_id','AMD2-1'),
                   'statut':('status','candidate_promue'),'schema':('schema','nexora.sync.autre')}
        for name,(key,value) in mutations.items():
            with self.subTest(name=name):
                d=json.loads(json.dumps(cand));d[key]=value
                self.refuse(s.consulter,self.write('cand-'+name+'.json',d),self.roots)
        d=json.loads(json.dumps(cand));d['hypotheses']['workflow'][0]['texte']='hypothèse injectée'
        self.refuse(s.consulter,self.write('cand-hyp.json',d),self.roots)
        d=json.loads(json.dumps(cand));d['teacher_alias']='muse'
        self.refuse(s.consulter,self.write('cand-alias.json',d),self.roots)
        d=json.loads(json.dumps(cand));d['teacher_receipt']['sha256']='0'*64
        self.refuse(s.consulter,self.write('cand-ref.json',d),self.roots)

    def test_candidat_apres_alteration_des_preuves(self):
        obs,res,rec,cand=self.valid_candidate();out=self.write('cand.json',cand)
        rec.write_text(json.dumps({'type':'result','subtype':'success','is_error':False,'num_turns':1,'modelUsage':{'eco-gemini-eleve':{}},'result':json.dumps(self.answer(('h1',)))}))
        self.refuse(s.consulter,out,self.roots)

    def test_candidat_tronque_ou_non_dict(self):
        for value in ([], {'schema':s.CAND}, {'schema':s.CAND,'status':'candidate_non_promue','memory_promotion':'none','human_review':'pending','amd2_brief_id':None}):
            with self.subTest(value=value):
                self.refuse(s.consulter,self.write('cand-bad.json',value),self.roots)

    def test_observations_alterees_ou_non_dict(self):
        obs=self.obs();d=json.loads(obs.read_text());d['episodes'][0]['run_id']='falsifié'
        self.refuse(s.valider_reponse,self.write('obs-bad.json',d),self.write('r.json',self.answer()),
                    self.receipt(self.answer()),self.roots,'gemini-eleve')
        self.refuse(s.prompt,self.write('obs-list.json',[]),self.roots)

    # --- CLI ---
    def test_cli_refus_recu_falsifie_et_candidat_falsifie(self):
        obs=self.obs();ans=self.answer();res=self.write('response.json',ans);bad=self.receipt(ans,result=json.dumps(self.answer(('h1',))));request=self.write('request.json',s.prompt(obs,self.roots))
        _,_,_,cand=self.valid_candidate();cand['human_review']='approved';cf=self.write('cand-fals.json',cand)
        with contextlib.redirect_stdout(io.StringIO()) as o, contextlib.redirect_stderr(io.StringIO()) as e:
            self.assertEqual(s.main(['--root',str(self.root),'--output-root',str(self.root),'valider','--observations',str(obs),'--reponse',str(res),'--receipt',str(bad),'--teacher','gemini-eleve','--request',str(request),'--request-sha256',digest(request),'--output',str(self.root/'c1.json')]),1)
            self.assertEqual(s.main(['--root',str(self.root),'--output-root',str(self.root),'consulter','--candidat',str(cf),'--output',str(self.root/'c2.json')]),1)
        self.assertNotIn('ok',json.loads(o.getvalue() or '{}').get('status',''))
        self.assertIn('refuse',e.getvalue())
        self.assertFalse((self.root/'c1.json').exists());self.assertFalse((self.root/'c2.json').exists())


if __name__=='__main__':unittest.main()
