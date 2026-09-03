# Sozo Trade Bot 🤖💎

Bot Telegram qui **trade TON/USDT directement depuis ton wallet Telegram** (TON Space),
et qui continue d'envoyer ton **rapport de marché quotidien** (PDF) par email et sur Telegram.

## Comment ça marche (important à comprendre)

Le wallet custodial `@wallet` de Telegram **n'a pas d'API publique de trading** : aucun bot
ne peut trader dessus à ta place. La méthode officielle et sécurisée, c'est **TON Connect** :

1. Tu lies ton wallet Telegram (TON Space) au bot avec `/connecter` — un tap, pas de seed phrase.
2. Le bot prépare les swaps TON ↔ USDT sur le DEX **STON.fi**.
3. **Chaque transaction doit être confirmée par toi dans ton wallet Telegram.**
   Le bot ne détient jamais tes clés privées et ne peut rien envoyer sans ton accord.

> ⚠️ Ne partage JAMAIS ta phrase de récupération (seed phrase) — ni avec un bot, ni avec personne.

## Commandes du bot

| Commande | Effet |
|---|---|
| `/connecter` | Lier ton wallet Telegram via TON Connect |
| `/wallet` | Adresse + soldes TON et USDT |
| `/prix` | Prix actuel TON/USDT sur STON.fi |
| `/signal` | Signal de trading TON/USDT généré par Claude (recherche web) avec boutons Acheter/Vendre |
| `/acheter 10` | Acheter du TON avec 10 USDT (devis → confirmation → validation dans le wallet) |
| `/vendre 2` | Vendre 2 TON contre des USDT |
| `/rapport` | Générer et recevoir le rapport PDF du jour |
| `/deconnecter` | Délier le wallet |

Garde-fous intégrés : liste blanche de `chat_id`, plafond par swap (`MAX_SWAP_TON`,
`MAX_SWAP_USDT`), slippage maximal (`SLIPPAGE_BPS`), confirmation en 2 étapes.

## Installation

### 1. Créer le bot Telegram

1. Ouvre [@BotFather](https://t.me/BotFather) → `/newbot` → choisis un nom et un identifiant.
2. Récupère le **token** (forme `123456:ABC-DEF…`).

### 2. Configurer et lancer

```bash
git clone https://github.com/sozo19/sozo-trade-reports.git
cd sozo-trade-reports
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # puis remplis .env
export $(grep -v '^#' .env | xargs)
python bot.py
```

Au premier `/start`, le bot t'affiche ton `chat_id` : mets-le dans `AUTHORIZED_CHAT_IDS`
et relance le bot. Sans ça, toutes les commandes sensibles restent bloquées.
(Si tu utilises le bot dans un **groupe**, ajoute aussi les `user_ids` autorisés
dans `AUTHORIZED_USER_IDS` — sinon le bot refuse les groupes.)

### 2 bis. Héberger le manifest TON Connect (obligatoire pour `/connecter`)

Au moment de la connexion, c'est **ton wallet** (pas le bot) qui télécharge le
manifest pour afficher le nom de l'application. Il doit donc être sur une URL
**publiquement accessible** — et ce repo est privé, donc son URL GitHub "raw"
ne fonctionne pas. Le plus simple :

1. Va sur [gist.github.com](https://gist.github.com), crée un gist **public**
   nommé `tonconnect-manifest.json` avec le contenu du fichier
   [tonconnect-manifest.json](tonconnect-manifest.json) de ce repo.
2. Clique sur « Raw » et copie l'URL obtenue.
3. Mets cette URL dans `TONCONNECT_MANIFEST_URL` (fichier `.env`).

(GitHub Pages ou n'importe quel hébergement statique fonctionne aussi.)

Le bot doit tourner en continu pour répondre : un petit serveur (VPS à 3-5 €/mois,
Raspberry Pi, ou un hébergeur comme Railway/Render) suffit. Sur un serveur, lance-le
par exemple avec `nohup python bot.py &` ou un service systemd.

### 3. (Optionnel) Tester la connexion en testnet

`TON_TESTNET=1` permet de tester la **liaison du wallet** et la lecture des soldes
sur le testnet TON. Les swaps sont volontairement refusés en testnet (STON.fi n'y a
pas de paire TON/USDT équivalente) : pour t'entraîner sans risque, reste en mainnet
avec de tout petits montants.

### 4. Le rapport quotidien (GitHub Actions)

Le workflow `.github/workflows/daily_report.yml` tourne tous les jours à 7h CET et
envoie le PDF par email **et sur Telegram** si tu ajoutes ces secrets au repo
(Settings → Secrets and variables → Actions) :

| Secret | Contenu |
|---|---|
| `ANTHROPIC_API_KEY` | Ta clé API Anthropic (déjà en place) |
| `TELEGRAM_BOT_TOKEN` | Le token de ton bot |
| `TELEGRAM_CHAT_ID` | Ton chat_id (affiché par `/start`) |

Sans les secrets Telegram, l'étape est simplement ignorée — et même si l'envoi
Telegram échoue, l'email part quand même (`continue-on-error`).

## Variables d'environnement

Voir [.env.example](.env.example) pour la liste complète et les valeurs par défaut.

## Sécurité

- Le bot ne détient **aucune clé privée** : tout passe par TON Connect, chaque
  transaction est validée dans ton wallet.
- `AUTHORIZED_CHAT_IDS` empêche n'importe qui d'utiliser ton bot (et ta clé API) ;
  en groupe, `AUTHORIZED_USER_IDS` est exigé en plus (par utilisateur).
- Les sessions TON Connect sont stockées dans `.tc_sessions/` (exclu de git,
  permissions 0600 — lisibles par ton compte uniquement).
- Plafonds par swap + slippage maximal configurables, devis valable 90 s :
  le minimum garanti signé est exactement celui affiché.

## Avertissement

Les signaux et rapports sont générés par IA **à titre informatif uniquement** — ce n'est
pas un conseil financier. Le trading de crypto-actifs comporte un risque de perte totale.
Commence petit, ou en testnet.
