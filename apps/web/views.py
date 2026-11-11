from datetime import date

from django.shortcuts import render

from apps.cases.models import Case

# Only cases a police station has acknowledged are listed publicly.
PUBLIC_STATUSES = ["active"]


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


def _tile(case):
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
    }


def home(request):
    cases = (Case.objects
             .filter(visibility=Case.Visibility.PUBLIC,
                     case_type=Case.Type.MISSING,
                     status__in=PUBLIC_STATUSES)
             .select_related("subject")
             .prefetch_related("media")[:6])
    return render(request, "home.html", {"tiles": [_tile(c) for c in cases]})


def _soon(request, title, text, milestone):
    return render(request, "coming_soon.html",
                  {"title": title, "text": text, "milestone": milestone})


def search(request):
    return _soon(request, "Search",
                 "Searching by name, nickname, age and county arrives in the next step.",
                 "M1b")


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
