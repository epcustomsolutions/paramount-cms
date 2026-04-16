from django.contrib import admin

from .models import Claim, ClaimDocument, ClaimNote


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ("claim_number", "client", "status", "insurance_company", "date_of_loss", "updated_at")
    search_fields = (
        "claim_number",
        "client__first_name",
        "client__last_name",
        "insurance_company",
        "description",
    )
    list_filter = ("status",)


@admin.register(ClaimNote)
class ClaimNoteAdmin(admin.ModelAdmin):
    list_display = ("claim", "created_by", "created_at")
    search_fields = ("claim__claim_number", "content")
    list_filter = ("created_at",)


@admin.register(ClaimDocument)
class ClaimDocumentAdmin(admin.ModelAdmin):
    list_display = ("filename", "claim", "uploaded_by", "file_size", "uploaded_at")
    search_fields = ("filename", "claim__claim_number")
    list_filter = ("uploaded_at",)
