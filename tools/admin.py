from django.contrib import admin

from .models import MileageEntry


@admin.register(MileageEntry)
class MileageEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "start_mileage", "end_mileage", "updated_at")
    search_fields = ("user__username", "user__email", "date")
    list_filter = ("date",)
