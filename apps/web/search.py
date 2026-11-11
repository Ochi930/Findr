"""Name matching for Findr search. Pure Python, no database access, so it is
easy to test. It tolerates spelling mistakes, swapped name order, nicknames
and partial names. On Postgres (later) a trigram index can replace the
scoring step; the rules stay the same."""

import re
import unicodedata
from datetime import date
from difflib import SequenceMatcher

MIN_SCORE = 0.72      # average match needed for a result
MIN_TOKEN = 0.60      # every word typed must match something reasonably well


def normalise(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("'", "").replace("\u2019", "")
    return re.sub(r"[^a-z0-9\s-]", " ", text)


def tokenize(text):
    return [t for t in re.split(r"[\s-]+", normalise(text)) if t]


def sound_key(word):
    """Rough sound-alike key so Kamau/Kamaw, Cecilia/Sesilia, Zawadi/Sawadi
    compare as equal."""
    w = re.sub(r"ph", "f", word)
    w = re.sub(r"ck", "k", w)
    w = re.sub(r"c(?=[eiy])", "s", w)
    w = w.replace("c", "k").replace("q", "k").replace("z", "s").replace("y", "i")
    w = re.sub(r"(.)\1+", r"\1", w)
    return w


def token_score(query_token, candidate_token):
    if query_token == candidate_token:
        return 1.0
    if len(query_token) >= 3 and candidate_token.startswith(query_token):
        return 0.92
    best = SequenceMatcher(None, query_token, candidate_token).ratio()
    if sound_key(query_token) == sound_key(candidate_token):
        best = max(best, 0.9)
    return best


def name_score(query, candidate_tokens):
    """0 to 1. Word order does not matter. Each typed word is matched to its
    best partner among the person's names, nicknames and aliases."""
    q_tokens = tokenize(query)
    if not q_tokens or not candidate_tokens:
        return 0.0
    per_word = [max(token_score(q, c) for c in candidate_tokens)
                for q in q_tokens]
    if min(per_word) < MIN_TOKEN:
        return 0.0
    score = sum(per_word) / len(per_word)
    return score if score >= MIN_SCORE else 0.0


def subject_tokens(subject):
    parts = [subject.first_name, subject.middle_name, subject.last_name]
    parts += (subject.other_names or "").splitlines()
    if subject.kind == "pet":
        parts += [subject.species, subject.breed, subject.colour_markings]
    tokens = []
    for p in parts:
        tokens.extend(tokenize(p))
    return tokens


def age_range(subject, today=None):
    """(low, high) in years, or None when age is unknown."""
    today = today or date.today()
    if subject.date_of_birth:
        b = subject.date_of_birth
        yrs = today.year - b.year - ((today.month, today.day) < (b.month, b.day))
        return yrs, yrs
    if subject.age_min is not None or subject.age_max is not None:
        lo = subject.age_min if subject.age_min is not None else subject.age_max
        hi = subject.age_max if subject.age_max is not None else subject.age_min
        return lo, hi
    return None


def age_matches(subject, wanted_from, wanted_to):
    """Unknown ages are kept: hospitals and families often do not know."""
    if wanted_from is None and wanted_to is None:
        return True
    rng = age_range(subject)
    if rng is None:
        return True
    lo, hi = rng
    wf = wanted_from if wanted_from is not None else 0
    wt = wanted_to if wanted_to is not None else 130
    return lo <= wt and hi >= wf


REFERENCE_RE = re.compile(r"^fnd-\d{4}-[a-z0-9]{6}$")


def looks_like_reference(text):
    return bool(REFERENCE_RE.match((text or "").strip().lower()))
