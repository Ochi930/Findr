from datetime import date

from django.core.paginator import Paginator
from django.shortcuts import render

from apps.cases.models import Case

from . import search as finder
from .constants import COUNTIES

# Only cases a police station has acknowledged are listed publicly.
PUBLIC_STATUSES = ["active"]
# Search also shows people who were found safe, clearly marked as found.
SEARCH_STATUSES = ["active", "found_safe"]
TONES = ["tide", "deep", "sand"]


def _age_label(subject):
    if subject.kind == "pet":
        return subject.breed or subject.species
    if subject.date_of_birth:
        t, b = date.today(), subject.date_of_birth
        years = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
        return f"{years} years old"
    lo, hi = subject.age_min, subject.age_max
    if lo is not None and hi is not None:
        return f"{lo} years old" if lo == hi else f"{lo} to {hi} years old"
    return ""


def _tile(case, index=0):
    s = case.subject
    photo = next((m for m in case.media.all()
                  if m.kind in ("last_seen", "photo")), None)
    initials = ((s.first_name[:1] + s.last_name[:1]) or s.full_name[:1]).upper()
    return {
        "case": case,
        "name": s.full_name,
        "detail": _age_label(s),
        "photo": photo.file.url if photo else "",
        "initials": initials,
        "tone": TONES[index % 3],
        "found": case.status == Case.Status.FOUND_SAFE,
    }


def home(request):
    cases = (Case.objects
             .filter(visibility=Case.Visibility.PUBLIC,
                     case_type=Case.Type.MISSING,
                     status__in=PUBLIC_STATUSES)
             .select_related("subject")
             .prefetch_related("media")[:6])
    return render(request, "home.html", {"tiles": [_tile(c, i) for i, c in enumerate(cases)]})


def _soon(request, title, text, milestone):
    return render(request, "coming_soon.html",
                  {"title": title, "text": text, "milestone": milestone})


def _int(value):
    try:
        n = int(value)
        return n if 0 <= n <= 130 else None
    except (TypeError, ValueError):
        return None


def search(request):
    g = request.GET
    q = g.get("q", "").strip()[:100]
    kind = g.get("kind", "")
    sex = g.get("sex", "")
    county = g.get("county", "")
    status = g.get("status", "")
    age_from, age_to = _int(g.get("age_from")), _int(g.get("age_to"))
    searched = any([q, kind, sex, county, status,
                    age_from is not None, age_to is not None])

    qs = (Case.objects
          .filter(visibility=Case.Visibility.PUBLIC,
                  case_type=Case.Type.MISSING,
                  status__in=SEARCH_STATUSES)
          .select_related("subject").prefetch_related("media"))
    if kind in ("person", "pet"):
        qs = qs.filter(subject__kind=kind)
    if sex in ("f", "m", "o"):
        qs = qs.filter(subject__sex=sex)
    if county in COUNTIES:
        qs = qs.filter(county__iexact=county)
    if status == "missing":
        qs = qs.filter(status=Case.Status.ACTIVE)
    elif status == "found":
        qs = qs.filter(status=Case.Status.FOUND_SAFE)

    if q and finder.looks_like_reference(q):
        qs = qs.filter(reference__iexact=q)
        cases = list(qs[:50])
    else:
        # The database narrows the list; Python scores the names (see search.py).
        candidates = list(qs.order_by("-created_at")[:2000])
        candidates = [c for c in candidates
                      if finder.age_matches(c.subject, age_from, age_to)]
        if q:
            scored = []
            for c in candidates:
                score = finder.name_score(q, finder.subject_tokens(c.subject))
                if score:
                    scored.append((score, c))
            # Best match first; still-missing ahead of found at equal score.
            scored.sort(key=lambda x: (-round(x[0], 2),
                                       x[1].status != Case.Status.ACTIVE))
            cases = [c for _, c in scored]
        else:
            cases = candidates
            cases.sort(key=lambda c: c.status != Case.Status.ACTIVE)

    page = Paginator(cases, 12).get_page(g.get("page"))
    tiles = [_tile(c, i) for i, c in enumerate(page.object_list)]

    params = g.copy()
    params.pop("page", None)

    return render(request, "search.html", {
        "tiles": tiles, "page": page, "total": len(cases),
        "searched": searched, "counties": COUNTIES,
        "form": {"q": q, "kind": kind, "sex": sex, "county": county,
                 "status": status,
                 "age_from": "" if age_from is None else age_from,
                 "age_to": "" if age_to is None else age_to},
        "querystring": params.urlencode(),
    })


def report(request):
    return _soon(request, "Report someone missing",
                 "The report form, with photo upload and last-seen details, is coming.",
                 "M1c")


def tip(request):
    return _soon(request, "Send a tip",
                 "Anonymous tips need no account. This form is coming.",
                 "M1d")


def hospitals(request):
    return _soon(request, "Hospitals and mortuaries",
                 "Verified hospitals and mortuaries will be able to post here.",
                 "M3")
