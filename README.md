# Projets Sozo

Un dossier par projet. Chaque dossier est autonome : on peut travailler dans l'un sans
jamais toucher aux autres.

| Dossier | Projet | État |
|---|---|---|
| [`trading-reports/`](trading-reports/) | Rapport de trading quotidien envoyé par e-mail | En production |
| [`barbershop-mont-blanc/`](barbershop-mont-blanc/) | Landing page + réservation intégrée pour un salon de coiffure | Démo à présenter |

## Les projets

### `trading-reports/`

Génère chaque matin un rapport PDF et l'envoie par e-mail.
Lancé automatiquement par [`.github/workflows/daily_report.yml`](.github/workflows/daily_report.yml)
à 6 h UTC (7 h heure suisse).

Secrets nécessaires (Settings → Secrets and variables → Actions) :
`ANTHROPIC_API_KEY`, `EMAIL_USER`, `EMAIL_PASS`, `EMAIL_TO`.

### `barbershop-mont-blanc/`

Landing page de démonstration avec système de réservation intégré à la page, destinée à
remplacer une page Salonkee. Un seul fichier HTML, sans dépendance.
Voir [son README](barbershop-mont-blanc/README.md) pour la personnalisation et les
arguments de vente.

## Ajouter une nouvelle idée

1. Créez un dossier à la racine, avec un nom court et explicite (`nom-du-projet/`)
2. Mettez-y un `README.md` qui explique en trois lignes ce que fait le projet
3. Ajoutez une ligne au tableau ci-dessus

Si le projet a besoin d'une automatisation, ajoutez son workflow dans
`.github/workflows/` et donnez-lui un nom qui reprend celui du dossier — c'est ce qui
permet de savoir, plus tard, à quel projet chaque workflow appartient.
