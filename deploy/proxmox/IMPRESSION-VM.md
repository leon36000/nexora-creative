# Mode Marketing sur la VM 202 : dépendances d'impression

Le rendu des PDF (page **Marketing**) utilise Chromium (Playwright), et en option Ghostscript (CMJN) et poppler (export SVG). `mettre-a-jour-creative.sh` les installe une fois (étape idempotente) :

```
cd /srv/creative/app && npx playwright-core install chromium      # navigateur, dans ~/.cache/ms-playwright du service
sudo npx playwright-core install-deps chromium                     # bibliothèques système (apt)
sudo apt-get install -y ghostscript poppler-utils                  # CMJN (gs) et SVG (pdftocairo), facultatifs
```

Variables facultatives de `/etc/nexora/creative.env` : `NEXORA_CHROMIUM` (chemin d'un Chromium déjà installé), `NEXORA_CHROMIUM_SANS_BAC=1` (si le bac à sable de Chromium est refusé dans la VM). Sans Ghostscript le PDF reste en RVB (la page l'indique) ; sans poppler, pas d'export SVG. Un rendu à la fois (file), ≈ 300 Mo de mémoire, ≈ 0,3 s par pièce.
