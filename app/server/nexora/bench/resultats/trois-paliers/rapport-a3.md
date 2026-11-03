# Campagne a3 : 56 essais, 0.233 USD fournisseur

## 1. Par palier (tous tours, hors v0) : score avec les IC95 bootstrap sur les briefs

| Palier | essais | score brut [IC95] | tournage valide 1er coup | montage valide 1er coup | repli | USD / film | crédits / film | jetons (lus/écrits) | latence |
|---|---|---|---|---|---|---|---|---|---|
| eco | 16 | 0.797 [0.637 ; 0.912] | 75 % | 31 % | 13 % | 0.0007 | 0.11 | 4973 / 2168 | 35 s |
| equilibre | 16 | 0.923 [0.912 ; 0.933] | 81 % | 31 % | 0 % | 0.0011 | 0.18 | 4139 / 4177 | 40 s |
| expert | 16 | 0.939 [0.922 ; 0.956] | 88 % | 50 % | 0 % | 0.0125 | 1.93 | 3736 / 1771 | 32 s |

## 2. Effet de la mémoire (allumée − éteinte, apparié par brief, tours 1 à 3)

| Palier | éteinte | allumée | Δ [IC95] |
|---|---|---|---|
| eco | 0.674 [0.343 ; 0.905] | 0.920 [0.910 ; 0.929] | +0.246 [0.012 ; 0.582] (n=8) |
| equilibre | 0.927 [0.921 ; 0.932] | 0.919 [0.901 ; 0.936] | -0.008 [-0.024 ; 0.007] (n=8) |
| expert | 0.937 [0.922 ; 0.949] | 0.942 [0.918 ; 0.967] | +0.005 [-0.013 ; 0.022] (n=8) |

## 3. Évolution par tour (la mémoire grossit entre les tours)

| Palier | Mémoire | tour 1 | tour 2 | tour 3 | Δ tour 3 − tour 1 [IC95] | USD/film t1 → t3 |
|---|---|---|---|---|---|---|

## 4. Ancien harnais (EditPlan brut, un appel, sans mémoire) contre la liste compacte (palier Éco, tour 1, mémoire éteinte, même matière)

| Harnais | valide 1er coup | repli | score brut | USD/film |
|---|---|---|---|---|
| v0 (EditPlan brut) | 0 % | 100 % | 0.000 [0.000 ; 0.000] | 0.0004 |
| liste compacte + validateur + 2 réparations | 25 % | 25 % | 0.674 [0.343 ; 0.905] | 0.0008 |

Δ liste − v0 : +0.674 [0.342 ; 0.905] (n=8)

## 5. Par brief (score moyen, tours et mémoires confondus)

| Brief | eco | equilibre | expert |
|---|---|---|---|
| workstudio | 0.46 | 0.94 | 0.97 |
| nexora | 0.94 | 0.94 | 0.96 |
| creative | 0.89 | 0.91 | 0.91 |
| reception | 0.89 | 0.92 | 0.93 |
| surveillance | 0.91 | 0.92 | 0.91 |
| infra | 0.91 | 0.91 | 0.94 |
| modeles | 0.90 | 0.91 | 0.92 |
| opsys | 0.47 | 0.94 | 0.97 |

## 6. Métriques du composite (moyennes, hors v0)

| Palier | rythme | battues | doublons | texte | audio |
|---|---|---|---|---|---|
| eco | 0.73 | 1.00 | 0.96 | 0.99 | 1.00 |
| equilibre | 0.77 | 1.00 | 0.95 | 1.00 | 1.00 |
| expert | 0.81 | 1.00 | 1.00 | 0.98 | 1.00 |

Causes des replis (2) : dans_la_source ×1, texte_trop_long ×1
