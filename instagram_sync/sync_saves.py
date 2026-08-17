#!/usr/bin/env python3
"""Instagram Saves -> Compétences Claude.

Récupère les reels enregistrés sur Instagram (via la session du compte),
récupère leur contenu textuel (transcript ScrapeCreators, sinon transcription
locale Whisper, sinon légende seule), puis les distille avec Claude en :
  - une note de connaissance   -> knowledge/instagram/<date>-<slug>.md
  - une compétence Claude      -> .claude/skills/ig-<slug>/SKILL.md
    (seulement si le contenu est jugé actionnable)

Inspiré du workflow "Instagram Saves -> Obsidian" (2x/jour, état persisté,
les échecs ne sont pas ajoutés à l'état pour être retentés au run suivant).

Secrets requis : IG_USERNAME, IG_SESSIONID, ANTHROPIC_API_KEY
Optionnels     : IG_CSRFTOKEN, IG_MID, IG_DS_USER_ID, SCRAPECREATORS_API_KEY
Voir instagram_sync/README.md pour la mise en place.
"""

import json
import os
import re
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
STATE_FILE = HERE / "state.json"
KNOWLEDGE_DIR = REPO_ROOT / "knowledge" / "instagram"
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

MAX_POSTS_PER_RUN = int(os.getenv("IG_MAX_POSTS_PER_RUN", "10"))
STOP_AFTER_KNOWN = int(os.getenv("IG_STOP_AFTER_KNOWN", "10"))
VIDEOS_ONLY = os.getenv("IG_VIDEOS_ONLY", "1") == "1"
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5")
SC_TRANSCRIPT_URL = os.getenv(
    "SCRAPECREATORS_TRANSCRIPT_URL",
    "https://api.scrapecreators.com/v2/instagram/media/transcript",
)


# ---------------------------------------------------------------- état

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"processed": {}}


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


# ---------------------------------------------------------------- instagram

def build_loader():
    import instaloader

    username = os.environ.get("IG_USERNAME")
    sessionid = os.environ.get("IG_SESSIONID")
    if not username or not sessionid:
        sys.exit(
            "Configuration manquante : définis IG_USERNAME et IG_SESSIONID "
            "(voir instagram_sync/README.md)."
        )

    ds_user_id = os.environ.get("IG_DS_USER_ID")
    if not ds_user_id:
        # le sessionid commence par "<ds_user_id>%3A..." (ou "<ds_user_id>:...")
        ds_user_id = sessionid.split("%3A")[0].split(":")[0]

    cookies = {"sessionid": sessionid, "ds_user_id": ds_user_id}
    for env_var, cookie_name in (("IG_CSRFTOKEN", "csrftoken"), ("IG_MID", "mid")):
        if os.environ.get(env_var):
            cookies[cookie_name] = os.environ[env_var]

    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        save_metadata=False,
        quiet=True,
    )
    loader.load_session(username, cookies)
    if loader.test_login() is None:
        sys.exit(
            "Session Instagram invalide ou expirée : reconnecte-toi sur "
            "instagram.com dans ton navigateur, récupère le nouveau cookie "
            "'sessionid' et mets à jour le secret IG_SESSIONID."
        )
    return loader


# ---------------------------------------------------------------- transcription

def transcript_scrapecreators(post_url):
    api_key = os.environ.get("SCRAPECREATORS_API_KEY")
    if not api_key:
        return None
    try:
        resp = requests.get(
            SC_TRANSCRIPT_URL,
            params={"url": post_url},
            headers={"x-api-key": api_key},
            timeout=90,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # l'API est optionnelle : on bascule sur le fallback
        print(f"  ScrapeCreators indisponible ({exc}), fallback transcription locale.")
        return None

    # forme de réponse défensive : la clé exacte dépend de la version de l'API
    for key in ("transcript", "text", "transcription"):
        if isinstance(data.get(key), str) and data[key].strip():
            return data[key].strip()
    transcripts = data.get("transcripts")
    if isinstance(transcripts, list):
        parts = [t.get("text", "") if isinstance(t, dict) else str(t) for t in transcripts]
        joined = " ".join(p.strip() for p in parts if p and p.strip())
        if joined:
            return joined
    return None


def transcript_whisper(video_url):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    if not video_url:
        return None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            with requests.get(video_url, stream=True, timeout=120) as resp:
                resp.raise_for_status()
                for chunk in resp.iter_content(chunk_size=1 << 16):
                    tmp.write(chunk)
            tmp_path = tmp.name
        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        segments, _info = model.transcribe(tmp_path, vad_filter=True)
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return text or None
    except Exception as exc:
        print(f"  Transcription Whisper impossible ({exc}).")
        return None
    finally:
        try:
            os.unlink(tmp_path)
        except (OSError, UnboundLocalError):
            pass


def get_transcript(post_url, video_url):
    return transcript_scrapecreators(post_url) or transcript_whisper(video_url)


# ---------------------------------------------------------------- distillation

DISTILL_SCHEMA = {
    "type": "object",
    "properties": {
        "titre": {"type": "string", "description": "Titre court et parlant du contenu"},
        "slug": {
            "type": "string",
            "description": "Identifiant kebab-case ascii, 3 a 5 mots, ex: setup-breakout-londres",
        },
        "resume": {"type": "string", "description": "Resume du contenu en 3-6 phrases"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "vaut_une_competence": {
            "type": "boolean",
            "description": "true si le contenu enseigne une methode/technique actionnable, false si c'est du divertissement, un meme ou trop vague",
        },
        "competence_nom": {"type": "string"},
        "competence_description": {
            "type": "string",
            "description": "Description de declenchement de la competence : quand Claude doit l'utiliser, avec les mots-cles typiques",
        },
        "competence_instructions": {
            "type": "string",
            "description": "Corps de la competence en Markdown : la methode restructuree en instructions claires et applicables",
        },
    },
    "required": [
        "titre", "slug", "resume", "tags", "vaut_une_competence",
        "competence_nom", "competence_description", "competence_instructions",
    ],
    "additionalProperties": False,
}

DISTILL_PROMPT = """Tu distilles le contenu d'un reel Instagram enregistré par l'utilisateur \
pour l'intégrer dans son « second cerveau » et, si le contenu s'y prête, en faire une \
compétence réutilisable pour un assistant IA.

Reel de @{owner}, enregistré le {date} :

<legende>
{caption}
</legende>

<transcription>
{transcript}
</transcription>

Analyse ce contenu et produis le JSON demandé :
- Si le reel enseigne une méthode, une technique, un process ou un savoir actionnable \
(trading, création de contenu, productivité, outils, etc.), mets vaut_une_competence à true \
et rédige la compétence : des instructions structurées, concrètes, débarrassées du style \
« réseau social », que l'assistant pourra appliquer.
- Si c'est du divertissement, un meme, une pub, ou trop vague pour être actionnable, \
mets vaut_une_competence à false et laisse les champs competence_* avec une chaîne vide.
- Rédige tout en français (le slug reste en ascii kebab-case).
- Si la transcription est absente, base-toi uniquement sur la légende et reste prudent \
sur ce que tu affirmes."""


def distill(post_meta, caption, transcript):
    import anthropic

    client = anthropic.Anthropic()
    prompt = DISTILL_PROMPT.format(
        owner=post_meta["owner"],
        date=post_meta["date"],
        caption=caption or "(pas de légende)",
        transcript=transcript or "(pas de transcription disponible)",
    )
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8000,
        output_config={"format": {"type": "json_schema", "schema": DISTILL_SCHEMA}},
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("distillation refusée par le modèle")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


# ---------------------------------------------------------------- écriture

def slugify(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value[:60] or "sans-titre"


def write_note(post_meta, result, caption, transcript):
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(result["slug"])
    path = KNOWLEDGE_DIR / f"{post_meta['date']}-{slug}.md"
    tags = ", ".join(result.get("tags", []))
    body = f"""---
titre: "{result['titre']}"
source: {post_meta['url']}
auteur: "@{post_meta['owner']}"
date_enregistrement: {post_meta['date']}
tags: [{tags}]
competence: {"ig-" + slug if result["vaut_une_competence"] else "aucune"}
---

# {result['titre']}

{result['resume']}

## Légende originale

{caption or "(pas de légende)"}

## Transcription

{transcript or "(pas de transcription disponible)"}
"""
    path.write_text(body, encoding="utf-8")
    return path


def write_skill(result, post_meta):
    slug = slugify(result["slug"])
    skill_dir = SKILLS_DIR / f"ig-{slug}"
    skill_dir.mkdir(parents=True, exist_ok=True)
    description = " ".join(result["competence_description"].split())[:1000]
    body = f"""---
name: ig-{slug}
description: {description}
---

# {result['competence_nom'] or result['titre']}

> Source : reel Instagram de @{post_meta['owner']} — {post_meta['url']}
> Note complète (légende + transcription) : knowledge/instagram/{post_meta['date']}-{slug}.md

{result['competence_instructions']}
"""
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    return skill_dir


# ---------------------------------------------------------------- boucle principale

def process_post(post):
    post_meta = {
        "shortcode": post.shortcode,
        "url": f"https://www.instagram.com/p/{post.shortcode}/",
        "owner": post.owner_username,
        "date": post.date_utc.strftime("%Y-%m-%d"),
    }
    caption = (post.caption or "").strip()
    transcript = None
    if post.is_video:
        transcript = get_transcript(post_meta["url"], post.video_url)

    result = distill(post_meta, caption, transcript)
    note_path = write_note(post_meta, result, caption, transcript)
    print(f"  Note : {note_path.relative_to(REPO_ROOT)}")

    if result["vaut_une_competence"] and result["competence_instructions"].strip():
        skill_dir = write_skill(result, post_meta)
        print(f"  Compétence : {skill_dir.relative_to(REPO_ROOT)}")
    else:
        print("  Pas assez actionnable pour une compétence — note seule.")

    return {
        "date": post_meta["date"],
        "owner": post_meta["owner"],
        "titre": result["titre"],
        "competence": result["vaut_une_competence"],
        "traite_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Configuration manquante : définis ANTHROPIC_API_KEY.")

    import instaloader

    state = load_state()
    loader = build_loader()
    profile = instaloader.Profile.from_username(
        loader.context, os.environ["IG_USERNAME"]
    )

    processed_this_run = 0
    known_streak = 0
    errors = 0

    print(f"Parcours des enregistrements de @{profile.username}…")
    for post in profile.get_saved_posts():
        if processed_this_run >= MAX_POSTS_PER_RUN:
            print(f"Limite de {MAX_POSTS_PER_RUN} posts par run atteinte.")
            break

        if post.shortcode in state["processed"]:
            known_streak += 1
            if known_streak >= STOP_AFTER_KNOWN:
                print("Que des posts déjà traités — arrêt.")
                break
            continue
        known_streak = 0

        if VIDEOS_ONLY and not post.is_video:
            state["processed"][post.shortcode] = {"ignore": "pas-une-video"}
            save_state(state)
            continue

        print(f"Nouveau save : {post.shortcode} (@{post.owner_username})")
        try:
            state["processed"][post.shortcode] = process_post(post)
            processed_this_run += 1
            save_state(state)  # sauvegarde incrémentale : un crash ne perd rien
        except Exception as exc:
            # non ajouté à l'état -> sera retenté au prochain run
            errors += 1
            print(f"  ERREUR sur {post.shortcode} : {exc} — retenté au prochain run.")

        time.sleep(6)  # rythme doux pour ne pas stresser l'API Instagram

    print(f"Terminé : {processed_this_run} traité(s), {errors} erreur(s).")
    if errors and processed_this_run == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
