"""
Phase 4.1 — Weekly flashcard set generator for Skiri Pawnee learners.

Curates ~15 high-value beginner words per category, split into weekly
sets of 10-20. Each category gets 1-2 weeks max — the goal is a
manageable study plan (~20 weeks), not an exhaustive dump.

Selection priorities:
  1. Blue Book-attested entries (used in teaching materials)
  2. Nouns (concrete, easy to learn)
  3. Short headwords (simpler words first)
  4. Entries with clear, concise definitions
"""

import sqlite3
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FlashCard:
    entry_id: str
    headword: str
    normalized_form: Optional[str] = None
    simplified_pronunciation: Optional[str] = None
    phonetic_form: Optional[str] = None
    definition: str = ""
    grammatical_class: Optional[str] = None
    blue_book_attested: bool = False


@dataclass
class FlashCardSet:
    week: int
    category: str
    category_label: str
    cards: List[FlashCard] = field(default_factory=list)

    @property
    def card_count(self) -> int:
        return len(self.cards)


# Display labels and max cards per category
CATEGORIES = {
    "kinship":   {"label": "Family & Kinship",         "max": 20},
    "number":    {"label": "Numbers & Counting",       "max": 20},
    "animal":    {"label": "Animals",                   "max": 30},
    "body":      {"label": "Body & Health",             "max": 20},
    "food":      {"label": "Food & Cooking",            "max": 20},
    "clothing":  {"label": "Clothing & Adornment",      "max": 15},
    "housing":   {"label": "Home & Shelter",            "max": 15},
    "color":     {"label": "Colors & Appearance",       "max": 15},
    "celestial": {"label": "Sky, Stars & Weather",      "max": 20},
    "water":     {"label": "Water & Rivers",            "max": 15},
    "plant":     {"label": "Plants & Trees",            "max": 20},
    "tool":      {"label": "Tools & Objects",           "max": 15},
    "land":      {"label": "Land & Earth",              "max": 15},
    "emotion":   {"label": "Feelings & Emotions",       "max": 15},
    "ceremony":  {"label": "Ceremony & Sacred",         "max": 15},
    "social":    {"label": "People & Society",          "max": 20},
    "speech":    {"label": "Language & Communication",   "max": 15},
    "motion":    {"label": "Movement & Travel",         "max": 15},
    "location":  {"label": "Places & Directions",       "max": 15},
}

# Category ordering for the curriculum (learner-friendly progression)
CATEGORY_ORDER = [
    "kinship", "number", "animal", "body", "food", "clothing",
    "housing", "color", "celestial", "water", "plant", "tool",
    "land", "emotion", "ceremony", "social", "speech", "motion",
    "location",
]

SET_SIZE = 15  # target cards per weekly set

# ---- Flashcard category filters ----
# The semantic tags from Phase 2.1 are noisy (keyword-matched on full definitions),
# so we filter flashcard entries by checking the definition starts with or is
# primarily about the category topic. For each category we define:
#   "require": keywords that MUST appear (at least one) — checked as whole words
#   "reject": keywords that disqualify an entry (overrides require)
#   "gram": if set, restrict to these grammatical classes
# Categories with None use no filter.

import re

CATEGORY_FILTERS = {
    "kinship": {
        "require": {"mother", "father", "sister", "brother", "son", "daughter",
                     "uncle", "aunt", "grandmother", "grandfather", "grandchild",
                     "grandson", "granddaughter", "wife", "husband", "spouse",
                     "cousin", "nephew", "niece", "child", "parent", "sibling",
                     "relative", "kin", "in-law", "family"},
        "reject": {"jesus", "quiet", "silent"},
        "gram": {"N", "N-KIN", "N-DEP"},
    },
    "number": {
        # Numbers are best filtered by grammatical class — NUM entries
        # are reliable. For nouns, only allow money/counting terms.
        "require": {"nickel", "dime", "cent", "penny", "dollar",
                     "quarter", "half", "playing cards"},
        "reject": set(),
        "gram": {"NUM"},  # strict: only NUM class
        "_also_allow_n_with_require": True,  # see _entry_matches_category
    },
    "animal": {
        "require": {"animal", "bird", "fish", "insect", "snake", "turtle",
                     "bear", "deer", "elk", "horse", "dog", "cat", "wolf",
                     "eagle", "hawk", "owl", "buffalo", "beaver", "rabbit",
                     "coyote", "bull", "cow", "calf", "duck", "goose",
                     "frog", "toad", "lizard", "mouse", "squirrel", "skunk",
                     "fox", "otter", "mink", "bee", "wasp", "spider",
                     "prairie dog", "magpie", "crow", "turkey", "chicken",
                     "sparrow", "louse", "tick", "grouse", "quail",
                     "hare", "pig", "hog", "peccary", "tomcat"},
        "reject": {"be stretched", "hang suspended", "take,", "carry;",
                    "climb", "bark shrilly"},
        "gram": {"N"},
    },
    "body": {
        "require": {"foot", "hand", "head", "face", "eye", "ear", "nose",
                     "mouth", "tongue", "tooth", "teeth", "hair", "arm",
                     "leg", "finger", "toe", "chest", "breast", "back",
                     "neck", "shoulder", "knee", "belly", "stomach",
                     "heart", "bone", "skin", "blood", "body", "lip",
                     "chin", "forehead", "elbow", "wrist", "ankle",
                     "throat", "lung", "liver", "rib", "thigh", "carcass",
                     "corpse", "fat", "urine", "breath"},
        "reject": {"sixteen", "bracelet", "wristwatch", "climb"},
        "gram": {"N", "N-DEP"},
    },
    "food": {
        "require": {"food", "bread", "meat", "corn", "bean", "squash",
                     "berry", "fruit", "apple", "peach", "mush", "porridge",
                     "salt", "pie", "acorn", "potato", "turnip", "nut",
                     "sugar", "lard", "hominy", "apricot", "orange",
                     "plum", "cherry", "grape", "cook", "roast",
                     "dried meat", "pemmican", "stew", "soup", "fat",
                     "cornbread", "cornmeal", "pepper", "flour"},
        "reject": {"snake", "suspended", "water;", "get into water",
                    "pig", "hog", "peccary", "mink", "river", "crayfish",
                    "crawfish", "buckskin", "legging", "carbuncle", "boil,",
                    "tadpole", "paunch", "hide;", "peeling", "island"},
        "gram": {"N", "N-DEP"},
    },
    "clothing": {
        "require": {"moccasin", "robe", "blanket", "shawl", "shirt",
                     "legging", "dress", "breechcloth", "belt", "shoe",
                     "hat", "cap", "glove", "mitten", "sock", "feather",
                     "bead", "bracelet", "necklace", "earring", "pendant",
                     "cloth", "hide", "buckskin", "silk", "satin",
                     "calico", "material", "wrap", "paint", "handkerchief"},
        "reject": {"bee", "wasp", "tongue", "hornet"},
        "gram": {"N", "N-DEP"},
    },
    "housing": {
        "require": {"house", "lodge", "tipi", "dwelling", "village", "bed",
                     "roof", "door", "floor", "wall", "room", "fire",
                     "firewood", "mat", "mattress", "sheet", "pillow",
                     "stove", "oven", "chair", "table", "bowl", "dish",
                     "plate", "kettle", "pot", "bucket", "school", "jail",
                     "church", "barn", "camp", "tent", "linoleum",
                     "basement"},
        "reject": {"tribe", "band", "be sticking", "be lying", "be upright",
                    "suspended", "dance", "level ground", "clearing",
                    "meadow", "former skiri village", "wolves (standing)"},
        "gram": {"N"},
    },
    "color": {
        "require": {"black", "white", "red", "yellow", "blue", "green",
                     "brown", "gray", "grey", "spotted", "striped",
                     "paint", "colored", "dark", "pale"},
        "reject": {"prairie dog", "bear (", "fox (", "be slender", "deer",
                    "bean", "corn", "dogwood", "bee", "wasp", "hornet",
                    "magpie", "quail", "flicker", "yellowhammer",
                    "grass", "reed", "marsh"},
        "gram": {"N", "ADJ", "VD"},
    },
    "celestial": {
        "require": {"moon", "sun", "star", "sky", "cloud", "rain", "snow",
                     "hail", "wind", "thunder", "lightning", "storm",
                     "night", "day", "summer", "winter", "spring", "autumn",
                     "fall", "weather", "cold", "hot", "warm", "freeze",
                     "ice", "frost", "constellation", "pleiades", "sleet"},
        "reject": {"frog", "mother", "face", "wolf", "coyote"},
        "gram": None,  # allow ADV like "at night"
    },
    "water": {
        "require": {"water", "river", "creek", "stream", "lake", "pond",
                     "spring", "rain", "flood", "island", "fish", "swim",
                     "canoe", "boat", "bridge", "ice", "snow", "tadpole",
                     "ravine", "gully"},
        "reject": {"frog", "mother", "cradleboard", "wolf", "quiet",
                    "silent", "dry goods", "flicker", "grass", "hay",
                    "tribe", "mink", "paunch", "snake", "former skiri village"},
        "gram": {"N", "N-DEP"},
    },
    "plant": {
        "require": {"tree", "grass", "weed", "flower", "leaf", "root",
                     "seed", "bark", "branch", "wood", "stick", "bush",
                     "vine", "herb", "medicine", "corn", "bean", "squash",
                     "potato", "turnip", "berry", "fruit", "apple", "peach",
                     "mushroom", "oak", "cottonwood", "willow", "elm",
                     "cedar", "sage", "gourd", "acorn", "plum"},
        "reject": {"frog", "shield", "yelp", "suspended", "climb",
                    "bark shrilly"},
        "gram": {"N", "N-DEP"},
    },
    "tool": {
        "require": {"knife", "arrow", "bow", "ax", "axe", "scraper",
                     "awl", "needle", "pestle", "mortar", "kettle", "pot",
                     "bucket", "trap", "snare", "rope", "string", "cord",
                     "bag", "sack", "basket", "shield", "gun", "rifle",
                     "pipe", "hoe", "rake", "shovel", "hammer", "saw",
                     "oven", "tool", "instrument", "weapon"},
        "reject": {"foot", "paw", "tribe"},
        "gram": {"N"},
    },
    "land": {
        "require": {"land", "ground", "earth", "dirt", "sand", "rock",
                     "stone", "hill", "mountain", "valley", "prairie",
                     "plain", "field", "meadow", "ravine", "cliff",
                     "bluff", "mound", "cave", "clay", "mud", "sod",
                     "turf", "island"},
        "reject": {"prairie dog", "chicken", "hawk", "lizard", "climb"},
        "gram": {"N", "N-DEP"},
    },
    "emotion": None,  # emotion tags are generally OK
    "ceremony": {
        "require": {"dance", "ceremony", "ritual", "sacred", "medicine",
                     "bundle", "pipe", "song", "drum", "prayer", "spirit",
                     "doctor", "healer", "chief", "warrior", "paint",
                     "feather", "church", "worship"},
        "reject": {"tribe", "mother", "aunt"},
        "gram": None,
    },
    "social": None,  # social is broad by nature, OK as-is
    "speech": {
        "require": {"voice", "speech", "talk", "speak", "say", "tell",
                     "word", "language", "name", "song", "sing", "call",
                     "shout", "whisper", "mute", "tongue", "story"},
        "reject": {"tribe", "water", "get into"},
        "gram": None,
    },
    "motion": {
        "require": {"go", "walk", "run", "come", "bring", "carry", "move",
                     "crawl", "climb", "jump", "fly", "swim", "ride",
                     "travel", "return", "arrive", "leave", "enter",
                     "cross", "follow", "chase", "flee", "escape",
                     "direction", "train", "truck", "wagon"},
        "reject": set(),
        "gram": None,
    },
    "location": {
        "require": {"place", "village", "town", "city", "camp", "river",
                     "creek", "hill", "mountain", "valley", "prairie",
                     "field", "north", "south", "east", "west",
                     "middle", "center", "inside", "outside", "bridge",
                     "road", "path", "trail", "island", "lodge"},
        "reject": {"jesus", "snake", "baloney", "shoe", "moccasin",
                    "scraper", "bracelet", "outstanding", "warrior",
                    "shoulder", "back", "coccyx", "tailbone", "loin",
                    "buttock", "abdomen"},
        "gram": {"N", "N-DEP", "ADV"},
    },
}


def _word_match(keyword: str, text: str) -> bool:
    """Check if keyword appears as a whole word (or phrase) in text."""
    return bool(re.search(r'\b' + re.escape(keyword) + r'\b', text))


def _entry_matches_category(tag: str, definition: str, gram_class: str) -> bool:
    """Check if a definition actually matches its category topic."""
    filt = CATEGORY_FILTERS.get(tag)
    if filt is None:
        return True  # no filter for this category

    defn_lower = definition.lower()

    # Check reject list first
    reject = filt.get("reject", set())
    if any(kw in defn_lower for kw in reject):
        return False

    # Check grammatical class restriction
    allowed_gram = filt.get("gram")
    if allowed_gram:
        if gram_class in allowed_gram:
            return True  # class match is sufficient
        # Some categories also allow other classes if definition matches
        if filt.get("_also_allow_n_with_require"):
            require = filt.get("require", set())
            if require and any(_word_match(kw, defn_lower) for kw in require):
                return True
        return False

    # Check require list (at least one keyword must match as a whole word)
    require = filt.get("require", set())
    if require:
        return any(_word_match(kw, defn_lower) for kw in require)

    return True


def _fetch_top_entries(
    conn: sqlite3.Connection, tag: str, limit: int
) -> List[FlashCard]:
    """
    Fetch the best beginner-friendly entries for a category.
    Prioritizes BB-attested nouns with short, clear definitions.
    Filters out mis-tagged entries using definition keyword matching.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT le.entry_id, le.headword, le.normalized_form,
               le.simplified_pronunciation, le.phonetic_form,
               le.grammatical_class, le.blue_book_attested,
               (SELECT definition FROM glosses g
                WHERE g.entry_id = le.entry_id
                ORDER BY sense_number LIMIT 1) as definition
        FROM lexical_entries le
        JOIN semantic_tags st ON le.entry_id = st.entry_id
        WHERE st.tag = ?
          AND le.simplified_pronunciation IS NOT NULL
        ORDER BY
            le.blue_book_attested DESC,
            CASE
                WHEN le.grammatical_class IN ('N', 'N-KIN', 'N-DEP', 'NUM') THEN 0
                WHEN le.grammatical_class IN ('ADJ', 'ADV') THEN 1
                WHEN le.grammatical_class LIKE 'V%' THEN 2
                ELSE 3
            END,
            LENGTH(le.headword),
            le.headword
    """, (tag,))

    cards = []
    seen = set()
    for r in cur.fetchall():
        if len(cards) >= limit:
            break
        if r["entry_id"] in seen or not r["definition"]:
            continue

        defn = r["definition"]
        gram = r["grammatical_class"] or ""
        # Skip entries whose definition doesn't match the category
        if not _entry_matches_category(tag, defn, gram):
            continue

        seen.add(r["entry_id"])

        defn = r["definition"]
        # Skip entries with very long/technical definitions
        if len(defn) > 120:
            defn = defn[:117] + "..."

        cards.append(FlashCard(
            entry_id=r["entry_id"],
            headword=r["headword"],
            normalized_form=r["normalized_form"],
            simplified_pronunciation=r["simplified_pronunciation"],
            phonetic_form=r["phonetic_form"],
            definition=defn,
            grammatical_class=r["grammatical_class"],
            blue_book_attested=bool(r["blue_book_attested"]),
        ))

    return cards


def generate_all_sets(db_path: str) -> List[FlashCardSet]:
    """Generate all weekly flashcard sets from the database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    all_sets = []
    week_num = 1

    for cat in CATEGORY_ORDER:
        info = CATEGORIES.get(cat)
        if not info:
            continue
        label = info["label"]
        max_cards = info["max"]

        entries = _fetch_top_entries(conn, cat, max_cards)
        if not entries:
            continue

        # Split into weekly sets of SET_SIZE
        for i in range(0, len(entries), SET_SIZE):
            chunk = entries[i : i + SET_SIZE]
            # Merge small remainders into previous set
            if len(chunk) < 8 and all_sets and all_sets[-1].category == cat:
                all_sets[-1].cards.extend(chunk)
            else:
                all_sets.append(FlashCardSet(
                    week=week_num,
                    category=cat,
                    category_label=label,
                    cards=chunk,
                ))
                week_num += 1

    conn.close()
    return all_sets


def get_sets_by_category(db_path: str) -> dict:
    """Return sets grouped by category: {cat: [FlashCardSet, ...]}"""
    all_sets = generate_all_sets(db_path)
    by_cat = {}
    for s in all_sets:
        by_cat.setdefault(s.category, []).append(s)
    return by_cat


if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else "skiri_pawnee.db"
    sets = generate_all_sets(db)
    for s in sets:
        bb_count = sum(1 for c in s.cards if c.blue_book_attested)
        sys.stdout.buffer.write(
            f"Week {s.week:3d}: {s.category_label:30s} ({s.card_count:2d} cards"
            f"{f', {bb_count} BB' if bb_count else ''})\n".encode("utf-8")
        )
    print(f"\nTotal: {len(sets)} weeks, {sum(s.card_count for s in sets)} cards")
