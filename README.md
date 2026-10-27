# Carré Hastings – maquette 360° interactive

Maquette de vente interactive pour INOVA (programme « Carré Hastings », Carpiquet) réalisée par ATJ Graphics.
Les visuels 360° d'étage (30 images par niveau, rendus Object2VR) reçoivent des **polygones interactifs colorés par typologie**
(T2, T3, T4…), qui épousent les cloisons de chaque appartement et suivent la rotation. Au survol : info-bulle ; au clic : fiche
complète (plan de vente PDF, plan 3D, vues intérieures).

**Reprendre le travail dans une autre session Claude : lire [HANDOFF.md](HANDOFF.md).**

## Contenu
| Dossier | Rôle |
|---|---|
| `work/` | scripts Python, modèles de pages, données (tracé des polygones, lots) — à lancer depuis ce dossier |
| `work/site/` | images des vues intérieures, plans de vente (images + PDF), données des lots |
| `work/final/frames/` | les 30 images du R+1 en 1920 px |
| `docs/` | notes de méthode |

## Livrables générés (non versionnés, reproductibles)
- `maquette-r1-autonome.html` : un seul fichier, tout embarqué (~14 Mo)
- `maquette-r1/` : même page, images/PDF à part (à servir par un serveur web)
- `controle-polygones.html` : outil pour contrôler/corriger les contours image par image

## Démarrage rapide
```bash
pip install opencv-python numpy scipy pillow pymupdf
cd work
python build_final.py ..            # reconstruit la maquette dans le dossier parent
python mk_editor2.py ..             # reconstruit l'outil de contrôle
```
