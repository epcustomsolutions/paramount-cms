from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "email", "updated_at")
    search_fields = ("first_name", "last_name", "phone", "email", "notes")
    ordering = ("last_name", "first_name")
