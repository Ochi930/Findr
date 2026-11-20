from datetime import date

from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import redirect, render

from apps.cases.models import Case, Media, Subject

from . import search as finder
from .constants import COUNTIES
from .forms  import SKIN_SWATCHES, ReportForm

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


def tip(request):
    return _soon(request, "Send a tip",
                 "Anonymous tips need no account. This form is coming.",
                 "M1d")


def hospitals(request):
    return _soon(request, "Hospitals and mortuaries",
                 "Verified hospitals and mortuaries will be able to post here.",
                 "M3")

REPORT_LIMIT = 5

@transaction.atomic
def _save_report(d, user):
    age_From, age_to = d["age_from"], d["age_to"]
    subject = Subject.objects.create(
        kind=d["kind"],
        first_name=d["first_name"], middle_name=d["middle_name"],
        last_name=d["last_name"], other_names=d["other_names"],
        sex=d["sex"], 
        age_min=age_from, 
        age_max=age_to if age_to is not None else age_from,
        height_cm=d["height_cm"], 
        build=d["build"] or "unknown"
        skin_tone=int(d["skin_tone"]) if d["skin_tone"] else None,
        skin_tone_notes=d["skin_tone_notes"],
        hair=d["hair"], eyes=d["eyes"],
        distinguishing_marks=d["distinguishing_marks"],
        medical_needs=d["medical_needs"], 
        species=d["species"], breed=d["breed"],
        colour_markings=d["colour_markings"],
    )
    reporter = user if user.is_authenticated else None
    case = Case.objects.create(
        subject=subject,
        case_type=Case.Type.MISSING,
        status=Case.Status.SUBMITTED,
        source=Case.Source.CITIZEN,
        reporter=reporter,
        reporter_name=d["reporter_name"],
        reporter_phone=d["reporter_phone"],
        reporter_email=d["reporter_email"],
        relationship_to_subject=d["relationship"],
        last_seen_date=d["last_seen_date"],
        last_seen_place=d["last_seen_place"],
        county=d["county"],
        clothing_last_seen=d["clothing_last_seen"],
        circumstances=d["circumstances"],
    )
    for i, photo in enumerate(d["photos"]:
        Media.objects.create(
            case=case,
            kind=Media.Kind.LAST_SEEN if i == 0 else Media.Kind.PHOTO,
            file=photo, uploaded_by=reporter,
            consent_for_matching=d["consent_matching"])
    return case


def report(request):
    context = {"swatches": SKIN_SWATCHES}
    if request.method == "POST":
        key = f"report_count:{request.META.get('REMOTE_ADDR', '')}"
        count = cache.get(key, 0)
        form = ReportForm(request.POST, request.FILES)
        if count >= REPORT_LIMIT:
            context.update(form=form, limited=True)
            return render(request, "report.html", context, status=429)
        if form.is_valid():
            if form.cleaned_data["website"]:
                return redirect("home")
            case = _save_report(form.cleaned_data, request.user)
            cache.set(key, count + 1, 3600)
            request.session["last_report"] = case.reference
            return redirect("report_done")
    else:
        form = ReportForm()
    context["form"] = form
    return render(request, "report.html", context)

def report_done(request):
    reference = request.session.get("last_report")
    if not reference:
        return redirect("report")
    return render(request, "report_done.html", {"reference": reference})