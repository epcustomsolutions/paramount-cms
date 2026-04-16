from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from .models import Client


def claims_panel_oob_response(request, client_pk: int) -> HttpResponse:
    """HTMX: refresh the client detail claims panel and signal the modal to close."""
    client = get_object_or_404(Client, pk=client_pk)
    claims = client.claims.all().order_by("-created_at")
    html = render_to_string(
        "clients/partials/client_claims_panel_oob.html",
        {"client": client, "claims": claims},
        request=request,
    )
    response = HttpResponse(html)
    response["HX-Reswap"] = "none"
    response["HX-Trigger"] = "closeClaimModal"
    return response
