from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Append-only record of who viewed or changed sensitive data.
    Required for any police or biometric use. Never edited or deleted in code."""

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                              on_delete=models.SET_NULL)
    action = models.CharField(max_length=60)       # e.g. "case.view_limited"
    object_type = models.CharField(max_length=60)
    object_id = models.CharField(max_length=40)
    detail = models.JSONField(default=dict, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("Audit log entries cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Audit log entries cannot be deleted.")
