import secrets
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def new_reference():
    """Human-friendly, unguessable reference, e.g. FND-2026-K7P2QX."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I
    code = "".join(secrets.choice(alphabet) for _ in range(6))
    return f"FND-{date.today().year}-{code}"


class Subject(models.Model):
    """The person or animal being looked for, or who has been found.
    Almost every field is optional: hospitals and the public often know little."""

    class Kind(models.TextChoices):
        PERSON = "person", "Person"
        PET = "pet", "Pet"

    class Sex(models.TextChoices):
        FEMALE = "f", "Female"
        MALE = "m", "Male"
        OTHER = "o", "Other"
        UNKNOWN = "u", "Unknown"

    class Build(models.TextChoices):
        SLIM = "slim", "Slim"
        AVERAGE = "average", "Average"
        STOCKY = "stocky", "Stocky"
        LARGE = "large", "Large"
        UNKNOWN = "unknown", "Unknown"

    kind = models.CharField(max_length=10, choices=Kind.choices,
                            default=Kind.PERSON)

    # ---- Names matter: keep every part and every alias separately --------
    first_name = models.CharField(max_length=80, blank=True)
    middle_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80, blank=True)
    other_names = models.TextField(
        blank=True,
        help_text="Nicknames, vernacular/baptismal names, spelling variants. "
                  "One per line. All are searchable.")
    # For pets, first_name holds the pet's name.

    sex = models.CharField(max_length=1, choices=Sex.choices,
                           default=Sex.UNKNOWN)
    date_of_birth = models.DateField(null=True, blank=True)
    age_min = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Use min/max when exact age is unknown.")
    age_max = models.PositiveSmallIntegerField(null=True, blank=True)

    # ---- Physical description (needed later for appearance matching) -----
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    build = models.CharField(max_length=10, choices=Build.choices,
                             default=Build.UNKNOWN)
    skin_tone = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="1 (lightest) to 10 (darkest) on the on-screen swatch scale.")
    skin_tone_notes = models.CharField(max_length=200, blank=True)
    hair = models.CharField(max_length=120, blank=True)
    eyes = models.CharField(max_length=60, blank=True)
    distinguishing_marks = models.TextField(
        blank=True, help_text="Scars, tattoos, birthmarks, limp, glasses...")
    medical_needs = models.TextField(blank=True)
    languages = models.CharField(max_length=120, blank=True)
    walking_style = models.CharField(
        max_length=200, blank=True,
        help_text="Free text now; used as a hint for gait matching in M8.")

    # ---- Pets only --------------------------------------------------------
    species = models.CharField(max_length=40, blank=True)
    breed = models.CharField(max_length=80, blank=True)
    colour_markings = models.CharField(max_length=200, blank=True)
    microchip_no = models.CharField(max_length=40, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["kind", "sex"]),
        ]

    @property
    def full_name(self):
        return " ".join(p for p in (self.first_name, self.middle_name,
                                    self.last_name) if p) or "Unidentified"

    @property
    def is_child(self):
        if self.age_max is not None:
            return self.age_max < 18
        if self.date_of_birth:
            years = (date.today() - self.date_of_birth).days // 365
            return years < 18
        return False

    def __str__(self):
        return self.full_name


class Disaster(models.Model):
    """A named event after which people went missing (flood, landslide, fire,
    building collapse, attack, accident...). Created only by moderators or
    platform admins so the list stays trustworthy."""

    class Kind(models.TextChoices):
        FLOOD = "flood", "Flood"
        LANDSLIDE = "landslide", "Landslide"
        FIRE = "fire", "Fire"
        COLLAPSE = "collapse", "Building collapse"
        ACCIDENT = "accident", "Major accident"
        ATTACK = "attack", "Attack or violence"
        EPIDEMIC = "epidemic", "Epidemic"
        OTHER = "other", "Other"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    kind = models.CharField(max_length=12, choices=Kind.choices,
                            default=Kind.OTHER)
    started_on = models.DateField()
    ended_on = models.DateField(null=True, blank=True)
    counties = models.CharField(
        max_length=250, blank=True,
        help_text="Affected counties, separated by commas.")
    summary = models.TextField(blank=True)
    official_source = models.CharField(
        max_length=250, blank=True,
        help_text="Who confirmed the event, e.g. the county government or "
                  "National Disaster Operation Centre.")
    source_url = models.URLField(blank=True)
    is_public = models.BooleanField(
        default=False, help_text="Tick when the event is ready to be shown.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-started_on"]

    def __str__(self):
        return f"{self.name} ({self.started_on.year})"


class Case(models.Model):
    class Type(models.TextChoices):
        MISSING = "missing", "Missing"
        FOUND = "found", "Found (reported by the public)"
        WANTED = "wanted", "Wanted by police"

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        PENDING_REVIEW = "pending_review", "Awaiting police acknowledgement"
        ACTIVE = "active", "Active investigation"
        FOUND_SAFE = "found_safe", "Found safe"
        FOUND_DECEASED = "found_deceased", "Found deceased"
        CLOSED = "closed", "Closed"
        REJECTED = "rejected", "Rejected (duplicate or false)"

    class Source(models.TextChoices):
        CITIZEN = "citizen", "Citizen report"
        POLICE = "police", "Official police report"
        FACILITY = "facility", "Hospital or mortuary"

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public listing"
        LIMITED = "limited", "Limited (police and reporter only)"

    reference = models.CharField(max_length=20, unique=True,
                                 default=new_reference, editable=False)
    case_type = models.CharField(max_length=10, choices=Type.choices,
                                 default=Type.MISSING)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT,
                                related_name="cases")
    status = models.CharField(max_length=20, choices=Status.choices,
                              default=Status.SUBMITTED)
    source = models.CharField(max_length=10, choices=Source.choices,
                              default=Source.CITIZEN)
    visibility = models.CharField(max_length=10, choices=Visibility.choices,
                                  default=Visibility.PUBLIC)

    # Reporter (account optional; contact details are never shown publicly)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="reported_cases")
    reporter_name = models.CharField(max_length=120, blank=True)
    reporter_phone = models.CharField(max_length=30, blank=True)
    reporter_email = models.EmailField(blank=True)
    relationship_to_subject = models.CharField(max_length=80, blank=True)

    # Last seen
    last_seen_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Used to compute urgency. Never used to block a report.")
    last_seen_place = models.CharField(max_length=250, blank=True)
    county = models.CharField(max_length=60, blank=True, db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6,
                                   null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6,
                                    null=True, blank=True)
    clothing_last_seen = models.TextField(blank=True)
    circumstances = models.TextField(blank=True)

    # Disaster link: a person can be tagged to a disaster at any time, but they
    # only appear on that disaster's public page once police or the authority
    # has confirmed the person as missing after it.
    disaster = models.ForeignKey(
        Disaster, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="cases")
    disaster_confirmed = models.BooleanField(
        default=False,
        help_text="Confirmed missing after this disaster by police or an authority.")
    disaster_confirmed_at = models.DateTimeField(null=True, blank=True)

    # Police handling
    assigned_station = models.ForeignKey(
        "accounts.Organisation", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="cases")
    assigned_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="assigned_cases")
    ob_number = models.CharField("Occurrence Book number", max_length=60,
                                 blank=True)
    police_verified = models.BooleanField(default=False)

    # Stale-case tracking (the M2 job reads and writes these)
    created_at = models.DateTimeField(auto_now_add=True)
    last_police_update_at = models.DateTimeField(null=True, blank=True)
    stale_level = models.PositiveSmallIntegerField(
        default=0, help_text="0 ok, 1 reminder, 2 escalated, 3 senior escalation")
    stale_flagged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "case_type"]),
            models.Index(fields=["county", "status"]),
            models.Index(fields=["stale_level"]),
            models.Index(fields=["disaster", "disaster_confirmed"]),
        ]
        permissions = [
            ("post_wanted_notice", "Can post a wanted notice"),
            ("view_limited_case", "Can view limited-visibility cases"),
        ]

    def clean(self):
        if self.disaster_confirmed and not self.disaster_id:
            raise ValidationError("Choose a disaster before confirming.")
        if self.disaster_confirmed and not self.police_verified:
            raise ValidationError(
                "A disaster listing must be confirmed by police: tick "
                "'Police verified' first.")
        # Wanted notices are police-only and must carry an OB number.
        if self.case_type == self.Type.WANTED:
            if self.source != self.Source.POLICE or not self.ob_number:
                raise ValidationError(
                    "Wanted notices must come from police and include an OB number.")

    def __str__(self):
        return f"{self.reference} - {self.subject}"

    @property
    def hours_since_last_seen(self):
        if not self.last_seen_at:
            return None
        return int((timezone.now() - self.last_seen_at).total_seconds() // 3600)


class CaseUpdate(models.Model):
    """Timeline entry. Police updates reset the stale-case clock."""

    class Kind(models.TextChoices):
        ACKNOWLEDGED = "ack", "Acknowledged by station"
        PROGRESS = "progress", "Investigation update"
        TIP = "tip", "Tip received"
        STATUS = "status", "Status change"
        NOTE = "note", "Internal note"

    case = models.ForeignKey(Case, on_delete=models.CASCADE,
                             related_name="updates")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                               on_delete=models.SET_NULL)
    kind = models.CharField(max_length=10, choices=Kind.choices,
                            default=Kind.PROGRESS)
    note = models.TextField()
    is_public = models.BooleanField(
        default=False, help_text="Public updates are visible to the family.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


def media_path(instance, filename):
    return f"cases/{instance.case.reference}/{filename}"


class Media(models.Model):
    class Kind(models.TextChoices):
        PHOTO = "photo", "Photo"
        LAST_SEEN = "last_seen", "Last seen photo"
        VIDEO = "video", "Video"

    case = models.ForeignKey(Case, on_delete=models.CASCADE,
                             related_name="media")
    kind = models.CharField(max_length=10, choices=Kind.choices,
                            default=Kind.PHOTO)
    file = models.FileField(upload_to=media_path)
    caption = models.CharField(max_length=200, blank=True)
    taken_at = models.DateTimeField(null=True, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                    blank=True, on_delete=models.SET_NULL)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Face matching only ever runs on media with explicit consent (see DPIA).
    consent_for_matching = models.BooleanField(default=False)
