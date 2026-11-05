/**
 * Mode Marketing (vague 2) : kit de marque, puis une phrase → 3 propositions → on choisit → on retouche → PDF/PNG/SVG.
 * Surface simple (brief, trois cartes, quelques champs), panneau expert replié (calques, polices, interligne).
 * Tout le calcul (rendu, contrôle préliminaire) est fait par le serveur ; ici on ne tient que l'état de la spec.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { marketing, type CalqueTexteUi, type Constat, type KitMarque, type MarqueEtat, type PropositionUi, type RenduMarketing, type SpecUi } from '../api';
import { setParams, useRoute } from '../router';
import { toast } from '../store';
import { NEXORA_PRODUCT_NAMES } from '../../shared/productNames.js';
import '../marketing.css';

const VIDE: KitMarque = {
  nom: '', logo: {}, couleurs: { primaire: '#1F4E5F', secondaire: '#E6EEF0', accent: '#E07A2F', encre: '#14181B', papier: '#FBFAF7' },
  polices: { titre: 'fraunces', texte: 'inter' }, ton: { adjectifs: [], interdits: [] },
  contact: { entreprise: '', nom: '', titre: '', adresse: '', telephone: '', courriel: '', web: '' }, langue: 'fr',
};
const PIECES: Record<string, string> = { 'carte-affaires': 'Carte d’affaires', 'flyer-lettre': 'Dépliant', 'accroche-porte': 'Accroche-porte', 'flyer-a5': 'Dépliant A5', 'affiche-18x24': 'Affiche' };
const ordre = ['carte-affaires', 'flyer-lettre', 'accroche-porte', 'affiche-18x24', 'flyer-a5'];
const lib: Record<string, string> = { accroche: 'Accroche', sousTitre: 'Sous-titre', point1: 'Point 1', point2: 'Point 2', point3: 'Point 3', appel: 'Appel à l’action', offre: 'Pastille d’offre', nom: 'Nom', titre: 'Titre' };
const CHAMPS_PAR_PIECE: Record<string, string[]> = {
  'carte-affaires': ['accroche', 'nom', 'titre'],
  'flyer-lettre': ['accroche', 'sousTitre', 'point1', 'point2', 'point3', 'appel', 'offre'],
  'flyer-a5': ['accroche', 'sousTitre', 'point1', 'point2', 'point3', 'appel', 'offre'],
  'affiche-18x24': ['accroche', 'sousTitre', 'point1', 'point2', 'point3', 'appel', 'offre'],
  'accroche-porte': ['accroche', 'sousTitre', 'point1', 'point2', 'point3', 'appel'],
};

export default function MarketingPage() {
  const { params } = useRoute();
  const [etat, setEtat] = useState<MarqueEtat | null>(null);
  const [erreur, setErreur] = useState('');
  const charger = useCallback(() => marketing.marque().then(setEtat).catch((e) => setErreur(String(e.message ?? e))), []);
  useEffect(() => { charger(); }, [charger]);
  const onglet = params.get('onglet') ?? (etat && !etat.kit ? 'marque' : 'creer');
  return (
    <div className="page-scroll">
      <div className="page-pad mk">
        <h1 className="display mk-h1">{NEXORA_PRODUCT_NAMES.campaign} <span className="hl">sur ta marque</span></h1>
        <p className="dim mk-lead">Cartes, dépliants et accroche-portes en PDF prêts pour l’imprimeur (fond perdu, traits de coupe). Ta marque est saisie une fois ; chaque pièce la reprend.</p>
        <div className="mk-tabs" role="tablist">
          <button role="tab" aria-selected={onglet === 'creer'} className={onglet === 'creer' ? 'on' : ''} onClick={() => setParams({ onglet: 'creer' })}>Créer une pièce</button>
          <button role="tab" aria-selected={onglet === 'marque'} className={onglet === 'marque' ? 'on' : ''} onClick={() => setParams({ onglet: 'marque' })}>Ma marque{etat && !etat.kit ? ' •' : ''}</button>
        </div>
        {erreur && <p className="mk-err">{erreur}</p>}
        {!etat && !erreur && <p className="dim">Chargement…</p>}
        {etat && onglet === 'marque' && <PanneauMarque etat={etat} onSaved={() => { charger(); setParams({ onglet: 'creer' }); }} />}
        {etat && onglet !== 'marque' && (etat.kit ? <Creer etat={etat} kit={etat.kit} /> : <p className="mk-card">Commence par renseigner ta marque : <button className="btn accent" onClick={() => setParams({ onglet: 'marque' })}>Ma marque</button></p>)}
      </div>
    </div>
  );
}

// ---------------- Ma marque ----------------
function PanneauMarque({ etat, onSaved }: { etat: MarqueEtat; onSaved: () => void }) {
  const [kit, setKit] = useState<KitMarque>(etat.kit ?? VIDE);
  const [ctl, setCtl] = useState(etat.controles);
  const [dom, setDom] = useState<{ couleurs: string[]; palette: KitMarque['couleurs'] } | null>(null);
  const [avis, setAvis] = useState<string[]>([]);
  const [pistes, setPistes] = useState<Awaited<ReturnType<typeof marketing.logos>> | null>(null);
  const [devisLogo, setDevisLogo] = useState<string>('');
  const [occupe, setOccupe] = useState(false);
  const set = <K extends keyof KitMarque>(k: K, v: KitMarque[K]) => setKit((x) => ({ ...x, [k]: v }));
  const contact = (k: keyof KitMarque['contact'], v: string) => setKit((x) => ({ ...x, contact: { ...x.contact, [k]: v } }));
  const couleur = (k: keyof KitMarque['couleurs'], v: string) => setKit((x) => ({ ...x, couleurs: { ...x.couleurs, [k]: v.toUpperCase() } }));
  const liste = (s: string) => s.split(',').map((x) => x.trim()).filter(Boolean);

  const televerser = async (f: File | undefined) => {
    if (!f) return;
    try {
      const svg = f.type === 'image/svg+xml' || f.name.toLowerCase().endsWith('.svg');
      const donnees = svg ? await f.text() : btoa(String.fromCharCode(...new Uint8Array(await f.arrayBuffer())));
      const r = await marketing.logo(svg ? 'svg' : 'png', donnees);
      setKit((x) => ({ ...x, logo: r.logo }));
      setAvis(r.controle.avertissements);
      setDom({ couleurs: r.couleurs, palette: r.palette });
    } catch (e) { toast(e instanceof Error ? e.message : 'Logo illisible', true); }
  };
  const enregistrer = async () => {
    setOccupe(true);
    try { const r = await marketing.enregistrer({ ...kit, contact: { ...kit.contact, entreprise: kit.contact.entreprise || kit.nom } }); setCtl(r.controles); toast('Marque enregistrée'); onSaved(); }
    catch (e) { toast(e instanceof Error ? e.message : 'Enregistrement impossible', true); }
    setOccupe(false);
  };
  const devisPistes = async () => { const d = await marketing.devis('logos'); setDevisLogo(`≈ ${d.credits} crédit${d.credits > 1 ? 's' : ''} (${d.libelle}) · plafond réservé ${d.creditsReserves}`); };
  const contrastes = ctl?.contrastes ?? [];

  return (
    <div className="mk-grid">
      <section className="mk-card">
        <h2>Identité</h2>
        <label>Nom de la marque<input value={kit.nom} maxLength={80} onChange={(e) => set('nom', e.target.value)} placeholder="Ex. Plomberie Source-Vive" /></label>
        <div className="mk-logo">
          <div className="mk-logo-prev" aria-label="Aperçu du logo">
            {kit.logo.svg ? <span dangerouslySetInnerHTML={{ __html: kit.logo.svg }} /> : kit.logo.png ? <img src={kit.logo.png} alt="Logo" /> : <span className="dim">Aucun logo</span>}
          </div>
          <div>
            <label className="btn">Téléverser un logo (SVG ou PNG)<input type="file" accept=".svg,image/svg+xml,image/png" hidden onChange={(e) => televerser(e.target.files?.[0])} /></label>
            {avis.map((a) => <p key={a} className="mk-note">{a}</p>)}
            {dom && dom.couleurs.length > 0 && (
              <p className="mk-note">Couleurs du logo : {dom.couleurs.map((c) => <i key={c} className="mk-sw" style={{ background: c }} title={c} />)} <button className="btn" onClick={() => set('couleurs', dom.palette)}>Les appliquer à ma palette</button></p>
            )}
            <button className="btn" onClick={devisPistes}>Pas de logo ? 4 pistes</button>
            {devisLogo && (
              <p className="mk-note">Devis : {devisLogo} <button className="btn accent" disabled={!kit.nom || occupe} onClick={async () => {
                setOccupe(true);
                try { await marketing.enregistrer({ ...kit, contact: { ...kit.contact, entreprise: kit.contact.entreprise || kit.nom } }); setPistes(await marketing.logos(`${kit.nom} ${kit.ton.adjectifs.join(' ')}`)); }
                catch (e) { toast(e instanceof Error ? e.message : 'Pistes impossibles', true); }
                setOccupe(false);
              }}>Lancer</button></p>
            )}
          </div>
        </div>
        {pistes && (
          <div className="mk-pistes">
            {pistes.pistes.map((p) => (
              <button key={p.nom} className="mk-piste" onClick={() => { set('logo', { svg: p.svg }); setPistes(null); }} title={p.idee}>
                <span dangerouslySetInnerHTML={{ __html: p.svg }} /><b>{p.nom}</b><small>{p.origine === 'ia' ? 'Idée du modèle' : 'Généré par le code'}</small>
              </button>
            ))}
            {pistes.avertissements.map((a) => <p key={a} className="mk-note">{a}</p>)}
            <p className="mk-note">{pistes.usage.palier ? `Facturé : ${pistes.usage.credits.toFixed(2)} crédit (devis ${pistes.usage.devisCredits}).` : 'Aucun crédit utilisé.'}</p>
          </div>
        )}
        <label>Langue<select value={kit.langue} onChange={(e) => set('langue', e.target.value as 'fr' | 'en')}><option value="fr">Français (Canada)</option><option value="en">English (Canada)</option></select></label>
      </section>

      <section className="mk-card">
        <h2>Couleurs et polices</h2>
        <div className="mk-couleurs">
          {(['primaire', 'secondaire', 'accent', 'encre', 'papier'] as const).map((k) => (
            <label key={k} className="mk-col"><span>{k[0].toUpperCase() + k.slice(1)}</span><input type="color" value={kit.couleurs[k]} onChange={(e) => couleur(k, e.target.value)} /><code>{kit.couleurs[k]}</code></label>
          ))}
        </div>
        <ul className="mk-contr">
          {contrastes.slice(0, 4).map((c, i) => <li key={i} className={c.aa ? 'ok' : c.aaGrandTexte ? 'mid' : 'bad'}><i style={{ background: c.fond, color: c.texte }}>Aa</i>{c.ratio}:1 {c.aa ? 'lisible' : c.aaGrandTexte ? 'gros texte seulement' : 'trop faible'}</li>)}
        </ul>
        <p className="mk-note">Les contrastes se mettent à jour à l’enregistrement (norme AA : 4,5:1).</p>
        <div className="mk-2">
          <label>Police des titres<select value={kit.polices.titre} onChange={(e) => set('polices', { ...kit.polices, titre: e.target.value })}>{etat.polices.map((p) => <option key={p.id} value={p.id}>{p.nom}</option>)}</select></label>
          <label>Police du texte<select value={kit.polices.texte} onChange={(e) => set('polices', { ...kit.polices, texte: e.target.value })}>{etat.polices.map((p) => <option key={p.id} value={p.id}>{p.nom}</option>)}</select></label>
        </div>
        <label>Ton (3 adjectifs, séparés par des virgules)<input value={kit.ton.adjectifs.join(', ')} onChange={(e) => set('ton', { ...kit.ton, adjectifs: liste(e.target.value).slice(0, 3) })} placeholder="chaleureux, fiable, simple" /></label>
        <label>Mots à éviter<input value={kit.ton.interdits.join(', ')} onChange={(e) => set('ton', { ...kit.ton, interdits: liste(e.target.value) })} placeholder="meilleur, garanti" /></label>
      </section>

      <section className="mk-card">
        <h2>Coordonnées</h2>
        <p className="mk-note">Un champ vide disparaît de la pièce, sans trou.</p>
        {([['entreprise', 'Entreprise'], ['nom', 'Nom de la personne'], ['titre', 'Titre'], ['telephone', 'Téléphone'], ['courriel', 'Courriel'], ['web', 'Site web'], ['adresse', 'Adresse']] as const).map(([k, l]) => (
          <label key={k}>{l}<input value={kit.contact[k]} onChange={(e) => contact(k, e.target.value)} /></label>
        ))}
        <button className="btn accent mk-save" disabled={!kit.nom.trim() || occupe} onClick={enregistrer}>{occupe ? 'Enregistrement…' : 'Enregistrer ma marque'}</button>
      </section>
    </div>
  );
}

// ---------------- Créer ----------------
function Creer({ etat, kit }: { etat: MarqueEtat; kit: KitMarque }) {
  const formats = useMemo(() => etat.formats.filter((f) => f.gabarits.length).sort((a, b) => ordre.indexOf(a.id) - ordre.indexOf(b.id)), [etat]);
  const [format, setFormat] = useState(formats[0]?.id ?? 'carte-affaires');
  const [phrase, setPhrase] = useState('');
  const [devis, setDevis] = useState<string>('');
  const [props, setProps] = useState<PropositionUi[] | null>(null);
  const [infos, setInfos] = useState<string[]>([]);
  const [occupe, setOccupe] = useState(false);
  const [choix, setChoix] = useState<SpecUi | null>(null);
  const [apercus, setApercus] = useState<Record<string, string>>({});

  useEffect(() => { marketing.devis('propositions').then((d) => setDevis(`≈ ${d.credits} crédit${d.credits > 1 ? 's' : ''} (${d.libelle})`)).catch(() => setDevis('')); }, []);
  const fmt = formats.find((f) => f.id === format);

  const proposer = async () => {
    setOccupe(true); setProps(null); setChoix(null); setInfos([]);
    try {
      const r = await marketing.propositions(phrase, format);
      setProps(r.propositions);
      setInfos([...r.avertissements, r.sansIA ? 'Aucun texte écrit par le modèle : saisis tes textes après avoir choisi.' : `Écrit au palier ${r.palier}${r.escalades ? ` (après ${r.escalades} escalade)` : ''} · facturé ${r.usage.credits.toFixed(2)} crédit (devis ${r.usage.devisCredits}, plafond réservé par le serveur).`]);
      // aperçus : un rendu par proposition, en file côté serveur
      for (const p of r.propositions) marketing.rendu(p.spec, false).then((x) => { const png = x.fichiers.find((f) => f.genre === 'png'); if (png) setApercus((a) => ({ ...a, [p.gabarit]: png.url })); }).catch(() => {});
    } catch (e) { toast(e instanceof Error ? e.message : 'Propositions impossibles', true); }
    setOccupe(false);
  };

  return (
    <div className="mk-creer">
      <section className="mk-card">
        <h2>1. Que veux-tu créer ?</h2>
        <div className="mk-pieces" role="radiogroup" aria-label="Type de pièce">
          {formats.map((f) => <button key={f.id} role="radio" aria-checked={format === f.id} className={format === f.id ? 'on' : ''} onClick={() => { setFormat(f.id); setProps(null); setChoix(null); }}><b>{PIECES[f.id] ?? f.nom}</b><small>{f.nom.replace(/^(Carte d’affaires|Dépliant Lettre|Dépliant A5|Accroche-porte|Affiche|Brochure DL)\s*/, '')}</small></button>)}
        </div>
        <label>En une phrase
          <textarea rows={2} maxLength={400} value={phrase} onChange={(e) => setPhrase(e.target.value)} placeholder="Ex. carte d’affaires pour une plombière à Sherbrooke, ton chaleureux" />
        </label>
        <div className="mk-actions">
          <button className="btn accent" disabled={!phrase.trim() || occupe} onClick={proposer}>{occupe ? 'Je prépare 3 propositions…' : 'Proposer 3 compositions'}</button>
          {devis && <span className="mk-note">Devis : {devis}. Le rendu et les exports sont gratuits.</span>}
        </div>
        {infos.map((i) => <p key={i} className="mk-note">{i}</p>)}
      </section>

      {props && !choix && (
        <section className="mk-card">
          <h2>2. Choisis une composition</h2>
          <div className="mk-props">
            {props.map((p) => (
              <button key={p.gabarit} className="mk-prop" onClick={() => setChoix(p.spec)}>
                <span className="mk-thumb">{apercus[p.gabarit] ? <img src={apercus[p.gabarit]} alt={`Aperçu ${p.nom}`} /> : <i className="dim">Aperçu…</i>}</span>
                <b>{p.nom}</b><small>{p.variables.accroche ?? p.pourquoi}</small>
                {p.retires.length > 0 && <small className="mk-warn">Texte retiré : {p.retires[0]}</small>}
              </button>
            ))}
          </div>
        </section>
      )}

      {choix && fmt && <Editeur key={choix.gabarit + choix.format} kit={kit} format={fmt} depart={choix} cmjn={etat.cmjn} onRetour={() => setChoix(null)} />}
    </div>
  );
}

function Editeur({ kit, format, depart, cmjn, onRetour }: { kit: KitMarque; format: MarqueEtat['formats'][number]; depart: SpecUi; cmjn: boolean; onRetour: () => void }) {
  const [spec, setSpec] = useState<SpecUi>(depart);
  const [palette, setPalette] = useState<'defaut' | 'inverse' | 'sombre'>('defaut');
  const [face, setFace] = useState(0);
  const [rendu, setRendu] = useState<RenduMarketing | null>(null);
  const [occupe, setOccupe] = useState(false);
  const [cm, setCm] = useState(false);
  const minuterie = useRef<number | undefined>(undefined);
  const seq = useRef(0);

  // aperçu en direct : rendu serveur (≈ 0,3 s) après chaque modification
  useEffect(() => {
    window.clearTimeout(minuterie.current);
    minuterie.current = window.setTimeout(() => {
      const n = ++seq.current;
      setOccupe(true);
      marketing.rendu(spec, cm).then((r) => { if (n === seq.current) setRendu(r); }).catch((e) => toast(e instanceof Error ? e.message : 'Rendu impossible', true)).finally(() => { if (n === seq.current) setOccupe(false); });
    }, 350);
    return () => window.clearTimeout(minuterie.current);
  }, [spec, cm]);

  const pngs = rendu?.fichiers.filter((f) => f.genre === 'png') ?? [];
  const champs = CHAMPS_PAR_PIECE[format.id] ?? ['accroche'];
  const variable = (k: string, v: string) => setSpec((s) => ({ ...s, variables: { ...s.variables, [k]: v } }));
  const refaire = async (g: string, pal: typeof palette) => {
    try { const r = await marketing.spec({ gabarit: g, format: format.id, variables: spec.variables, palette: pal }); setSpec(r.spec); setPalette(pal); setFace(0); }
    catch (e) { toast(e instanceof Error ? e.message : 'Changement impossible', true); }
  };
  const texteCalques = spec.faces.flatMap((f, fi) => f.calques.filter((c) => c.type === 'texte').map((c) => ({ fi, c: c as unknown as CalqueTexteUi })));
  const majCalque = (fi: number, id: string, patch: Partial<CalqueTexteUi>) => setSpec((s) => ({ ...s, faces: s.faces.map((f, i) => (i === fi ? { ...f, calques: f.calques.map((c) => (c.id === id ? { ...c, ...patch } : c)) } : f)) }));
  const fichier = (g: string) => rendu?.fichiers.find((f) => f.genre === g);
  const constats: Constat[] = rendu?.controle.constats.filter((c) => c.gravite !== 'info') ?? [];

  return (
    <section className="mk-card mk-edit">
      <div className="mk-edit-head">
        <h2>3. Retouche et exporte</h2>
        <button className="btn" onClick={onRetour}>← Autres compositions</button>
      </div>
      <div className="mk-edit-grid">
        <div className="mk-prev">
          <div className="mk-faces" role="tablist">{spec.faces.filter((f) => f.genre === 'art').map((f, i) => <button key={f.nom} className={face === i ? 'on' : ''} onClick={() => setFace(i)}>{f.nom}</button>)}</div>
          <div className={`mk-view ${occupe ? 'busy' : ''}`}>{pngs[face] ? <img src={pngs[face].url} alt={`Aperçu ${spec.faces[face]?.nom}`} /> : <i className="dim">Rendu…</i>}</div>
          <p className="mk-note">{rendu ? `Rendu en ${rendu.ms} ms · fond perdu ${(spec as any).fondPerdu} mm` : ''}</p>
        </div>
        <div className="mk-ctl">
          <h3>Compositions et couleurs</h3>
          <div className="mk-chips">
            {format.gabarits.map((g) => <button key={g.id} className={spec.gabarit === g.id ? 'on' : ''} title={g.description} onClick={() => refaire(g.id, palette)}>{g.nom}</button>)}
          </div>
          <div className="mk-chips" aria-label="Palette">
            {([['defaut', 'Palette d’origine'], ['inverse', 'Couleurs inversées'], ['sombre', 'Version sombre']] as const).map(([p, l]) => <button key={p} className={palette === p ? 'on' : ''} onClick={() => refaire(spec.gabarit, p)}>{l}</button>)}
          </div>
          <h3>Textes</h3>
          {champs.map((k) => (
            <label key={k}>{lib[k] ?? k}<input value={spec.variables[k] ?? ''} maxLength={k === 'sousTitre' ? 130 : 60} onChange={(e) => variable(k, e.target.value)} /></label>
          ))}
          <details className="mk-expert">
            <summary>Panneau expert : calques, polices, interligne</summary>
            {texteCalques.map(({ fi, c }) => (
              <fieldset key={`${fi}-${c.id}`}>
                <legend>{spec.faces[fi].nom} · {c.id}</legend>
                <textarea rows={2} value={c.texte} onChange={(e) => majCalque(fi, c.id, { texte: e.target.value })} aria-label={`Texte de ${c.id}`} />
                <div className="mk-3">
                  <label>Taille (pt)<input type="number" min={5} max={200} step={0.5} value={c.taille} onChange={(e) => majCalque(fi, c.id, { taille: Number(e.target.value) })} /></label>
                  <label>Interligne<input type="number" min={0.9} max={2.4} step={0.05} value={c.interligne} onChange={(e) => majCalque(fi, c.id, { interligne: Number(e.target.value) })} /></label>
                  <label>Poids<select value={c.poids} onChange={(e) => majCalque(fi, c.id, { poids: Number(e.target.value) })}><option value={400}>Normal</option><option value={600}>Demi-gras</option><option value={700}>Gras</option></select></label>
                </div>
                <label>Police<select value={c.police} onChange={(e) => majCalque(fi, c.id, { police: e.target.value })}>{[['geist', 'Geist'], ['inter', 'Inter'], ['archivo', 'Archivo'], ['fraunces', 'Fraunces'], ['playfair', 'Playfair Display'], ['jetbrains', 'JetBrains Mono']].map(([v, n]) => <option key={v} value={v}>{n}</option>)}</select></label>
              </fieldset>
            ))}
          </details>
          <h3>Contrôle avant l’imprimeur</h3>
          {rendu && constats.length === 0 && <p className="mk-ok">Aucun problème détecté : fond perdu, zone de sécurité, contraste et résolution conformes.</p>}
          <ul className="mk-constats">{constats.map((c, i) => <li key={i} className={c.gravite}>{c.gravite === 'erreur' ? 'À corriger' : 'À vérifier'} : {c.message}</li>)}</ul>
          <h3>Exporter</h3>
          <label className="mk-check"><input type="checkbox" checked={cm} disabled={!cmjn} onChange={(e) => setCm(e.target.checked)} />PDF en CMJN {cmjn ? '(Ghostscript, épreuve conseillée)' : '(indisponible sur ce serveur : PDF en RVB)'}</label>
          <div className="mk-actions">
            <a className={`btn accent ${fichier('pdf-impression') ? '' : 'off'}`} href={fichier('pdf-impression')?.url + '?telecharger=1'} download>PDF imprimeur (traits de coupe)</a>
            <a className={`btn ${fichier('pdf-sans-traits') ? '' : 'off'}`} href={fichier('pdf-sans-traits')?.url + '?telecharger=1'} download>PDF fond perdu</a>
            <a className={`btn ${pngs[0] ? '' : 'off'}`} href={pngs[face]?.url + '?telecharger=1'} download>PNG</a>
            {fichier('svg') && <a className="btn" href={fichier('svg')!.url + '?telecharger=1'} download>SVG</a>}
          </div>
          <p className="mk-note">{(spec as any).format === 'accroche-porte' ? 'La page 3 du PDF est le gabarit de découpe de la poignée (couleur d’accompagnement, à ne pas imprimer).' : 'Le PDF contient une page par face.'} Couleurs vives : demander une épreuve à l’imprimeur.</p>
        </div>
      </div>
    </section>
  );
}
