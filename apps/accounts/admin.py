from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Organisation, User


@admin.register(User)
class FindrUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Findr", {"fields": ("role", "phone", "organisation", "is_role_verified")}),)
    list_display = ("username", "email", "role", "organisation", "is_role_verified")
    list_filter = ("role", "is_role_verified")


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "county", "is_verified")
    list_filter = ("kind", "county", "is_verified")
    search_fields = ("name", "county")
