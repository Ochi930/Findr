from django.contrib import admin

from .models import Case, CaseUpdate, Media, Subject


class UpdateInline(admin.TabularInline):
    model = CaseUpdate
    extra = 0


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("reference", "subject", "case_type", "status", "county",
                    "stale_level", "created_at")
    list_filter = ("case_type", "status", "source", "county", "stale_level")
    search_fields = ("reference", "subject__first_name", "subject__last_name",
                     "subject__other_names", "ob_number")
    inlines = [UpdateInline]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("full_name", "kind", "sex", "age_min", "age_max")
    search_fields = ("first_name", "middle_name", "last_name", "other_names")


admin.site.register(Media)
