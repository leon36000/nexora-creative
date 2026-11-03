# Campagne a2 : 152 essais, 0.668 USD fournisseur

## 1. Par palier (tous tours, hors v0) : score avec les IC95 bootstrap sur les briefs

| Palier | essais | score brut [IC95] | tournage valide 1er coup | montage valide 1er coup | repli | USD / film | crédits / film | jetons (lus/écrits) | latence |
|---|---|---|---|---|---|---|---|---|---|
| eco | 48 | 0.627 [0.522 ; 0.747] | 71 % | 17 % | 31 % | 0.0008 | 0.12 | 5203 / 2240 | 31 s |
| equilibre | 48 | 0.896 [0.854 ; 0.923] | 73 % | 44 % | 2 % | 0.0011 | 0.16 | 3863 / 3952 | 42 s |
| expert | 48 | 0.936 [0.921 ; 0.952] | 85 % | 67 % | 0 % | 0.0120 | 1.86 | 3326 / 1745 | 30 s |

## 2. Effet de la mémoire (allumée − éteinte, apparié par brief, tours 1 à 3)

| Palier | éteinte | allumée | Δ [IC95] |
|---|---|---|---|
| eco | 0.453 [0.331 ; 0.611] | 0.801 [0.686 ; 0.892] | +0.348 [0.230 ; 0.472] (n=8) |
| equilibre | 0.874 [0.797 ; 0.918] | 0.918 [0.907 ; 0.930] | +0.045 [0.004 ; 0.116] (n=8) |
| expert | 0.931 [0.921 ; 0.942] | 0.941 [0.919 ; 0.963] | +0.009 [-0.004 ; 0.024] (n=8) |

## 3. Évolution par tour (la mémoire grossit entre les tours)

| Palier | Mémoire | tour 1 | tour 2 | tour 3 | Δ tour 3 − tour 1 [IC95] | USD/film t1 → t3 |
|---|---|---|---|---|---|---|
| eco | éteinte | 0.338 | 0.450 | 0.571 | +0.234 [0.008 ; 0.552] (n=8) | 0.0009 → 0.0008 |
| eco | allumée | 0.689 | 0.913 | 0.802 | +0.112 [-0.243 ; 0.468] (n=8) | 0.0007 → 0.0007 |
| equilibre | éteinte | 0.913 | 0.909 | 0.799 | -0.114 [-0.346 ; 0.015] (n=8) | 0.0009 → 0.0010 |
| equilibre | allumée | 0.914 | 0.927 | 0.915 | +0.001 [-0.008 ; 0.013] (n=8) | 0.0010 → 0.0012 |
| expert | éteinte | 0.925 | 0.935 | 0.934 | +0.010 [-0.003 ; 0.024] (n=8) | 0.0121 → 0.0099 |
| expert | allumée | 0.942 | 0.938 | 0.942 | +0.000 [-0.007 ; 0.007] (n=8) | 0.0125 → 0.0129 |

## 4. Ancien harnais (EditPlan brut, un appel, sans mémoire) contre la liste compacte (palier Éco, tour 1, mémoire éteinte, même matière)

| Harnais | valide 1er coup | repli | score brut | USD/film |
|---|---|---|---|---|
| v0 (EditPlan brut) | 0 % | 100 % | 0.000 [0.000 ; 0.000] | 0.0004 |
| liste compacte + validateur + 2 réparations | 13 % | 63 % | 0.338 [0.111 ; 0.675] | 0.0009 |

Δ liste − v0 : +0.338 [0.111 ; 0.672] (n=8)

## 5. Par brief (score moyen, tours et mémoires confondus)

| Brief | eco | equilibre | expert |
|---|---|---|---|
| workstudio | 0.77 | 0.93 | 0.96 |
| nexora | 0.93 | 0.93 | 0.97 |
| creative | 0.75 | 0.89 | 0.91 |
| reception | 0.44 | 0.76 | 0.92 |
| surveillance | 0.46 | 0.91 | 0.92 |
| infra | 0.46 | 0.91 | 0.94 |
| modeles | 0.59 | 0.90 | 0.92 |
| opsys | 0.62 | 0.93 | 0.96 |

## 6. Métriques du composite (moyennes, hors v0)

| Palier | rythme | battues | doublons | texte | audio |
|---|---|---|---|---|---|
| eco | 0.75 | 1.00 | 0.93 | 0.97 | 1.00 |
| equilibre | 0.76 | 1.00 | 0.91 | 0.99 | 1.00 |
| expert | 0.79 | 1.00 | 1.00 | 0.99 | 1.00 |

Causes des replis (16) : texte_trop_long ×9, dans_la_source ×6, plans_distincts ×1, meme_source ×1
