from django.conf import settings
from django.db import models


class UnidentifiedRecord(models.Model):
    """Posted by a verified hospital or mortuary for a person who has not been
    identified. Every descriptive field may be blank: post what you know."""

    class RecordType(models.TextChoices):
        PATIENT = "patient", "Patient (alive, unidentified)"
        DECEASED = "deceased", "Deceased (in mortuary)"

    class Status(models.TextChoices):
        OPEN = "open", "Unidentified"
        POSSIBLE_MATCH = "possible", "Possible match under review"
        IDENTIFIED = "identified", "Identified and family notified"
        CLOSED = "closed", "Closed"

    facility = models.ForeignKey("accounts.Organisation",
                                 on_delete=models.PROTECT,
                                 related_name="unidentified_records")
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                  on_delete=models.SET_NULL)
    record_type = models.CharField(max_length=10, choices=RecordType.choices)
    status = models.CharField(max_length=12, choices=Status.choices,
                              default=Status.OPEN)

    sex = models.CharField(max_length=1, blank=True)
    age_min = models.PositiveSmallIntegerField(null=True, blank=True)
    age_max = models.PositiveSmallIntegerField(null=True, blank=True)
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    build = models.CharField(max_length=10, blank=True)
    skin_tone = models.PositiveSmallIntegerField(null=True, blank=True)
    skin_tone_notes = models.CharField(max_length=200, blank=True)
    hair = models.CharField(max_length=120, blank=True)
    clothing = models.TextField(blank=True)
    distinguishing_marks = models.TextField(blank=True)
    belongings = models.TextField(blank=True)

    found_at_place = models.CharField(max_length=250, blank=True)
    county = models.CharField(max_length=60, blank=True, db_index=True)
    admitted_at = models.DateTimeField(null=True, blank=True)
    police_ob_number = models.CharField(max_length=60, blank=True)

    # Photos of deceased persons are NOT public. Released to verified police or
    # to a family member in person / after verification.
    photo = models.ImageField(upload_to="facility/", blank=True)
    photo_public = models.BooleanField(default=False)

    matched_case = models.ForeignKey("cases.Case", null=True, blank=True,
                                     on_delete=models.SET_NULL,
                                     related_name="facility_matches")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
