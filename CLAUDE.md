# Carré Hastings – maquette 360° interactive (INOVA / ATJ Graphics)

Lire d'abord **HANDOFF.md** (état du projet, décisions, reprise pas à pas, §4 = où on en est).

## Règles de travail
- Répondre en **français**. Ton direct, sans jargon inutile ; dire clairement ce qui est vérifié et ce qui ne l'est pas.
- Le client (Tom, ATJ Graphics) exige des polygones **précis** : contours sur la **face intérieure des murs**, tous les angles respectés, jamais calés sur les ombres.
- Les projets réels auront **beaucoup de lots** et des **formes complexes** : tout outil ou script doit être indépendant du nombre de polygones et de leur forme.
- Ne jamais publier ni envoyer les données du client (plans de vente, visuels) hors de ce dépôt privé sans demande explicite.
- Les chemins source (OneDrive de Tom) ne sont pas dans le dépôt : voir HANDOFF.md > « Sources ».
- Python : `pip install opencv-python numpy scipy pillow pymupdf`. Pas de poppler.
- Tester les pages avec un vrai navigateur (clics réels, pas seulement des appels JS) : une régression a déjà échappé à des tests purement JS.
- Méthode retenue pour les polygones : **4 images tracées à la main par niveau** (0, 8, 15, 23) + **modèle de caméra en orbite** (`work/orbit.py`), pas l'alignement SIFT/ECC. Mesurer avant d'affirmer une précision (test à blanc : retirer une image tracée et la prédire).
- Cloner dans un chemin court sous Windows ; ne pas lancer de serveur de test sur un port déjà utilisé (vérifier que la page servie est la bonne).
