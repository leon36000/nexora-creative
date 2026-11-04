# Synthèse — Turing 8 Go (fidèle à candidats.md, 04-11-2026)
*Aucun benchmark exécuté sur RTX 2080/2070 SUPER ; A=annoncé, E=estimation non vérifiée.*

## 1. Agrandissement vidéo x2/x4
| Candidat | Licence des poids | VRAM ou taille annoncée | Tient en 8 Go sur Turing (oui/non/non vérifié) | Remarque courte |
|---|---|---|---|---|
| Real-ESRGAN x2plus/x4plus | BSD-3-Clause† projet | ≈67 Mo FP32 ; E ≈1–4 Go tuilé | oui | Tuilé, image par image, sans garantie temporelle |
| RealPLKSR 2x/4x MSSIM | MIT | ≈30 Mo FP32, exacte non vérifiée ; E ≈1–4 Go | oui | CNN léger, préférer MSSIM si détails bougent |
| SPAN x2/x4 officiel | Apache-2.0† projet | ≈0,4 M param, ≈1,6 Mo FP32 E ; E ≈1–3 Go | oui | Image seule, cohérence temporelle à mesurer |
| RealBasicVSR x4 / BasicVSR++ | Poids non vérifiée ; code Apache-2.0 | E ≈4–8 Go ou plus, pas de garantie | non vérifié | Vrai temporel, portage torch 2.11 non vérifié |
| SeedVR2-3B Q4/Q8 | Apache-2.0 | 3B FP16 6,78 Go ; Q4 2,00 Go, Q8 3,66 Go + VAE 501 Mo | non vérifié | Expérimental, FP16 résident et 7B irréalistes |

## 2. Interpolation d'images (à 1344×768)
| Candidat | Licence des poids | VRAM ou taille annoncée | Tient en 8 Go sur Turing (oui/non/non vérifié) | Remarque courte |
|---|---|---|---|---|
| Practical-RIFE 4.25/4.26 | MIT poids | ≈22,7 Mo ; A 30+ fps 720p sur 2080 Ti seulement | oui | Premier choix Turing, interpoler avant agrandissement |
| IFRNet-S / IFRNet | MIT† projet | ≈3/20 Mo FP32 E ; E ≈1–4 Go | oui | Petit CNN, comparer sur occlusions et mouvements |
| FILM / film_net | Apache-2.0 | 68,9 Mo FP16 ; E ≈2–6 Go | oui | Patches haute résolution, réaliste tuilé |
| AMT-S | CC-BY-NC-4.0 NC code, poids non vérifiée | ≈0,8 M param, ≈3,2 Mo FP32 E ; E ≈2–6 Go | oui | Plausible 8 Go, signal NC pour studio |
| GIMM-VFI-R-P | S-Lab License 1.0 NC | R-P 79,3 Mo + RAFT 21,1 Mo ; A V100 7932 MiB en 2K | non vérifié | Expérimental, tester à la source seulement |

## 3. Débruitage, artefacts et défloutage
| Candidat | Licence des poids | VRAM ou taille annoncée | Tient en 8 Go sur Turing (oui/non/non vérifié) | Remarque courte |
|---|---|---|---|---|
| FFmpeg hqdn3d/atadenoise/deblock | Aucun poids | 0 Go VRAM, CPU | oui | Choix de base, mémoire bornable |
| FastDVDnet | MIT† projet | ≈2,5 M param, ≈10 Mo FP32 E ; E ≈1–4 Go | oui | Fenêtre 5 images, vrai temporel sans flot |
| SCUNet color real PSNR | Apache-2.0† projet | ≈18 M param, ≈72 Mo FP32 E ; E ≈2–6 Go | oui | Image seule, PSNR en premier |
| NAFNet-width32/64 SIDD/GoPro/REDS | MIT† projet | ≈17/68 M, ≈68/272 Mo FP32 E ; E ≈2–6 Go | oui | Width32 prioritaire, tuilage nécessaire |
| Restormer real_denoising/motion_deblurring | MIT† projet | ≈26 M, ≈104 Mo FP32 E ; E ≈3–8 Go ou plus | non vérifié | Second choix, tuiler, risque contours inventés |

## 4. Transcription et alignement français
| Candidat | Licence des poids | VRAM ou taille annoncée | Tient en 8 Go sur Turing (oui/non/non vérifié) | Remarque courte |
|---|---|---|---|---|
| whisper-large-v3-turbo + faster-whisper | MIT | ≈809 M, 1,62 Go FP16 ; E ≈2–4 Go | oui | Mots estimés, pas alignement forcé dédié |
| WhisperX + wav2vec2-large-xlsr-53-french | Whisper MIT, aligner Apache-2.0 | Aligner 1,26 Go FP32 ; E ≈2–5 Go séparés | oui | Meilleur choix pour réaligner texte corrigé |
| parakeet-tdt-0.6b-v3 | CC-BY-4.0 | 2,51 Go ; Q8 714 Mo ; E ≈2–4 Go FP16 | oui | Runtime sm_75 vérifié, débit non vérifié |
| canary-1b-v2 | CC-BY-4.0 | Archive 6,36 Go ; E ≈3–6 Go | non vérifié | Conditionnel, archive lourde pour 7,7 Go RAM |
| ctc-forced-aligner + mms-300m-1130 | CC-BY-NC-4.0 NC | ≈300 M, ≈1,2 Go FP32 E ; E ≈1–3 Go | non vérifié | Aligne texte fourni, ne transcrit pas |

## 5. Voix française, séparation et nettoyage
| Candidat | Licence des poids | VRAM ou taille annoncée | Tient en 8 Go sur Turing (oui/non/non vérifié) | Remarque courte |
|---|---|---|---|---|
| Kokoro-82M v1.0 ff_siwis | Apache-2.0 | 327 Mo, ≈164 Mo FP16 E ; E ≈0,5–2 Go | oui | Voix fixe, plus simple, pas de clonage |
| Chatterbox Multilingual 500M V2 | MIT | ≈3,21 Go sélectionnés ; E ≈3–6 Go | non vérifié | Clonage par référence, mémoire à confirmer |
| Qwen3-TTS-12Hz-0.6B-Base | Apache-2.0 | 1,83 Go + tokenizer total 2,52 Go ; E ≈3–5 Go | non vérifié | Clonage 3 s annoncé, FP16 sm_75 à valider |
| Demucs v4 htdemucs | MIT† projet | ≈80 Mo par checkpoint ; A ≈3 Go, ≈7 Go défaut | oui | Réaliste, segment ≈7,8 s, tester FP32 |
| DeepFilterNet3 | MIT/Apache-2.0† projet | ≈8–20 Mo E ; 0 Go VRAM en CPU | oui | Nettoyage parole 48 kHz, pas séparateur musical |

## 6. Tri et jugement de prises
| Candidat | Licence des poids | VRAM ou taille annoncée | Tient en 8 Go sur Turing (oui/non/non vérifié) | Remarque courte |
|---|---|---|---|---|
| Qwen3-VL-4B-Instruct Q4 | Apache-2.0 | LLM Q4 2,50 Go + mmproj Q8 454 Mo ; E Q4 ≈4–6 Go | non vérifié | Vidéo native, meilleur compromis à calibrer |
| Qwen3-VL-2B-Instruct Q8 | Apache-2.0 | LLM Q8 1,83 Go + vision ; E Q8 ≈3,5–5 Go | non vérifié | Plus de marge, essayer Q8 avant Q4 |
| SmolVLM2-2.2B-Instruct Q4 | Apache-2.0 | LLM Q4 ≈1,11 Go ; E ≈2–4 Go | non vérifié | Vidéo entraînée, bon pour présélection |
| MiniCPM-V-4_5 int4 | Apache-2.0 fiche 4.5 | ≈9B, ≈18 Go FP16 E ; E int4 ≈7–10 Go | non | Ne pas compter sur 8 Go |
| SigLIP 2 base-patch16-224 | Apache-2.0 | 1,50 Go, ≈0,75 Go FP16 E ; E ≈1–2 Go | oui | Image seule, agréger scores par plan |

## 7. Encodage NVENC Turing
| Candidat | Licence des poids | VRAM ou taille annoncée | Tient en 8 Go sur Turing (oui/non/non vérifié) | Remarque courte |
|---|---|---|---|---|
| hevc_nvenc Main10 p5/hq | Sans objet | E quelques centaines Mo à >1 Go, pic non vérifié | oui | Premier choix, x4 5376×3072 dans limites géométriques |
| h264_nvenc High p5/hq | Sans objet | 8 bits seulement ; limite 4096×4096 | oui | x2 possible, x4 trop large |
| libx265 medium/slow 10 bits | Sans objet | 0 Go GPU, 4 vCPU goulot | oui | Référence compression, x4 potentiellement très lent |
| libx264 medium/slow | Sans objet | 0 Go GPU, 4 vCPU goulot | oui | Référence H.264, intérêt selon contenu |

## Doutes et non vérifiés
- Aucune mesure VRAM/vitesse sur 2080/2070 SUPER ; tous les E restent non vérifiés sur cette VM.
- Licences † : BSD Real-ESRGAN, Apache SPAN/SCUNet/NAFNet/Restormer/IFRNet/EMA, MIT FastDVDnet/Demucs/DeepFilterNet : portée poids non vérifiée.
- Tailles exactes non vérifiées : RealPLKSR, SPAN, IFRNet, SCUNet, NAFNet, Restormer, int8 turbo, BS-RoFormer, MDX23C.
- SeedVR2 8 Go via GGUF/BlockSwap : pas une mesure Turing à la sortie demandée ; 7B Q4 + offload peu réaliste avec 7,7 Go RAM.
- FlashVSR v1.1 : 17 fps à 768×1408 sur A100 seulement, sm_75 pas recommandé ; FlashVSR+ tout non vérifié.
- STAR exclu 8 Go (A ≈39 Go) ; Upscale-A-Video NTU NC, 8 Go non démontré ; Nomos « CC-BY-0.4 » à clarifier.
- WhisperX <8 Go et 70× temps réel : pas ce duo français sur Turing ; Parakeet/Canary RTF Turing non vérifié.
- Qwen3-TTS FP16 sm_75 à valider, sans FA2 ; Magpie zero-shot retiré ; Piper voix licence propre non vérifiée.
- VLM : aucune mesure publiée sur SUPER ; GGUF InternVL3.5 précise et tok/s non vérifiés ; Cosmos-Reason2 exclu par acceptation.
- DOVER contradiction MIT HF contre S-Lab NC code ; FAST-VQA NC ; VBench flicker exige vidéo statique.
- NVENC : page matrice à jour non vérifiée ; sessions 12 (SDK 13.1) contre 8 (13.0), pilote non vérifié ; UHQ exige FFmpeg 7.1, pas 6.1.
