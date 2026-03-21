#!/usr/bin/env python3
"""
Phase 2.1 — Semantic Category Tagging
======================================
Tags every lexical entry with one or more semantic categories by:
  1. Grammatical class rules (N-KIN → kinship, NUM → number, LOC → location)
  2. Keyword scanning across gloss definitions
  3. Etymology/literal-translation scanning for additional hints
  4. (Optional) Gemini API for entries untagged by rules

Results are written to the `semantic_tags` table in the SQLite database.
A review queue (JSON) is written for untagged entries and low-confidence cases.

Usage:
    # Rule-based only (fast):
    python tag_entries.py --db skiri_pawnee.db

    # Add Gemini for untagged entries:
    python tag_entries.py --db skiri_pawnee.db --gemini

    # Resume interrupted Gemini run:
    python tag_entries.py --db skiri_pawnee.db --gemini --checkpoint tag_checkpoint.json

    # Dry run (no DB writes):
    python tag_entries.py --db skiri_pawnee.db --dry-run
"""

import argparse
import json
import logging
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# =============================================================================
# Taxonomy
# =============================================================================
# Each category has:
#   keywords    — matched as whole words against lowercased gloss text
#   gram_classes — grammatical classes that auto-assign this tag at high confidence

TAXONOMY: dict[str, dict] = {
    "animal": {
        "gram_classes": [],
        "keywords": [
            "buffalo","bison","bear","beaver","deer","elk","antelope","pronghorn",
            "wolf","coyote","fox","dog","horse","mule","rabbit","hare","otter",
            "mink","skunk","badger","raccoon","weasel","marten","opossum",
            "squirrel","prairie dog","rat","mouse","porcupine","lynx","bobcat",
            "mountain lion","panther","moose","cattle","cow","bull","calf","pig",
            "sheep","goat","cat","monkey","elephant","camel",
            "eagle","hawk","owl","crow","raven","turkey","duck","goose","swan",
            "crane","heron","plover","sandpiper","godwit","curlew","snipe",
            "killdeer","woodpecker","flicker","kingfisher","swallow","martin",
            "wren","sparrow","robin","meadowlark","blackbird","oriole","bluebird",
            "bunting","grosbeak","finch","warbler","vireo","nuthatch","chickadee",
            "magpie","jay","lark","quail","grouse","pheasant","pigeon","dove",
            "nighthawk","whippoorwill","hummingbird","pelican","cormorant",
            "grebe","coot","rail","bittern","buzzard","vulture","kite","osprey",
            "peregrine","merlin","kestrel","harrier","prairie chicken",
            "snake","rattlesnake","turtle","tortoise","lizard","frog","toad",
            "salamander","alligator",
            "fish","catfish","bass","pike","perch","trout","carp","sucker",
            "drum","gar","sturgeon",
            "insect","beetle","fly","bee","wasp","ant","grasshopper","cricket",
            "butterfly","moth","worm","spider","tick","louse","lice","flea",
            "bug","dragonfly","firefly",
            "bird","fowl","waterfowl","animal","beast","creature",
            "hide","fur","feather","antler","hoof","claw","talon",
            "nest","burrow","den","flock","herd","pack",
        ],
    },
    "plant": {
        "gram_classes": [],
        "keywords": [
            "tree","shrub","bush","grass","reed","sedge","rush","cattail",
            "bulrush","willow","cottonwood","elm","oak","cedar","pine","juniper",
            "plum","cherry","chokecherry","serviceberry","hackberry","mulberry",
            "grape","gooseberry","currant","elderberry","berry","berries","rose",
            "briar","sunflower","milkweed","thistle","ragweed","sagebrush","sage",
            "artemisia","yucca","cactus","mushroom","fungus",
            "corn","maize","bean","squash","gourd","pumpkin","tobacco","herb",
            "root","bulb","tuber","turnip","wild onion","onion","potato",
            "blossom","flower","seed","pod","leaf","leaves","bark","wood",
            "twig","branch","log","stump","trunk","sapling","sprout","vine",
            "black haw","buffaloberry","breadroot","prairie turnip",
        ],
    },
    "body": {
        "gram_classes": [],
        "keywords": [
            "head","skull","scalp","hair","forehead","temple","face","cheek",
            "chin","jaw","nose","nostril","eye","eyelid","eyelash","eyebrow",
            "ear","mouth","lip","tongue","tooth","teeth","molar","gum","gums",
            "throat","neck","nape",
            "shoulder","arm","elbow","wrist","hand","finger","thumb","palm",
            "knuckle","fingernail","nail",
            "chest","breast","nipple","rib","side","back","spine","loin",
            "abdomen","belly","navel","waist","hip","buttock","groin",
            "genitali","penis","vagina",
            "leg","thigh","knee","shin","calf","ankle","foot","heel","sole",
            "toe","toenail",
            "heart","lung","liver","kidney","stomach","intestine","bowel",
            "bladder","bone","marrow","tendon","sinew","muscle","skin","flesh",
            "fat","blood","vein","artery","brain","nerve","gland","organ",
            "breath","saliva","spit","urine","feces","sweat","tear","mucus",
            "snot","bile",
        ],
    },
    "kinship": {
        "gram_classes": ["N-KIN"],
        "keywords": [
            "father","mother","son","daughter","brother","sister",
            "grandfather","grandmother","grandchild","grandparent",
            "grandson","granddaughter","uncle","aunt","nephew","niece",
            "cousin","husband","wife","spouse","in-law","parent","child",
            "sibling","relative","kin","older brother","younger brother",
            "older sister","younger sister","stepfather","stepmother",
            "stepson","stepdaughter","co-wife","co-husband",
        ],
        # IMPORTANT: kinship keyword matching is restricted to noun entries only.
        # Verbs whose *glosses* mention family members (e.g., "be married to",
        # "adopt a child", "take care of someone") must NOT receive this tag —
        # they describe kin-related actions, not kin terms themselves.
        # This guard is enforced in tag_entry() below.
        # Source of fix: piraski audit 2026-03-21 found 33 verb false positives.
        "noun_only_keyword": True,
    },
    "food": {
        "gram_classes": [],
        "keywords": [
            "food","eat","meal","feast","bread","meat","pemmican","jerky",
            "dried meat","cooked","boiled","roasted","fried","soup","stew",
            "broth","porridge","gruel","hominy","corn cake","corn bread",
            "mush","flour","dough","fat","tallow","lard","oil","butter",
            "cream","sugar","honey","salt","spice","seasoning","berry",
            "fruit","vegetable","grain","cereal","drink","beverage","tea",
            "coffee","milk","dried","smoked","preserved","jerked",
            "hunger","hungry","thirst","thirsty","cook","bake","roast",
            "boil","fry","stir","grind","pound","cracklings","pork rind",
            "bacon","toast","shortening","water",
        ],
    },
    "housing": {
        "gram_classes": [],
        "keywords": [
            "lodge","earthlodge","house","dwelling","tipi","tent","room",
            "chamber","floor","roof","wall","ceiling","door","entrance",
            "window","post","pillar","beam","fireplace","hearth","fire pit",
            "smoke hole","siding","partition","porch","threshold",
            "village","camp","campsite","settlement","store","trading post",
            "warehouse","barn","stable","outhouse","privy","toilet","bathroom",
            "sod house","canvas","tarp","cover","tipi cover",
            "bed","backrest","mat","build","construct","erect",
        ],
    },
    "celestial": {
        "gram_classes": [],
        "keywords": [
            "sun","moon","star","planet","sky","heaven","cloud","rain",
            "snow","hail","ice","frost","fog","mist","wind","storm",
            "thunder","lightning","rainbow","dawn","dusk","sunrise","sunset",
            "twilight","day","night","noon","midnight","spring","summer",
            "fall","autumn","winter","season","month","year",
            "january","february","march","april","may","june","july",
            "august","september","october","november","december",
            "cold","hot","warm","cool","freeze","north","south","east","west",
            "morning star","evening star","milky way",
        ],
    },
    "ceremony": {
        "gram_classes": [],
        "keywords": [
            "ceremony","ritual","sacred","holy","medicine","bundle",
            "dance","song","sing","pray","prayer","offering","sacrifice",
            "pipe","smoke","tobacco","incense","shaman","doctor","heal",
            "cure","blessing","bless","supernatural","spirit","ghost",
            "vision","sweat lodge","sweatlodge","sweat bath","drum","rattle",
            "flute","feast","giveaway","war bundle","medicine bundle","power",
            "sun dance","ghost dance","corn dance","initiation","rite","rites",
            "witch","witchcraft","sorcery","charm","amulet","talisman","fetish",
        ],
    },
    "tool": {
        "gram_classes": [],
        "keywords": [
            "arrow","bow","quiver","lance","spear","club","tomahawk","knife",
            "blade","axe","hatchet","gun","rifle","pistol","shield","armor",
            "tool","implement","instrument","utensil","pot","kettle","vessel",
            "container","basket","bag","pouch","sack","pack","bundle",
            "rope","cord","string","strap","lace","needle","awl","scraper",
            "flesher","tanner","hammer","mallet","chisel","wedge","net","trap",
            "snare","lure","saddle","bridle","halter","rein","stirrup",
            "horseshoe","plow","hoe","rake","shovel",
            "digging stick","grinding stone","mortar","pestle","comb","brush",
            "razor","paddle","oar","canoe","sled","travois","wagon","cart",
            "wheel","toothpick",
        ],
    },
    "clothing": {
        "gram_classes": [],
        "keywords": [
            "moccasin","shoe","boot","sandal","robe","blanket","coat",
            "jacket","shirt","dress","legging","breechcloth","skirt","apron",
            "belt","sash","strap","tie","ribbon","hat","cap","bonnet",
            "headdress","glove","mitten","necklace","bracelet","ring",
            "earring","pendant","bead","beadwork","quillwork","paint",
            "tattoo","decoration","ornament","adorn","feather","plume",
            "roach","buckskin","hide","leather","tanned","woven","weave",
            "cloth","fabric","textile","hair tie","braid tie",
            "clothing","garment","wear",
        ],
    },
    "color": {
        "gram_classes": [],
        "keywords": [
            "red","reddish","scarlet","crimson","blue","bluish","azure",
            "green","greenish","yellow","yellowish","golden","orange",
            "white","whitish","pale","albino","black","blackish","dark",
            "gray","grey","greyish","brown","brownish","tan","purple",
            "violet","spotted","striped","mottled","speckled",
            "colored","colour","color","hue","tint",
        ],
    },
    "number": {
        "gram_classes": ["NUM"],
        "keywords": [
            "one","two","three","four","five","six","seven","eight","nine",
            "ten","eleven","twelve","twenty","thirty","forty","fifty",
            "hundred","thousand","first","second","third","fourth","fifth",
            "once","twice","times","count","numeral","quantity",
            "many","few","several","half","quarter","double",
        ],
    },
    "location": {
        "gram_classes": ["LOC"],
        "keywords": [
            "place","location","area","region","territory",
            "here","there","where","somewhere","inside","outside","above",
            "below","under","near","far","distant","close","left","right",
            "front","behind","top","bottom","edge","corner","center",
            "along","across","through","around","between","upriver",
            "downriver","upstream","downstream","uphill","downhill",
            "upland","lowland","bank","cliff","precipice","slope",
        ],
    },
    "social": {
        "gram_classes": [],
        "keywords": [
            "tribe","band","clan","moiety","phratry","nation","people",
            "group","society","association","chief","leader","headman",
            "council","warrior","soldier","scout","brave","enemy","friend",
            "ally","stranger","slave","captive","prisoner","race","nationality",
            "pawnee","skiri","kitkahahki","pitahawirata","chaui",
            "sioux","lakota","comanche","cheyenne","arapaho","osage","kansa",
            "kaw","omaha","ponca","arikara","wichita","caddo",
            "war","battle","raid","fight","victory","defeat","peace",
            "treaty","trade","law","custom","rule","tradition","gift",
            "giveaway","exchange","marriage","divorce","widow","orphan",
            "adoption","elder","man","woman","boy","girl","male","female",
            # Age/gender/social role terms — explicitly social, not kinship.
            # These were previously mis-tagged as kinship via keyword match.
            # boy, girl → social age category; elderly woman/man → social role
            "youth","lad","maiden","lass","young man","young woman",
            "old man","old woman","elderly","aged","infant","baby",
            "adolescent","pubescent","adult","middle-aged",
        ],
    },
    "land": {
        "gram_classes": [],
        "keywords": [
            "hill","mountain","butte","bluff","ridge","mesa","valley",
            "plain","prairie","meadow","field","forest","woodland","timber",
            "grove","swamp","marsh","bog","wetland","sand","soil","clay",
            "dirt","mud","rock","stone","gravel","pebble","boulder","cave",
            "ravine","canyon","gully","arroyo","trail","path","road",
            "crossing","bridge","ford","island","peninsula","shore",
        ],
    },
    "water": {
        "gram_classes": [],
        "keywords": [
            "water","river","stream","creek","brook","lake","pond","pool",
            "spring","well","rain","snow","ice","flood","swimming","swim",
            "wade","boat","canoe","ferry","wet","dry","damp","moist",
            "current","flow","ripple","wave",
        ],
    },
    "emotion": {
        "gram_classes": [],
        "keywords": [
            "happy","happiness","glad","joy","joyful","pleased","sad",
            "sadness","grieve","mourn","sorrow","grief","angry","anger",
            "mad","rage","furious","afraid","fear","scared","frighten",
            "terror","love","affection","fond","hate","dislike","despise",
            "ashamed","shame","embarrassed","proud","pride","jealous","envy",
            "lonesome","lonely","homesick","worry","anxious","nervous",
            "brave","courage","coward","good thoughts","good feelings",
            "kind","kindhearted","pity","compassion","mercy",
        ],
    },
    "speech": {
        "gram_classes": [],
        "keywords": [
            "say","said","speak","speech","talk","tell","shout","yell",
            "call","cry out","announce","sing","song","chant","ask",
            "question","answer","reply","name","word","language","tongue",
            "story","tale","narrative","promise","vow","oath","order",
            "command","instruct","laugh","cry","weep","greet","greeting",
            "farewell","whisper","murmur","sound","noise","voice",
            "interpret","translate","lie","deceive","truth",
        ],
    },
    "motion": {
        "gram_classes": [],
        "keywords": [
            "go","come","walk","run","move","travel","journey","trip",
            "arrive","depart","leave","return","enter","exit","pass through",
            "ride","drive","lead","carry","bring","take","follow","chase",
            "flee","escape","swim","fly","jump","leap","crawl","creep",
            "sneak","wander","roam","migrate",
        ],
    },
}

# =============================================================================
# Pre-compiled patterns (built once at module load for speed)
# =============================================================================

def _build_patterns(taxonomy: dict) -> dict[str, re.Pattern]:
    """Build one combined OR pattern per category from keyword list."""
    compiled = {}
    for tag, info in taxonomy.items():
        kws = info["keywords"]
        if not kws:
            continue
        # Sort by length descending so longer phrases match before shorter ones
        sorted_kws = sorted(kws, key=len, reverse=True)
        pattern = r'\b(?:' + '|'.join(re.escape(k) for k in sorted_kws) + r')\b'
        compiled[tag] = re.compile(pattern, re.IGNORECASE)
    return compiled

PATTERNS = _build_patterns(TAXONOMY)

# Gram-class → tag mapping (built from taxonomy)
GRAM_CLASS_TAGS: dict[str, list[str]] = {}
for _tag, _info in TAXONOMY.items():
    for _gc in _info["gram_classes"]:
        GRAM_CLASS_TAGS.setdefault(_gc, []).append(_tag)


# =============================================================================
# Tagging logic
# =============================================================================

def tag_entry(gram_class: str, gloss_texts: list[str],
              literal_translation: str, raw_etymology: str) -> list[tuple[str, str, str]]:
    """
    Returns deduplicated list of (tag, source, confidence).
    Priority: gram_class > keyword > etymology

    Special rules:
      kinship — keyword match is suppressed for verb grammatical classes.
                Verbs whose glosses mention family (e.g. "be married to",
                "adopt a child") are describing kin-related actions, not kin
                terms. Only nouns (N, N-KIN, N-DEP) may receive kinship via
                keyword match. gram_class route (N-KIN → kinship) is unaffected.
    """
    priority = {"gram_class": 3, "keyword": 2, "etymology": 1}
    best: dict[str, tuple[str, str, str]] = {}

    # Noun grammatical classes (for kinship noun-only guard)
    NOUN_CLASSES = {"N", "N-KIN", "N-DEP"}
    is_noun = gram_class and any(nc in gram_class for nc in NOUN_CLASSES)

    # 1. Gram-class rules
    for gc_prefix, tags in GRAM_CLASS_TAGS.items():
        if gram_class and gc_prefix in gram_class:
            for tag in tags:
                best[tag] = (tag, "gram_class", "high")

    # 2. Keyword scan on gloss text
    gloss_blob = " ".join(gloss_texts).lower()
    if gloss_blob:
        for tag, pattern in PATTERNS.items():
            if pattern.search(gloss_blob):
                # Guard: kinship keyword only fires for noun grammatical classes
                if tag == "kinship" and not is_noun:
                    continue  # verbs mentioning family are not kinship terms
                if tag not in best or priority["keyword"] > priority[best[tag][1]]:
                    best[tag] = (tag, "keyword", "medium")

    # 3. Etymology scan (lower confidence)
    etym_blob = " ".join(filter(None, [literal_translation, raw_etymology])).lower()
    if etym_blob:
        for tag, pattern in PATTERNS.items():
            if pattern.search(etym_blob):
                # Same guard applies at etymology level
                if tag == "kinship" and not is_noun:
                    continue
                if tag not in best:
                    best[tag] = (tag, "etymology", "low")

    return list(best.values())


# =============================================================================
# Gemini tagging
# =============================================================================

GEMINI_SYSTEM_PROMPT = """You are a Skiri Pawnee linguistic expert helping classify dictionary entries into semantic categories.

Given a batch of dictionary entries, assign each entry zero or more tags from this fixed taxonomy:

TAXONOMY (use only these exact tag names):
  animal      - fauna: mammals, birds, fish, reptiles, insects
  plant       - flora: trees, grasses, crops, fungi
  body        - body parts and anatomy
  kinship     - family relations and kin terms
  food        - food, drink, cooking, hunger/thirst
  housing     - dwellings, structures, furniture
  celestial   - sky, weather, seasons, time of day/year
  ceremony    - ritual, sacred practices, medicine, dance
  tool        - tools, weapons, implements, containers, vehicles
  clothing    - garments, adornment, jewelry
  color       - color and visual appearance terms
  number      - numerals and quantifiers
  location    - spatial/directional terms, place descriptions
  social      - tribal, political, social, war/peace, gender roles
  land        - terrain, geography, landscape features
  water       - rivers, lakes, moisture, aquatic contexts
  emotion     - feelings, mental states, attitudes
  speech      - communication, language, sound production
  motion      - movement and travel verbs

Rules:
- Multiple tags allowed per entry
- Return empty list [] if no category clearly applies
- Focus on the PRIMARY meaning; do not over-tag
- Consider ALL gloss definitions for an entry when assigning tags

Respond ONLY with a JSON object mapping entry_id to an array of tags:
{
  "SK-example-p1-1": ["animal", "food"],
  "SK-other-p2-3": []
}"""


def gemini_tag_batch(entries: list[dict], model_name: str = "gemini-2.5-flash",
                     max_retries: int = 3) -> dict[str, list[str]]:
    """
    Send a batch of entries to Gemini for tagging.
    entries: list of {entry_id, headword, grammatical_class, glosses}
    Returns dict of entry_id → [tag, ...]
    """
    try:
        from google import genai
    except ImportError:
        log.error("google-genai not installed. Run: pip install google-genai")
        sys.exit(1)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    # Build user message
    batch_text = json.dumps(entries, ensure_ascii=False, indent=2)
    prompt = (
        "Classify each of these Skiri Pawnee dictionary entries into semantic categories.\n\n"
        f"{batch_text}"
    )

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "system_instruction": GEMINI_SYSTEM_PROMPT,
                    "temperature": 0.1,
                },
            )
            text = response.text.strip()

            # Strip markdown fences if present
            if text.startswith("```"):
                text = re.sub(r'^```(?:json)?\s*', '', text)
                text = re.sub(r'\s*```$', '', text)

            result = json.loads(text)
            # Validate tags
            valid_tags = set(TAXONOMY.keys())
            cleaned = {}
            for eid, tags in result.items():
                cleaned[eid] = [t for t in tags if t in valid_tags]
            return cleaned

        except json.JSONDecodeError as e:
            log.warning("Gemini returned invalid JSON on attempt %d: %s", attempt, e)
        except Exception as e:
            log.warning("Gemini API error on attempt %d: %s", attempt, e)
            if attempt < max_retries:
                wait = 15 * attempt
                log.info("Retrying in %ds...", wait)
                time.sleep(wait)

    log.error("Gemini batch failed after %d attempts", max_retries)
    return {}


# =============================================================================
# Database operations
# =============================================================================

MIGRATE_SQL = """
CREATE TABLE IF NOT EXISTS semantic_tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id    TEXT NOT NULL REFERENCES lexical_entries(entry_id) ON DELETE CASCADE,
    tag         TEXT NOT NULL,
    source      TEXT NOT NULL DEFAULT 'keyword',
    confidence  TEXT NOT NULL DEFAULT 'medium',
    UNIQUE(entry_id, tag)
);
CREATE INDEX IF NOT EXISTS idx_semantic_tag ON semantic_tags(tag);
CREATE INDEX IF NOT EXISTS idx_semantic_entry ON semantic_tags(entry_id);
"""


def ensure_table(conn: sqlite3.Connection) -> None:
    for stmt in MIGRATE_SQL.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(stmt)
    conn.commit()


def fetch_entries(conn: sqlite3.Connection) -> list[tuple]:
    """Return list of (entry_id, gram_class, gloss_texts, literal_translation, raw_etymology)."""
    cur = conn.cursor()
    cur.execute("SELECT entry_id, grammatical_class FROM lexical_entries")
    rows = cur.fetchall()

    results = []
    for entry_id, gram_class in rows:
        g_cur = conn.cursor()
        g_cur.execute("SELECT definition FROM glosses WHERE entry_id = ?", (entry_id,))
        gloss_texts = [r[0] for r in g_cur.fetchall() if r[0]]

        e_cur = conn.cursor()
        e_cur.execute(
            "SELECT literal_translation, raw_etymology FROM etymology WHERE entry_id = ?",
            (entry_id,)
        )
        row = e_cur.fetchone()
        lit_trans = (row[0] or "") if row else ""
        raw_etym = (row[1] or "") if row else ""

        results.append((entry_id, gram_class or "", gloss_texts, lit_trans, raw_etym))

    return results


def write_tags(conn: sqlite3.Connection, entry_id: str,
               tags: list[tuple[str, str, str]], dry_run: bool) -> int:
    if dry_run or not tags:
        return len(tags)
    cur = conn.cursor()
    for tag, source, confidence in tags:
        cur.execute("""
            INSERT OR REPLACE INTO semantic_tags (entry_id, tag, source, confidence)
            VALUES (?, ?, ?, ?)
        """, (entry_id, tag, source, confidence))
    return len(tags)


def load_checkpoint(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"tagged_ids": []}


def save_checkpoint(path: Path, checkpoint: dict) -> None:
    path.write_text(json.dumps(checkpoint, ensure_ascii=False), encoding="utf-8")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Phase 2.1 — Semantic category tagging")
    parser.add_argument("--db", required=True, help="Path to skiri_pawnee.db")
    parser.add_argument("--review", default="tag_review_queue.json",
                        help="Output path for review queue JSON")
    parser.add_argument("--gemini", action="store_true",
                        help="Use Gemini API to tag entries that rules cannot classify")
    parser.add_argument("--gemini-model", default="gemini-2.5-flash",
                        help="Gemini model name (default: gemini-2.5-flash)")
    parser.add_argument("--gemini-batch", type=int, default=30,
                        help="Entries per Gemini batch (default: 30)")
    parser.add_argument("--checkpoint", default="tag_checkpoint.json",
                        help="Checkpoint file for resuming Gemini run")
    parser.add_argument("--dry-run", action="store_true",
                        help="Compute tags but do not write to database")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        log.error("Database not found: %s", db_path)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    if not args.dry_run:
        ensure_table(conn)
        conn.execute("DELETE FROM semantic_tags WHERE source != 'manual'")
        conn.commit()
        log.info("Cleared existing auto-generated tags")

    entries = fetch_entries(conn)
    log.info("Loaded %d entries from database", len(entries))

    tag_counts: dict[str, int] = {tag: 0 for tag in TAXONOMY}
    untagged: list[dict] = []
    total_written = 0

    # --- Pass 1: rule-based ---
    log.info("Running rule-based tagging...")
    for entry_id, gram_class, gloss_texts, lit_trans, raw_etym in entries:
        tags = tag_entry(gram_class, gloss_texts, lit_trans, raw_etym)
        if not tags:
            untagged.append({
                "entry_id": entry_id,
                "grammatical_class": gram_class,
                "glosses": gloss_texts,
            })
        else:
            for tag, source, confidence in tags:
                tag_counts[tag] += 1
            total_written += write_tags(conn, entry_id, tags, args.dry_run)

    if not args.dry_run:
        conn.commit()

    log.info("Rule-based: %d tagged, %d untagged", len(entries) - len(untagged), len(untagged))

    # --- Pass 2: Gemini for untagged entries ---
    if args.gemini and untagged:
        checkpoint_path = Path(args.checkpoint)
        checkpoint = load_checkpoint(checkpoint_path)
        already_done = set(checkpoint["tagged_ids"])

        remaining = [e for e in untagged if e["entry_id"] not in already_done]
        log.info("Gemini pass: %d entries to classify (%d already done from checkpoint)",
                 len(remaining), len(already_done))

        batch_size = args.gemini_batch
        gemini_tagged = 0
        gemini_untagged_ids = []

        for i in range(0, len(remaining), batch_size):
            batch = remaining[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(remaining) + batch_size - 1) // batch_size
            log.info("Gemini batch %d/%d (%d entries)...", batch_num, total_batches, len(batch))

            # Build minimal entry objects for the prompt
            batch_input = [
                {
                    "entry_id": e["entry_id"],
                    "grammatical_class": e["grammatical_class"],
                    "glosses": e["glosses"],
                }
                for e in batch
            ]

            result = gemini_tag_batch(batch_input, model_name=args.gemini_model)

            for entry in batch:
                eid = entry["entry_id"]
                tags_from_gemini = result.get(eid, [])
                if tags_from_gemini:
                    tag_tuples = [(t, "gemini", "medium") for t in tags_from_gemini]
                    for t, _, _ in tag_tuples:
                        tag_counts[t] += 1
                    total_written += write_tags(conn, eid, tag_tuples, args.dry_run)
                    gemini_tagged += 1
                    # Remove from untagged list
                    untagged[:] = [u for u in untagged if u["entry_id"] != eid]
                else:
                    gemini_untagged_ids.append(eid)

                checkpoint["tagged_ids"].append(eid)

            if not args.dry_run:
                conn.commit()
            save_checkpoint(checkpoint_path, checkpoint)

            # Brief delay to respect rate limits
            if i + batch_size < len(remaining):
                time.sleep(1)

        log.info("Gemini pass complete: %d newly tagged, %d still untagged",
                 gemini_tagged, len(untagged))

    conn.close()

    # --- Summary ---
    log.info("=" * 60)
    log.info("Tagging complete%s", " (dry run)" if args.dry_run else "")
    log.info("  Total entries:   %d", len(entries))
    log.info("  Tagged entries:  %d", len(entries) - len(untagged))
    log.info("  Untagged:        %d", len(untagged))
    log.info("  Tag assignments: %d", total_written)
    log.info("")
    log.info("Tag distribution:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        if count:
            log.info("  %-16s %d", tag, count)

    # --- Review queue ---
    review = {
        "summary": {
            "total_entries": len(entries),
            "tagged": len(entries) - len(untagged),
            "untagged": len(untagged),
            "tag_distribution": {t: c for t, c in sorted(tag_counts.items(), key=lambda x: -x[1]) if c},
        },
        "untagged_entries": untagged,
    }
    review_path = Path(args.review)
    review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Review queue → %s (%d untagged)", review_path, len(untagged))


if __name__ == "__main__":
    main()
