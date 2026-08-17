---
name: instagram-saves
description: Base de connaissances des reels Instagram enregistrés par l'utilisateur, synchronisée automatiquement 2x/jour. Utiliser quand une question fait référence à une technique, stratégie, méthode ou idée « vue dans un reel », « enregistrée sur Instagram », ou quand le sujet pourrait être couvert par un contenu sauvegardé (trading, création de contenu, productivité, outils IA…). Permet aussi de retrouver et citer un reel précis.
---

# Saves Instagram — second cerveau

Les reels que l'utilisateur enregistre sur Instagram sont automatiquement
transformés en connaissances exploitables par le workflow
`instagram_sync/sync_saves.py` (GitHub Action, 2x/jour).

## Où chercher

1. **Notes complètes** : `knowledge/instagram/*.md` — une note par reel, avec
   frontmatter (titre, source, auteur, tags), résumé, légende originale et
   transcription. Utiliser Grep/Glob sur ce dossier pour retrouver un sujet.
2. **Compétences dédiées** : `.claude/skills/ig-*/SKILL.md` — les reels jugés
   actionnables (méthode, technique, process) ont leur propre compétence,
   chargée automatiquement quand le sujet s'y prête.
3. **État de synchronisation** : `instagram_sync/state.json` — liste des
   shortcodes déjà traités, avec titre et date.

## Comment répondre

- Quand l'utilisateur évoque un contenu qu'il a « vu » ou « enregistré »,
  chercher d'abord dans `knowledge/instagram/` (Grep sur les mots-clés, ou le
  nom du créateur `@...`).
- Toujours citer la source (URL du reel et auteur) quand une réponse s'appuie
  sur une note.
- Si l'utilisateur veut améliorer/corriger une compétence générée (`ig-*`),
  éditer directement son `SKILL.md` — la synchronisation n'écrase pas les
  compétences existantes d'un reel déjà traité.
