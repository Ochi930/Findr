from django.contrib.auth.models import AbstractUser
from django.db import models


class Organisation(models.Model):
    """A police station, DCI unit, hospital, mortuary or partner body."""

    class Kind(models.TextChoices):
        POLICE_STATION = "police_station", "Police station"
        DCI = "dci", "DCI unit"
        HOSPITAL = "hospital", "Hospital"
        MORTUARY = "mortuary", "Mortuary"
        NGO = "ngo", "Partner organisation"

    kind = models.CharField(max_length=20, choices=Kind.choices)
    name = models.CharField(max_length=200)
    county = models.CharField(max_length=60, blank=True)
    sub_county = models.CharField(max_length=60, blank=True)
    email = models.EmailField(help_text="Where new reports are sent.")
    phone = models.CharField(max_length=30, blank=True)
    # Only verified organisations may post official records. Verification is
    # a manual step by a platform admin (see docs/ROLES.md).
    is_verified = models.BooleanField(default=False)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="children",
        help_text="Escalation chain, e.g. station -> sub-county -> county.")

    class Meta:
        ordering = ["county", "name"]
        constraints = [models.UniqueConstraint(
            fields=["kind", "name", "county"], name="uniq_org")]

    def __str__(self):
        return f"{self.name} ({self.get_kind_display()})"


class User(AbstractUser):
    """Citizens register with email/phone. Staff accounts are created by admins.
    Anonymous tips need no account at all."""

    class Role(models.TextChoices):
        CITIZEN = "citizen", "Citizen"
        OFFICER = "officer", "Police officer"
        STATION_ADMIN = "station_admin", "Station administrator"
        SUPERVISOR = "supervisor", "County / regional supervisor"
        FACILITY_STAFF = "facility_staff", "Hospital or mortuary staff"
        MODERATOR = "moderator", "Moderator"
        PLATFORM_ADMIN = "platform_admin", "Platform administrator"

    role = models.CharField(max_length=20, choices=Role.choices,
                            default=Role.CITIZEN)
    phone = models.CharField(max_length=30, blank=True)
    organisation = models.ForeignKey(
        Organisation, null=True, blank=True, on_delete=models.PROTECT,
        related_name="members")
    # Staff roles only count once an admin has verified the person.
    is_role_verified = models.BooleanField(default=False)

    @property
    def is_police(self):
        return self.is_role_verified and self.role in {
            self.Role.OFFICER, self.Role.STATION_ADMIN, self.Role.SUPERVISOR}
