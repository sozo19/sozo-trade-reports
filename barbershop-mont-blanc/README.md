# Barbershop Mont-Blanc — Landing page de démonstration

Page de vente **prête à présenter** au patron du salon, conçue pour remplacer la page
Salonkee actuelle. Tout tient dans un seul fichier : `index.html` (HTML + CSS natif + JS,
aucune dépendance, aucun build).

Ouvrez simplement `index.html` dans un navigateur.

---

## Ce que contient la page

| Section | Détail |
|---|---|
| **Header** | Fixe, transparent puis assombri au scroll, bouton « Réserver » ancré sur le module |
| **Hero** | Titre animé ligne par ligne, chiffres clés, double CTA |
| **Services** | 6 prestations avec prix, durée et bouton « Choisir » qui pré-remplit la réservation |
| **La Maison** | Bloc image + 3 arguments |
| **Réservation** | Le cœur du site — formulaire multi-étapes (voir plus bas) |
| **Avis** | 3 témoignages, note globale |
| **Footer** | Horaires (avec statut *ouvert / fermé* calculé en direct), adresse, réseaux |

## Le module de réservation

Quatre étapes, sans jamais quitter la page :

1. **Service** — cases cliquables avec prix et durée
2. **Barbier** — 4 profils, dont « Peu importe » (qui débloque plus de créneaux)
3. **Créneau** — vrai calendrier interactif (navigation mensuelle, dimanches et jours
   passés désactivés, réservation ouverte à 60 jours) + grille horaire
4. **Coordonnées** — validation en direct des champs, puis confirmation animée

Détails qui font la différence en démo :

- Le **récapitulatif de gauche se remplit en temps réel** à chaque choix.
- Les créneaux sont **déterministes** : un même jour affiche toujours les mêmes
  disponibilités, et environ 40 % sont déjà « pris » pour que la démo paraisse crédible.
- La durée du service **modifie réellement** la grille horaire.
- Aucun créneau passé n'est proposé pour la journée en cours.
- L'écran de confirmation génère une **référence de réservation** et un bouton
  « Ajouter à mon agenda » qui télécharge un vrai fichier `.ics`.
- Transitions glissées entre les étapes, révélations au scroll, survols travaillés.

> ⚠️ Démo front-end : la confirmation simule l'envoi (950 ms) et **n'écrit dans aucune
> base**. Le branchement sur l'agenda réel du salon se fait dans la fonction
> `confirmer()`, à l'endroit commenté.

## Personnaliser en 2 minutes

Tout est regroupé en haut des blocs `<style>` et `<script>` :

- **Photos** — dans `:root`, remplacez `--photo-hero: none;` par
  `url("photos/salon.jpg")` (idem `--photo-atelier`). Les filtres et voiles s'appliquent
  automatiquement. Sans photo, la page reste élégante grâce au décor généré en CSS.
- **Prestations / prix / durées** — tableau `PRESTATIONS`. Il alimente à la fois la
  section vitrine **et** l'étape 1 du formulaire.
- **Équipe** — tableau `COIFFEURS`. Pour de vraies photos, remplacez le monogramme par
  `<img src="photos/marco.jpg" alt="Marco">` (le commentaire est en place dans le code).
- **Horaires** — tableau `HORAIRES` : il pilote le footer, le statut ouvert/fermé, les
  jours désactivés du calendrier et les plages horaires proposées.
- **Coordonnées** — adresse, téléphone et e-mail dans le footer.

## Compatibilité

Chrome, Firefox, Safari et Edge récents. Testé de 390 px à 1440 px, aucun débordement
horizontal. Navigation clavier, `aria-*` sur le parcours de réservation, et respect de
`prefers-reduced-motion`. Les polices viennent de Google Fonts ; hors ligne, la page
bascule proprement sur des polices système.

---

## Partager la démo

Un workflow GitHub Actions (`.github/workflows/deploy-demo.yml`) publie ce dossier sur
GitHub Pages à chaque push sur `main`.

Activation, une seule fois : **Settings → Pages → Source : « GitHub Actions »**.
L'adresse publique devient ensuite :

```
https://sozo19.github.io/sozo-trade-reports/
```

La page porte une balise `noindex, nofollow` pour ne pas être référencée par Google et
passer pour le site officiel du salon. **À retirer** le jour de la mise en ligne
définitive (ligne 11 de `index.html`).

---

## Arguments pour la présentation au patron

**1. L'image de marque.** Aujourd'hui, au moment le plus important — celui où le client
décide — il quitte votre univers pour une page Salonkee identique à celle de tous les
autres salons. Ici, il reste chez vous du premier clic à la confirmation. C'est
l'expérience d'un salon haut de gamme, de bout en bout.

**2. Moins de clics, plus de rendez-vous.** Le système est intégré à la page. Le client
choisit sa prestation, son barbier, son créneau et valide — sans changement de page, sans
compte à créer, sans mot de passe oublié. Chaque étape supprimée, c'est un client de plus
qui va au bout.

**3. Votre fichier clients vous appartient.** Avec votre propre système, les noms, les
téléphones et les e-mails sont à vous. Vous pouvez relancer par SMS un client qui n'est
pas revenu depuis trois mois, envoyer une offre avant les fêtes, remplir un mardi
après-midi creux. Sur une plateforme externe, cette base ne vous appartient pas — et les
règles peuvent changer sans vous demander votre avis.

**4. Bonus concret.** Le bouton « Ajouter à mon agenda » place le rendez-vous directement
dans le téléphone du client. Moins d'oublis, moins de fauteuils vides.
