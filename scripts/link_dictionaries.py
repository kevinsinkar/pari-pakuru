#!/usr/bin/env python3
"""
link_dictionaries.py — Link S2E and E2S with shared IDs, sync phonetic forms.

Place in: pari-pakuru/scripts/

1. Assigns a unique `entry_id` to every S2E entry (the primary record).
2. Matches each E2S subentry to its corresponding S2E entry via skiri_term/headword.
3. Writes the `entry_id` into the E2S subentry as `s2e_entry_id`.
4. Updates S2E phonetic_form with E2S's more accurate IPA transcription where matched.
5. Logs all links, phonetic updates, and unmatched entries.

Usage:
    python link_dictionaries.py                  # Link and sync both
    python link_dictionaries.py --dry-run        # Preview without writing
    python link_dictionaries.py --no-phonetic    # Link only, don't update phonetic forms

No API key required. Purely local.
"""

import json
import hashlib
import argparse
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DICT_DATA_DIR = PROJECT_ROOT / "Dictionary Data"

# Inputs: use normalized files
S2E_JSON = DICT_DATA_DIR / "skiri_to_english_normalized.json"
E2S_JSON = DICT_DATA_DIR / "english_to_skiri_normalized.json"

# Outputs
LINKED_S2E = DICT_DATA_DIR / "skiri_to_english_linked.json"
LINKED_E2S = DICT_DATA_DIR / "english_to_skiri_linked.json"
LINK_LOG = DICT_DATA_DIR / "link_changelog.json"
LINK_REPORT = DICT_DATA_DIR / "link_report.md"
LOG_FILE = SCRIPT_DIR / "link_dictionaries.log"

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("link_dictionaries")


# ===========================================================================
#  STEP 1: GENERATE ENTRY IDs FOR S2E
# ===========================================================================

def generate_entry_id(entry: dict, index: int) -> str:
    """
    Generate a stable, unique ID for an S2E entry.

    Format: SK-{headword_slug}-{page}-{index_on_page}

    Uses headword + page number + sequential index to disambiguate
    homonyms (same headword, different senses on same/different pages).
    """
    headword = entry.get("headword", "unknown")
    page = entry.get("entry_metadata", {}).get("page_number", 0)

    # Create a short slug from the headword (ASCII-safe)
    slug = headword.lower().strip()
    # Keep Skiri chars but make it filesystem-safe
    slug = slug.replace(" ", "_").replace("'", "").replace("ʔ", "q")
    slug = slug.replace("ʊ", "u").replace("ɪ", "i").replace("ə", "a")
    slug = slug.replace("č", "c").replace("á", "a").replace("í", "i")
    # Truncate to keep IDs manageable
    slug = slug[:30]

    return f"SK-{slug}-p{page}-{index:04d}"


def assign_s2e_ids(entries: list) -> dict:
    """
    Assign entry_id to every S2E entry. Returns headword → [entry] index.
    """
    headword_index = defaultdict(list)

    for i, entry in enumerate(entries):
        entry_id = generate_entry_id(entry, i)
        entry["entry_id"] = entry_id

        headword = entry.get("headword", "")
        if headword:
            headword_index[headword].append(i)

    log.info(f"Assigned {len(entries)} entry IDs to S2E")
    return headword_index


# ===========================================================================
#  STEP 2: MATCH E2S SUBENTRIES TO S2E ENTRIES
# ===========================================================================

def match_subentry_to_s2e(skiri_term: str, e2s_glosses: list,
                           s2e_entries: list, headword_index: dict) -> dict:
    """
    Find the best matching S2E entry for an E2S subentry.

    Matching strategy (in order of priority):
    1. Exact headword match (unique) — high confidence
    2. Headword match + gloss overlap — disambiguates homonyms
    3. Headword match only (first entry) — fallback for homonyms

    Returns:
        {"entry_id": str, "match_type": str, "confidence": str}
        or None if no match found.
    """
    if not skiri_term or skiri_term in ("N/A", "[Cross-reference]",
                                         "(see cross-reference)",
                                         "N/A - Cross-reference only",
                                         "N/A - See Cross-Reference",
                                         "[cross-reference]",
                                         "(see cross-references)"):
        return None

    candidates = headword_index.get(skiri_term, [])

    if not candidates:
        return None

    if len(candidates) == 1:
        idx = candidates[0]
        return {
            "entry_id": s2e_entries[idx]["entry_id"],
            "s2e_index": idx,
            "match_type": "exact_unique",
            "confidence": "high",
        }

    # Multiple S2E entries with same headword — disambiguate by gloss overlap
    e2s_gloss_words = set()
    for g in e2s_glosses:
        if isinstance(g, dict):
            defn = g.get("definition", "") or ""
        elif isinstance(g, str):
            defn = g
        else:
            continue
        e2s_gloss_words.update(w.lower().strip(".,;:()") for w in defn.split())

    best_idx = None
    best_overlap = 0

    for idx in candidates:
        s2e_entry = s2e_entries[idx]
        s2e_glosses = s2e_entry.get("part_I", {}).get("glosses", [])
        s2e_gloss_words = set()
        for g in s2e_glosses:
            if isinstance(g, dict):
                defn = g.get("definition", "") or ""
            elif isinstance(g, str):
                defn = g
            else:
                continue
            s2e_gloss_words.update(w.lower().strip(".,;:()") for w in defn.split())

        overlap = len(e2s_gloss_words & s2e_gloss_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_idx = idx

    if best_idx is not None and best_overlap > 0:
        return {
            "entry_id": s2e_entries[best_idx]["entry_id"],
            "s2e_index": best_idx,
            "match_type": "gloss_disambiguated",
            "confidence": "medium",
            "gloss_overlap": best_overlap,
        }

    # Fallback: take first candidate
    idx = candidates[0]
    return {
        "entry_id": s2e_entries[idx]["entry_id"],
        "s2e_index": idx,
        "match_type": "first_homonym_fallback",
        "confidence": "low",
    }


# ===========================================================================
#  STEP 3: LINK AND SYNC PHONETIC FORMS
# ===========================================================================

def link_and_sync(s2e: list, e2s: list, headword_index: dict,
                  sync_phonetic: bool = True) -> dict:
    """
    Link E2S subentries to S2E entries and optionally sync phonetic forms.

    Returns stats dict and populates changelog.
    """
    changelog = []
    stats = {
        "e2s_subentries_total": 0,
        "matched": 0,
        "unmatched_no_term": 0,
        "unmatched_no_s2e": 0,
        "phonetic_updated": 0,
        "phonetic_already_match": 0,
        "phonetic_s2e_empty": 0,
        "match_exact_unique": 0,
        "match_gloss_disambiguated": 0,
        "match_first_fallback": 0,
    }

    # Track which S2E entries got phonetic updates (prefer first match)
    s2e_phonetic_updated = set()

    for entry in e2s:
        english_word = entry.get("english_entry_word", "")

        for sub in entry.get("subentries", []):
            stats["e2s_subentries_total"] += 1

            pi = sub.get("part_I")
            if pi is None:
                stats["unmatched_no_term"] += 1
                sub["s2e_entry_id"] = None
                sub["s2e_match_type"] = "no_part_I"
                continue

            skiri_term = pi.get("skiri_term", "")
            if not skiri_term:
                stats["unmatched_no_term"] += 1
                sub["s2e_entry_id"] = None
                sub["s2e_match_type"] = "empty_skiri_term"
                continue

            # Get E2S glosses for disambiguation
            e2s_glosses = pi.get("english_glosses", [])

            # Match
            match = match_subentry_to_s2e(skiri_term, e2s_glosses,
                                           s2e, headword_index)

            if match is None:
                stats["unmatched_no_s2e"] += 1
                sub["s2e_entry_id"] = None
                sub["s2e_match_type"] = "no_s2e_match"

                changelog.append({
                    "action": "unmatched",
                    "english_word": english_word,
                    "skiri_term": skiri_term,
                })
                continue

            # Write the link
            sub["s2e_entry_id"] = match["entry_id"]
            sub["s2e_match_type"] = match["match_type"]
            stats["matched"] += 1
            stats[f"match_{match['match_type']}"] = stats.get(
                f"match_{match['match_type']}", 0) + 1

            # --- Sync phonetic form: E2S (accurate IPA) → S2E ---
            if sync_phonetic:
                s2e_idx = match["s2e_index"]
                e2s_phonetic = pi.get("phonetic_form", "")
                s2e_phonetic = s2e[s2e_idx].get("part_I", {}).get(
                    "phonetic_form", "")

                if not e2s_phonetic:
                    pass  # nothing to sync
                elif not s2e_phonetic:
                    # S2E has no phonetic — fill it in
                    s2e[s2e_idx].setdefault("part_I", {})["phonetic_form"] = e2s_phonetic
                    stats["phonetic_s2e_empty"] += 1
                    s2e_phonetic_updated.add(s2e_idx)
                    changelog.append({
                        "action": "phonetic_filled",
                        "entry_id": match["entry_id"],
                        "skiri_term": skiri_term,
                        "e2s_phonetic": e2s_phonetic,
                    })
                elif e2s_phonetic == s2e_phonetic:
                    stats["phonetic_already_match"] += 1
                elif s2e_idx not in s2e_phonetic_updated:
                    # Update S2E with E2S's more accurate IPA form
                    old = s2e_phonetic
                    s2e[s2e_idx]["part_I"]["phonetic_form"] = e2s_phonetic
                    stats["phonetic_updated"] += 1
                    s2e_phonetic_updated.add(s2e_idx)
                    changelog.append({
                        "action": "phonetic_updated",
                        "entry_id": match["entry_id"],
                        "skiri_term": skiri_term,
                        "english_word": english_word,
                        "old_s2e_phonetic": old,
                        "new_s2e_phonetic": e2s_phonetic,
                    })

    return stats, changelog


# ===========================================================================
#  REPORT
# ===========================================================================

def generate_report(stats: dict, changelog: list, s2e_count: int, e2s_count: int):
    """Generate markdown report."""
    unmatched = [c for c in changelog if c["action"] == "unmatched"]
    ph_updated = [c for c in changelog if c["action"] == "phonetic_updated"]
    ph_filled = [c for c in changelog if c["action"] == "phonetic_filled"]

    report = f"""# Dictionary Link Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Datasets

| Dataset | Entries |
|---------|---------|
| S2E | {s2e_count} |
| E2S | {e2s_count} |
| E2S subentries processed | {stats['e2s_subentries_total']} |

## Matching Results

| Metric | Count |
|--------|-------|
| Matched (linked) | {stats['matched']} |
| — exact unique headword | {stats.get('match_exact_unique', 0)} |
| — gloss-disambiguated | {stats.get('match_gloss_disambiguated', 0)} |
| — first homonym fallback | {stats.get('match_first_homonym_fallback', 0)} |
| Unmatched — no skiri_term | {stats['unmatched_no_term']} |
| Unmatched — no S2E match | {stats['unmatched_no_s2e']} |

## Phonetic Form Sync (E2S → S2E)

E2S phonetic forms are the authoritative IPA source.

| Metric | Count |
|--------|-------|
| S2E phonetic updated from E2S | {stats['phonetic_updated']} |
| S2E phonetic filled (was empty) | {stats['phonetic_s2e_empty']} |
| Already matching | {stats['phonetic_already_match']} |

## Unmatched E2S Terms (first 30)

These E2S subentries could not be linked to any S2E entry:

"""
    for item in unmatched[:30]:
        report += f"- `{item['skiri_term']}` (English: {item['english_word']})\n"
    if len(unmatched) > 30:
        report += f"\n... and {len(unmatched) - 30} more.\n"

    report += f"""
## Phonetic Form Updates (first 30)

| Skiri Term | Old S2E | New (from E2S) |
|------------|---------|----------------|
"""
    for item in ph_updated[:30]:
        report += f"| `{item['skiri_term']}` | `{item['old_s2e_phonetic']}` | `{item['new_s2e_phonetic']}` |\n"

    report += f"""
## Output Files

| File | Description |
|------|-------------|
| `{LINKED_S2E.name}` | S2E with entry_id + updated phonetic forms |
| `{LINKED_E2S.name}` | E2S with s2e_entry_id on each subentry |
| `{LINK_LOG.name}` | Full changelog |
"""
    return report


# ===========================================================================
#  FILE I/O
# ===========================================================================

def load_json(path: Path) -> list:
    if not path.exists():
        log.error(f"File not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        log.info(f"Loaded {len(data)} entries from {path.name}")
        return data
    return []


def save_json(data, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info(f"Saved → {path.name}")


# ===========================================================================
#  MAIN
# ===========================================================================

def run(dry_run=False, sync_phonetic=True):
    log.info("=" * 60)
    log.info("DICTIONARY LINKING + PHONETIC SYNC")
    log.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    log.info(f"Phonetic sync: {'ON' if sync_phonetic else 'OFF'}")
    log.info("=" * 60)

    s2e = load_json(S2E_JSON)
    e2s = load_json(E2S_JSON)

    if not s2e or not e2s:
        log.error("Could not load one or both dictionaries.")
        return

    # Step 1: assign IDs to S2E
    log.info("Step 1: Assigning entry IDs to S2E...")
    headword_index = assign_s2e_ids(s2e)

    # Step 2+3: match and sync
    log.info("Step 2: Matching E2S subentries to S2E entries...")
    stats, changelog = link_and_sync(s2e, e2s, headword_index,
                                      sync_phonetic=sync_phonetic)

    # Report
    log.info("")
    log.info("=" * 60)
    log.info(f"RESULTS {'(DRY RUN)' if dry_run else ''}")
    log.info("=" * 60)
    log.info(f"Matched:            {stats['matched']}")
    log.info(f"Unmatched (no term):{stats['unmatched_no_term']}")
    log.info(f"Unmatched (no S2E): {stats['unmatched_no_s2e']}")
    if sync_phonetic:
        log.info(f"Phonetic updated:   {stats['phonetic_updated']}")
        log.info(f"Phonetic filled:    {stats['phonetic_s2e_empty']}")
        log.info(f"Already matching:   {stats['phonetic_already_match']}")

    if not dry_run:
        save_json(s2e, LINKED_S2E)
        save_json(e2s, LINKED_E2S)
        save_json(changelog, LINK_LOG)

        report = generate_report(stats, changelog, len(s2e), len(e2s))
        with open(LINK_REPORT, "w", encoding="utf-8") as f:
            f.write(report)
        log.info(f"Report → {LINK_REPORT.name}")
    else:
        log.info("Dry run — no files written.")


def main():
    parser = argparse.ArgumentParser(
        description="Link S2E and E2S dictionaries with shared IDs, sync phonetic forms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
What this does:
  1. Assigns entry_id to every S2E entry (the primary record)
  2. Matches E2S subentries to S2E via skiri_term = headword
  3. Writes s2e_entry_id into E2S subentries
  4. Updates S2E phonetic_form with E2S's more accurate IPA transcription

Matching strategy for homonyms (same headword, different senses):
  - If unique match: high confidence
  - If multiple: disambiguate by gloss overlap → medium confidence
  - Fallback: first entry → low confidence (flagged for review)

Examples:
  python link_dictionaries.py                  # link + sync phonetic
  python link_dictionaries.py --dry-run        # preview
  python link_dictionaries.py --no-phonetic    # link only
        """
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without writing files")
    parser.add_argument("--no-phonetic", action="store_true",
                        help="Skip phonetic form sync (link only)")

    args = parser.parse_args()
    run(dry_run=args.dry_run, sync_phonetic=not args.no_phonetic)


if __name__ == "__main__":
    main()
