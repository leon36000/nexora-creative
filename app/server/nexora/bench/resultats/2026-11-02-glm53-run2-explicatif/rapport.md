# Banc de montage 2026-11-02-glm53-run2-explicatif
Modèle z-ai/glm-5.3 ; 2 briefs × 3 répétitions ; 18 appels ; 135298 jetons ; 0.269 USD (plafond 0.8)

| Bras | score brut [IC95] | score avec repli [IC95] | EDL valide 1er coup | repli | USD/essai | jetons/essai |
|---|---|---|---|---|---|---|
| montage_auto (code seul) | 0.907 [0.883 ; 0.931] | 0.907 [0.883 ; 0.931] | 100 % | 0 % | 0.000 | 0 |
| GLM tel quel | 0.703 [0.529 ; 0.877] | 0.850 [0.824 ; 0.877] | 83 % | 17 % | 0.008 | 5552 |
| GLM + exemplaire + validateur + 1 critique | 0.906 [0.894 ; 0.917] | 0.906 [0.894 ; 0.917] | 100 % | 0 % | 0.037 | 16998 |

Comparaisons appariées par brief (différence de score, IC95 bootstrap sur les briefs ; « brut » = invalide compte 0) :
| B − A | brut : Δ [IC95] | avec repli : Δ [IC95] | briefs |
|---|---|---|---|
| a0 − code | -0.204 [-0.353 ; -0.055] | -0.057 [-0.059 ; -0.055] | 2 |
| a1 − code | -0.002 [-0.014 ; 0.011] | -0.002 [-0.014 ; 0.011] | 2 |
| a1 − a0 | +0.203 [0.040 ; 0.365] | +0.055 [0.040 ; 0.070] | 2 |

Par partition (score avec repli moyen) :
| Partition | code | a0 | a1 |
|---|---|---|---|
| apprentissage | 0.883 | 0.824 | 0.894 |
| validation | 0.931 | 0.877 | 0.917 |
