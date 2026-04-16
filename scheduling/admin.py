from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("start", "end", "client", "claim", "status", "reason")
    list_filter = ("status",)
    search_fields = (
        "client__first_name",
        "client__last_name",
        "client__phone",
        "claim__claim_number",
        "reason",
    )
