"""The two spellings of a dictionary word, written into a page together.

A page shows the dictionary's own spelling (Parks's: aa, c, ʔ) unless the visitor has chosen the learner
spelling (â, č, ') with the switch at the top of every page. The choice is kept in the visitor's browser
(static/js/skiri.js, Skiri.spelling), so the server does not know it. A page therefore carries both
spellings, and a style rule shows one of them (static/css/pawnee-theme.css: .when-parks, .when-learner).

Used by the local app (web/app.py) and by the static build (scripts/build_static_site.py), so that both
write the same markup. The scripts of the pages do the same with Skiri.spell() and Skiri.spellOther().

Nothing here makes a form. The learner spelling is the entry's stored `normalized_form`: the dictionary's
headword respelt letter by letter (scripts/check_simplified_forms.py checks the rule). An entry without one
(a word found only in the textbook) has one spelling, and the switch does not change it.
"""
from __future__ import annotations

from markupsafe import Markup, escape


def _field(entry, name):
    """A value of an entry, whether it came as an object, a dict or a database row."""
    if hasattr(entry, name):
        return getattr(entry, name)
    try:
        return entry[name]
    except (KeyError, IndexError, TypeError):
        return None


def forms(entry) -> tuple:
    """(the dictionary's spelling, the learner spelling), the second None when the entry has none of its own."""
    parks = _field(entry, "headword") or ""
    learner = _field(entry, "normalized_form")
    return parks, (learner if learner and learner != parks else None)


def pair(when_parks, when_learner) -> Markup:
    """Two spans, one for each choice of the switch; the texts are escaped."""
    return Markup('<span class="when-parks">%s</span><span class="when-learner">%s</span>') % (when_parks, when_learner)


def primary_spelling(entry) -> Markup:
    """The word as a page shows it first: the dictionary's spelling, or the learner spelling when that is chosen."""
    parks, learner = forms(entry)
    return pair(parks, learner) if learner else escape(parks)


def secondary_spelling(entry):
    """The other spelling, shown small beside the first; None when the entry has only one."""
    parks, learner = forms(entry)
    return pair(learner, parks) if learner else None


def register(target) -> None:
    """Give the two filters to a Flask app or to a Jinja environment."""
    env = getattr(target, "jinja_env", target)
    env.filters["primary_spelling"] = primary_spelling
    env.filters["secondary_spelling"] = secondary_spelling
