# Campagne a1 : 56 essais, 0.241 USD fournisseur

## 1. Par palier (tous tours, hors v0) : score avec les IC95 bootstrap sur les briefs

| Palier | essais | score brut [IC95] | tournage valide 1er coup | montage valide 1er coup | repli | USD / film | crédits / film | jetons (lus/écrits) | latence |
|---|---|---|---|---|---|---|---|---|---|
| eco | 16 | 0.394 [0.225 ; 0.561] | 75 % | 19 % | 56 % | 0.0008 | 0.12 | 5914 / 2295 | 31 s |
| equilibre | 16 | 0.854 [0.740 ; 0.917] | 75 % | 13 % | 6 % | 0.0012 | 0.18 | 4362 / 4172 | 40 s |
| expert | 16 | 0.930 [0.913 ; 0.948] | 81 % | 56 % | 0 % | 0.0129 | 1.99 | 3700 / 1852 | 31 s |

## 2. Effet de la mémoire (allumée − éteinte, apparié par brief, tours 1 à 3)

| Palier | éteinte | allumée | Δ [IC95] |
|---|---|---|---|
| eco | 0.222 [0.000 ; 0.538] | 0.567 [0.229 ; 0.810] | +0.345 [-0.117 ; 0.706] (n=8) |
| equilibre | 0.917 [0.906 ; 0.927] | 0.791 [0.558 ; 0.918] | -0.126 [-0.363 ; 0.006] (n=8) |
| expert | 0.922 [0.909 ; 0.936] | 0.938 [0.912 ; 0.966] | +0.017 [-0.005 ; 0.041] (n=8) |

## 3. Évolution par tour (la mémoire grossit entre les tours)

| Palier | Mémoire | tour 1 | tour 2 | tour 3 | Δ tour 3 − tour 1 [IC95] | USD/film t1 → t3 |
|---|---|---|---|---|---|---|

## 4. Ancien harnais (EditPlan brut, un appel, sans mémoire) contre la liste compacte (palier Éco, tour 1, mémoire éteinte, même matière)

| Harnais | valide 1er coup | repli | score brut | USD/film |
|---|---|---|---|---|
| v0 (EditPlan brut) | 13 % | 88 % | 0.092 [0.000 ; 0.277] | 0.0004 |
| liste compacte + validateur + 2 réparations | 0 % | 75 % | 0.222 [0.000 ; 0.538] | 0.0009 |

Δ liste − v0 : +0.129 [-0.185 ; 0.466] (n=8)

## 5. Par brief (score moyen, tours et mémoires confondus)

| Brief | eco | equilibre | expert |
|---|---|---|---|
| workstudio | 0.00 | 0.90 | 0.96 |
| nexora | 0.47 | 0.94 | 0.97 |
| creative | 0.87 | 0.89 | 0.91 |
| reception | 0.45 | 0.92 | 0.91 |
| surveillance | 0.00 | 0.90 | 0.92 |
| infra | 0.44 | 0.91 | 0.90 |
| modeles | 0.46 | 0.91 | 0.92 |
| opsys | 0.47 | 0.47 | 0.95 |

## 6. Métriques du composite (moyennes, hors v0)

| Palier | rythme | battues | doublons | texte | audio |
|---|---|---|---|---|---|
| eco | 0.70 | 1.00 | 0.96 | 0.99 | 1.00 |
| equilibre | 0.75 | 1.00 | 0.91 | 0.99 | 1.00 |
| expert | 0.79 | 1.00 | 0.95 | 1.00 | 1.00 |

Causes des replis (10) : duree_cible ×5, texte_trop_long ×4, meme_source ×1, dans_la_source ×1, accroche ×1
