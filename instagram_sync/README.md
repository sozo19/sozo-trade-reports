# Instagram Saves → Compétences Claude

Ce dossier contient le pipeline qui transforme automatiquement les reels que tu
enregistres sur Instagram (bouton 🔖) en **compétences pour Claude** et en
**notes de connaissance**, deux fois par jour.

Inspiré du workflow « Instagram Saves → Obsidian » : chaque save devient un
asset dans ton second cerveau au lieu d'être oublié.

## Ce que ça produit

| Sortie | Emplacement | Quand |
|---|---|---|
| Note complète (résumé + légende + transcription) | `knowledge/instagram/<date>-<slug>.md` | pour chaque reel |
| Compétence Claude | `.claude/skills/ig-<slug>/SKILL.md` | si le contenu est actionnable (méthode, technique, process) |
| État de synchro | `instagram_sync/state.json` | mis à jour à chaque run |

Les memes / divertissement / pubs donnent une note mais pas de compétence —
c'est Claude (API) qui fait le tri.

## Mise en place (une fois, ~10 min)

### 1. Récupérer le cookie de session Instagram

1. Connecte-toi à [instagram.com](https://www.instagram.com) dans ton navigateur.
2. Ouvre les outils développeur (F12) → onglet **Application** (Chrome) ou
   **Stockage** (Firefox) → **Cookies** → `https://www.instagram.com`.
3. Copie la valeur du cookie **`sessionid`** (et idéalement aussi `csrftoken`
   et `mid`).

### 2. Ajouter les secrets GitHub

Dans le dépôt : **Settings → Secrets and variables → Actions → New repository secret** :

| Secret | Obligatoire | Valeur |
|---|---|---|
| `IG_USERNAME` | ✅ | ton nom d'utilisateur Instagram |
| `IG_SESSIONID` | ✅ | le cookie `sessionid` |
| `ANTHROPIC_API_KEY` | ✅ | déjà configuré pour le rapport quotidien |
| `IG_CSRFTOKEN` | recommandé | le cookie `csrftoken` |
| `IG_MID` | optionnel | le cookie `mid` |
| `SCRAPECREATORS_API_KEY` | optionnel | clé [ScrapeCreators](https://scrapecreators.com) pour des transcriptions de meilleure qualité |

Sans clé ScrapeCreators, la transcription est faite localement avec Whisper
(gratuit, un peu moins précis). Sans transcription possible, seule la légende
du reel est utilisée.

### 3. Lancer un premier test

**Actions → Instagram Saves vers Compétences → Run workflow.**
Le premier run traite jusqu'à 10 saves récents ; les suivants ne traitent que
les nouveaux. Les compétences apparaissent ensuite automatiquement dans tes
sessions Claude sur ce dépôt.

## Exécution locale (alternative recommandée si Instagram bloque)

```bash
pip install -r instagram_sync/requirements.txt
export IG_USERNAME=... IG_SESSIONID=... ANTHROPIC_API_KEY=...
python instagram_sync/sync_saves.py
```

## ⚠️ À savoir (important)

- **Ce pipeline utilise l'API non officielle d'Instagram** (comme tous les
  outils de ce type, dont celui de la vidéo TikTok d'origine). C'est contraire
  aux conditions d'utilisation d'Instagram et cela comporte un **risque de
  restriction ou de blocage du compte**, surtout depuis les IP de datacenter
  de GitHub Actions. Le script limite le rythme (max 10 posts/run, pauses
  entre chaque), mais le risque n'est jamais nul. Si Instagram bloque la
  session, passe à l'exécution locale depuis ta machine.
- **Le cookie `sessionid` expire** (déconnexion, changement de mot de passe,
  ou au bout de quelques mois). Si le run échoue avec « Session Instagram
  invalide », remets simplement un cookie frais dans le secret.
- **Ne partage jamais ton `sessionid`** : il donne un accès complet à ton
  compte. Il ne doit vivre que dans les secrets GitHub.
- **Coût** : ~1 appel API Anthropic par reel (quelques centimes). ScrapeCreators
  est payant ; Whisper est gratuit.

## Réglages (variables d'environnement)

| Variable | Défaut | Rôle |
|---|---|---|
| `IG_MAX_POSTS_PER_RUN` | `10` | nombre max de nouveaux saves traités par run |
| `IG_VIDEOS_ONLY` | `1` | ignorer les photos (mettre `0` pour tout traiter) |
| `WHISPER_MODEL` | `base` | modèle Whisper local (`small` = plus précis, plus lent) |
| `CLAUDE_MODEL` | `claude-opus-5` | modèle utilisé pour la distillation |
| `SCRAPECREATORS_TRANSCRIPT_URL` | endpoint v2 | à ajuster si l'API ScrapeCreators change |

## Dépannage

- **« Session Instagram invalide ou expirée »** → régénère le cookie (étape 1).
- **Erreur sur un reel précis** → il n'est pas ajouté à `state.json` et sera
  retenté automatiquement au run suivant.
- **Trop de compétences générées** → supprime les dossiers `.claude/skills/ig-*`
  inutiles ; les reels correspondants restent dans `state.json` et ne seront
  pas retraités.
