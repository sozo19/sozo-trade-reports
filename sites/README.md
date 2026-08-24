# Sites de démonstration — Salons de coiffure de La Côte (VD)

26 sites vitrines one-page prêts à montrer en rendez-vous de prospection, générés depuis `Prospection_Coiffeurs_Sans_Site_Vaud.xlsx`.

## Structure

```
sites/
  index.html            ← hub : la liste des 26 démos (à ouvrir en premier)
  _data/salons.json     ← données + brief d'identité visuelle de chaque salon
  <slug>/
    index.html          ← le site de démo (autonome, aucune dépendance hors Google Fonts)
    pitch.md            ← identité visuelle, arborescence, copywriting, argumentaire de vente
```

## Utilisation

- **Voir une démo** : ouvrir `sites/<slug>/index.html` dans un navigateur (double-clic suffit), ou servir le dossier (`python3 -m http.server` depuis `sites/`) et naviguer depuis le hub.
- **Photos** : chaque visuel a un fond dessiné toujours visible ; des photos Unsplash libres de droits se chargent par-dessus quand la connexion le permet. À remplacer par les photos du salon avant la mise en ligne.
- **Réservation** : le module 3 étapes est une démo front-end ; il se branche sur Planity, Fresha, Calendly ou l'agenda du salon au moment de la vente.
- **Avis & équipe** : exemples réalistes clairement marqués « démonstration », à remplacer par les vrais avis Google et l'équipe réelle.

Chaque site a sa propre identité (palette, typographies Google Fonts, motif signature, layout) définie dans `_data/salons.json` — aucun doublon.
