# Banc de montage 2026-11-02-glm53
Modèle z-ai/glm-5.3 ; 12 briefs × 3 répétitions ; 121 appels ; 775759 jetons ; 1.235 USD (plafond 2.6)

| Bras | score brut [IC95] | score avec repli [IC95] | EDL valide 1er coup | repli | USD/essai | jetons/essai |
|---|---|---|---|---|---|---|
| montage_auto (code seul) | 0.937 [0.922 ; 0.950] | 0.937 [0.922 ; 0.950] | 100 % | 0 % | 0.000 | 0 |
| GLM tel quel | 0.500 [0.320 ; 0.668] | 0.884 [0.857 ; 0.909] | 58 % | 42 % | 0.005 | 3864 |
| GLM + exemplaire + validateur + 1 critique | 0.798 [0.686 ; 0.883] | 0.876 [0.850 ; 0.903] | 53 % | 8 % | 0.029 | 17685 |

Comparaisons appariées par brief (différence de score, IC95 bootstrap sur les briefs ; « brut » = invalide compte 0) :
| B − A | brut : Δ [IC95] | avec repli : Δ [IC95] | briefs |
|---|---|---|---|
| a0 − code | -0.437 [-0.608 ; -0.275] | -0.053 [-0.085 ; -0.025] | 12 |
| a1 − code | -0.139 [-0.250 ; -0.056] | -0.061 [-0.084 ; -0.037] | 12 |
| a1 − a0 | +0.298 [0.121 ; 0.477] | -0.008 [-0.048 ; 0.035] | 12 |

Par partition (score avec repli moyen) :
| Partition | code | a0 | a1 |
|---|---|---|---|
| apprentissage | 0.935 | 0.862 | 0.879 |
| validation | 0.946 | 0.935 | 0.869 |
| test | 0.931 | 0.874 | 0.875 |
