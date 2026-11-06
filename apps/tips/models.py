import secrets

from django.db import models


def new_tip_code():
    return secrets.token_urlsafe(9)


class Tip(models.Model):
    """Anonymous or named tip. No account needed.
    We store a salted hash of the IP, never the raw address, for abuse control."""

    class Status(models.TextChoices):
        NEW = "new", "New (in moderation queue)"
        PASSED = "passed", "Passed to police"
        DISMISSED = "dismissed", "Dismissed"
        CONFIRMED = "confirmed", "Led to a result"

    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE,
                             related_name="tips")
    tip_code = models.CharField(
        max_length=20, unique=True, default=new_tip_code, editable=False,
        help_text="Shown once to the tipper so they can add follow-ups.")
    message = models.TextField()
    seen_at = models.DateTimeField(null=True, blank=True)
    seen_place = models.CharField(max_length=250, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6,
                                   null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6,
                                    null=True, blank=True)
    photo = models.ImageField(upload_to="tips/", blank=True)
    contact = models.CharField(
        max_length=120, blank=True,
        help_text="Optional. Visible to police only.")
    ip_hash = models.CharField(max_length=64, blank=True, editable=False)
    status = models.CharField(max_length=10, choices=Status.choices,
                              default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
