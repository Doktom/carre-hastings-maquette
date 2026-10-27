# Carré Hastings – maquette 360° interactive (INOVA / ATJ Graphics)

Lire d'abord **HANDOFF.md** (état du projet, décisions, reprise pas à pas).

## Règles de travail
- Répondre en **français**. Ton direct, sans jargon inutile ; dire clairement ce qui est vérifié et ce qui ne l'est pas.
- Le client (Tom, ATJ Graphics) exige des polygones **précis** : contours sur la **face intérieure des murs**, tous les angles respectés, jamais calés sur les ombres.
- Les projets réels auront **beaucoup de lots** et des **formes complexes** : tout outil ou script doit être indépendant du nombre de polygones et de leur forme.
- Ne jamais publier ni envoyer les données du client (plans de vente, visuels) hors de ce dépôt privé sans demande explicite.
- Les chemins source (OneDrive de Tom) ne sont pas dans le dépôt : voir HANDOFF.md > « Sources ».
- Python : `pip install opencv-python numpy scipy pillow pymupdf`. Pas de poppler.
- Tester les pages avec un vrai navigateur (clics réels, pas seulement des appels JS) : une régression a déjà échappé à des tests purement JS.
