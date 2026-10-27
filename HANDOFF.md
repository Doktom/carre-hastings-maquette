# HANDOFF – reprendre le projet dans une nouvelle session

*Dernière mise à jour : 27/10/2026. Dépôt privé ; données du client INOVA incluses (plans de vente, visuels) : ne pas rendre public.*

## 1. Objectif
Remplacer, sur les visuels 360° d'étage (30 images par niveau, rendus Object2VR), les hotspots par des **polygones interactifs colorés par
typologie** qui suivent la **face intérieure des murs** de chaque appartement, à tous les angles de rotation.
Survol → petite info-bulle (lot, typologie, surface, étage, extérieurs). Clic → fiche complète : plan de vente (PDF), plan 3D, vues intérieures.
Maquette actuelle (Object2VR) : https://carre-hastings.atj-app.com/maquette-360/

Exigence forte de Tom (ATJ Graphics) : **précision des contours** (angles respectés, pas calés sur les ombres) et **le moins de
corrections manuelles possible**. Les projets suivants auront **beaucoup plus de lots et des formes plus complexes** : rien ne doit
dépendre du nombre/de la forme des polygones.

## 2. Sources (hors dépôt – OneDrive de Tom)
Racine : `C:\Users\tom\OneDrive\Documents\ATJ\ATJ GRAPHICS\PROJETS CLIENTS\2026\INOVA CARRE HASTING\`
- `360 ETAGES\360GOOD+\{RDC,R+1,R+2,TOITURE}\` : 30 JPG 2560×1440 par niveau (`MONPLAISIR_360 Coupe Etage R+1 (2k30)_000NN.jpg`), rotation complète (12°/image, caméra aérienne oblique)
- `360 ETAGES\output\` : export Object2VR existant (`object.xml` = anciens hotspots ; `states` 1=RDC, 2=R+1, 3=R+2 ; inutile pour la suite)
- `Plansdeventes_pdf\Plans de vente - INOVA RUE MONPLAISIR-N.pdf` : 1 PDF par lot (N = 1…10), texte extractible (PyMuPDF)
- `appartements 3d\004_VUES INTERIEURES\<dossier>\` : plan 3D + vues d'intérieur par lot (images 5504×3072, 8–14 Mo)
- `plan-rdc-pdf_2026-02-11_0749\` : plans architecte PC (non utilisés)

Sans accès à OneDrive : `work/final/frames/` contient les 30 images du R+1 en 1920 px et `work/site/` les vues/plans réduits des lots 5–8.
Variable `CARRE_BASE` = racine ci-dessus si elle est ailleurs.

## 3. Programme (10 lots)
| Niveau | Lots | Typologies | Surface hab. (m²) |
|---|---|---|---|
| RDC | 1, 2, 3, 4 | T4, T4, T2, T4 | 90,00 · 91,05 · 50,51 · 81,53 |
| R+1 | 5, 6, 7, 8 | T4, T4, T3, T4 | 90,00 · 91,05 · 70,97 · 81,53 |
| R+2 | 9, 10 | T4/T5, T4/T5 | 113,13 · 120,55 |
Couleurs : T2 vert `#2bb673`, T3 bleu `#2f80ed`, T4 orange `#f2994a`, T4/T5 violet `#9b51e0`. Pas de prix ni de statut dans les PDF.

## 4. État d'avancement
- **R+1 : terminé et fonctionnel** (4 lots, 30 images). Livrables générés par `build_final.py` / `mk_editor2.py` (non versionnés).
- **RDC, R+2 (et TOITURE) : à faire** avec la même méthode (§5). Puis **sélecteur d'étages** pour les assembler.
- À valider avec Tom (hypothèses de ma part, non confirmées) :
  1. Position des lots sur la maquette R+1 (vue image 0) : lot 8 en haut à gauche, 7 en haut à droite (le T3), 5 en bas à gauche, 6 en bas à droite. Déduit des hotspots Object2VR (le seul T3) et des mini-plans des PDF.
  2. Correspondance dossiers vues 3D → lots : 5→`R+1_T4_3`, 6→`R+1_T4_4`, 7→`R+1_T3_2`, 8→`R+1_T3_1` (les noms de dossiers ne suivent pas la numérotation des lots). À vérifier ; RDC et R+2 : à déterminer de la même façon.
  3. Mots du tableau « surfaces » (`work/site/lots.json`) extraits automatiquement des PDF ; un « Hall Hall » dupliqué est corrigé dans `build_final.py`.

## 5. Méthode (par niveau) – commandes
Dans `work/` (installer : `pip install opencv-python numpy scipy pillow pymupdf`).

1. **Images web** : `python export_frames.py "<…>/360GOOD+/RDC" final/frames_rdc rdc`
2. **Tracer les polygones sur l'image 0 uniquement** : `python mk_editor1.py "<…>/RDC/<image_00000>.jpg" editeur-rdc.html` génère l'éditeur (une image embarquée ; en option un JSON existant à retoucher). Pour le R+1 déjà tracé, `controle-polygones.html` (généré par `mk_editor2.py`) permet de parcourir les 30 images. Exporter le JSON (`polygones-<niveau>.json` : `{level, image:{width,height}, lots:{"5":{typo, points:[[x,y]…]}}}`, coordonnées dans l'image 2560×1440).
   - Contour = **bord intérieur du dessus des murs** ; magnétisme sur sommets voisins pour les murs mitoyens ; sommets nombreux pour les angles.
3. **Alignement des 30 images** (indépendant des polygones : seule l'enveloppe du bâtiment sert de masque) :
   `python align_level.py "<…>/360GOOD+/RDC" polygones-RDC.json align_RDC.json 2` (≈3 min)
4. **Report des polygones** : `python propagate.py polygones-RDC.json align_RDC.json polys_frames_rdc.json H`
5. **Contrôle visuel** : `python check_vertex.py <lot> <sommet> 5,10,15,20,25,29 sortie.jpg` (rogne autour d'un sommet sur plusieurs images) ; `evalscore.py` donne un score de bords (indicatif seulement, trop bruité pour trancher à ±10 px).
6. **Corrections éventuelles** : ouvrir `controle-polygones.html`, parcourir les images, glisser sommets/polygones ; exporter ; `python apply_corrections.py export.json` interpole l'écart entre images corrigées (sans toucher aux autres).
7. **Pages** : `python build_final.py <dossier_sortie>` (maquette) et `python mk_editor2.py <dossier_sortie>` (outil de contrôle). Ces scripts sont encore **spécifiques au R+1** (lots 5–8, chemins `r1_XX`, noms de dossiers 3D en dur dans `build_assets.py`) → à généraliser pour plusieurs niveaux et dizaines de lots (voir §8).

## 6. Pourquoi cette méthode d'alignement (ne pas refaire les impasses)
Les polygones sont dans le plan du **dessus des murs** ; entre deux images consécutives (12°), ce plan se déplace par une **homographie**.
- **Retenu (`align_level.py`)** : chaîne d'homographies image→image+1 (SIFT pour l'initialisation puis raffinement **ECC** sur la zone du bâtiment, masque = enveloppe convexe des polygones dilatée de 24 px, 1280×720). Le tour ne se referme pas (erreur de fermeture ≈ 44 px sur le R+1) : la dérive vient presque entièrement des **derniers pas** (peu de points de correspondance). On répartit donc l'erreur de fermeture sur le **dernier tiers du tour** (lissage progressif), pas sur tout le tour. Vérifié visuellement sur plusieurs sommets/images : erreur résiduelle typiquement ≤ 6–8 px, jamais > ~10 px.
- **Essayé, abandonné** :
  - modèle de caméra en orbite ajusté sur les hotspots Object2VR (rms 58 px, hotspots posés à la main) ou sur les homographies mesurées (rms 7 px, non exact : la trajectoire n'est pas une orbite parfaite) ;
  - optimisation globale avec mesures à pas 2–3 (biais sur grandes bases : écarts jusqu'à 48 px avec la chaîne, plus mauvais) ;
  - ECC restreint à une bande autour des contours (fermeture 55–93 px) ; ECC sur pixels très clairs seulement (fermeture 136 px) ;
  - répartition uniforme ou pondérée par les inliers de la fermeture (moins bonne en milieu de tour que la chaîne brute).
- **Pistes si plus de précision est nécessaire** : mesure de meilleure qualité sur les derniers pas (plus de points, multi-échelle) ; raffinement local par image avec contrainte sur les bords des murs ; keyframes corrigés à la main (outil de contrôle + `apply_corrections.py`).

## 7. Détails techniques utiles
- **Rendu de la maquette** : les images sont dessinées sur un `<canvas>` (ImageBitmap préchargés) en même temps que les polygones SVG (`viewBox 2560×1440`) ; avant, `img.src` tardait à décoder et les polygones « décalaient » pendant la rotation.
- **Fichier autonome** : `build_final.py` embarque tout en data-URI (`window.ASSET`, fonction `A(chemin)`) ; la prévisualisation de l'appli ne résout pas les chemins relatifs, d'où ce fichier unique (≈14 Mo).
- **Outil de contrôle** : état sauvegardé en `localStorage` (clé `controle-polygones-r1-v1`) ; **ne jamais capturer le pointeur sur la vue pour les clics de la barre** (`#bar`) sinon les boutons ne répondent plus (bug déjà corrigé).
- Info-bulle tactile : 1er appui = info-bulle, 2e = fiche (non testé sur appareil réel).
- Encodage : les PDF contiennent des accents ; extraire via PyMuPDF (`get_text('words')`), pas via la console Windows.

**Publication** : `docs/` est servi par GitHub Pages (https://doktom.github.io/carre-hastings-maquette/). Après régénération : copier le contenu de `maquette-r1/` dans `docs/` (+ `controle-polygones.html`), commit, push.

## 8. À faire ensuite (par priorité)
1. Faire valider le R+1 par Tom (rendu + correspondances §4).
2. RDC et R+2 : tracer, aligner, propager, contrôler (§5).
3. Généraliser `build_assets.py` / `build_final.py` / `mk_editor2.py` : plusieurs niveaux, N lots quelconques, mapping lot→dossier 3D configurable (un `config.json` par programme), sans valeurs en dur.
4. Sélecteur d'étages + vue d'ensemble ; héberger sur `atj-app.com` (serveur web requis pour la version dossier).
5. Outils d'édition pour projets complexes : lots à plusieurs zones (multi-polygones, trous), recherche/filtre dans la liste des lots, duplication de contours, vérification automatique des chevauchements.
6. Prix/statut des lots si fournis par INOVA.

## 9. Préférences de Tom
Français. Réponses courtes et concrètes. Il teste dans son navigateur : vérifier avec de vrais clics. Il veut voir des résultats vérifiés, pas des promesses ; annoncer clairement ce qui n'est pas contrôlé.
