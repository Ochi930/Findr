from django.contrib import admin
from .models import UnidentifiedRecord

@admin.register(UnidentifiedRecord)
class RecordAdmin(admin.ModelAdmin):
    list_display = ("facility", "record_type", "status", "county", "created_at")
    list_filter = ("record_type", "status", "county")
