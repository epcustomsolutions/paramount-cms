from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from clients.htmx import claims_panel_oob_response
from clients.models import Client

from .forms import ClaimDocumentForm, ClaimForm, ClaimNoteForm
from .models import Claim, ClaimDocument, ClaimNote


def _is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


def _modal_create_context(form, *, lock_client: bool, client_for_display, source: str):
    post_url = reverse("claims:claim-create")
    if source:
        post_url = f"{post_url}?source={source}"
    return {
        "form": form,
        "mode": "create",
        "post_url": post_url,
        "show_client_select": not lock_client,
        "client_for_display": client_for_display,
    }


def _modal_edit_context(form, claim, *, source: str = ""):
    post_url = reverse("claims:claim-edit", args=[claim.pk])
    if source:
        post_url = f"{post_url}?source={source}"
    return {
        "form": form,
        "mode": "edit",
        "post_url": post_url,
        "show_client_select": False,
        "client_for_display": claim.client,
    }


@login_required
def claim_list(request):
    claims = Claim.objects.select_related("client").all().order_by("-created_at", "id")
    return render(request, "claims/claim_list.html", {"claims": claims})


@login_required
def claim_detail(request, pk: int):
    claim = get_object_or_404(Claim.objects.select_related("client"), pk=pk)
    notes = claim.notes.select_related("created_by").all()
    documents = claim.documents.select_related("uploaded_by").all()
    note_form = ClaimNoteForm()
    document_form = ClaimDocumentForm()

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "add_note":
            note_form = ClaimNoteForm(request.POST)
            if note_form.is_valid():
                ClaimNote.objects.create(
                    claim=claim,
                    content=note_form.cleaned_data["content"],
                    created_by=request.user,
                )
                return redirect("claims:claim-detail", pk=claim.pk)

    return render(
        request,
        "claims/claim_detail.html",
        {
            "claim": claim,
            "notes": notes,
            "documents": documents,
            "note_form": note_form,
            "document_form": document_form,
        },
    )


def _locked_client_from_post(request):
    raw = (request.POST.get("client") or "").strip()
    if raw.isdigit():
        cid = int(raw)
        return Client.objects.filter(pk=cid).first()
    return None


@login_required
def claim_create(request):
    htmx = _is_htmx(request)
    lock_client = False
    client_for_display = None
    source = (request.GET.get("source") or request.POST.get("source") or "").strip()

    if request.method == "POST":
        form = ClaimForm(request.POST)
        if form.is_valid():
            claim = form.save()
            if htmx:
                if source == "claims-list":
                    response = HttpResponse()
                    response["HX-Trigger"] = "closeClaimModal, refreshClaimsPage"
                    return response
                return claims_panel_oob_response(request, claim.client_id)
            return redirect("claims:claim-detail", pk=claim.pk)
        if htmx:
            locked = _locked_client_from_post(request)
            ctx = _modal_create_context(
                form,
                lock_client=locked is not None,
                client_for_display=locked,
                source=source,
            )
            return render(request, "claims/partials/claim_form_modal.html", ctx)
    else:
        initial = {}
        raw_client = request.GET.get("client", "").strip()
        if raw_client.isdigit():
            cid = int(raw_client)
            q = Client.objects.filter(pk=cid).first()
            if q:
                initial["client"] = cid
                client_for_display = q
                lock_client = True
        form = ClaimForm(initial=initial)

    if htmx:
        ctx = _modal_create_context(
            form,
            lock_client=lock_client,
            client_for_display=client_for_display,
            source=source,
        )
        return render(request, "claims/partials/claim_form_modal.html", ctx)

    return render(
        request,
        "claims/claim_form.html",
        {"form": form, "mode": "create"},
    )


@login_required
def claim_edit(request, pk: int):
    claim = get_object_or_404(Claim, pk=pk)
    htmx = _is_htmx(request)
    source = (request.GET.get("source") or request.POST.get("source") or "").strip()

    if request.method == "POST":
        form = ClaimForm(request.POST, instance=claim)
        if form.is_valid():
            form.save()
            if htmx:
                if source == "detail":
                    response = HttpResponse()
                    response["HX-Redirect"] = reverse("claims:claim-detail", args=[claim.pk])
                    return response
                return claims_panel_oob_response(request, claim.client_id)
            return redirect("claims:claim-detail", pk=claim.pk)
        if htmx:
            return render(
                request,
                "claims/partials/claim_form_modal.html",
                _modal_edit_context(form, claim, source=source),
            )
    else:
        form = ClaimForm(instance=claim)

    if htmx:
        return render(
            request,
            "claims/partials/claim_form_modal.html",
            _modal_edit_context(form, claim, source=source),
        )

    return render(
        request,
        "claims/claim_form.html",
        {"form": form, "mode": "edit", "claim": claim},
    )


@login_required
def claim_delete(request, pk: int):
    claim = get_object_or_404(Claim, pk=pk)
    client_pk = claim.client_id
    htmx = _is_htmx(request)
    source = (request.GET.get("source") or request.POST.get("source") or "").strip()

    if request.method == "POST":
        claim.delete()
        if htmx:
            if source == "detail":
                response = HttpResponse()
                response["HX-Redirect"] = reverse("clients:client-detail", args=[client_pk])
                return response
            return claims_panel_oob_response(request, client_pk)
        return redirect("clients:client-detail", pk=client_pk)

    if htmx:
        return render(
            request,
            "claims/partials/claim_delete_modal.html",
            {"claim": claim, "source": source},
        )

    return render(
        request,
        "claims/claim_confirm_delete.html",
        {"claim": claim, "client_pk": client_pk},
    )


@login_required
def claim_document_upload(request, pk: int):
    claim = get_object_or_404(Claim, pk=pk)

    if request.method == "POST":
        form = ClaimDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.cleaned_data["file"]
            ClaimDocument.objects.create(
                claim=claim,
                uploaded_by=request.user,
                filename=f.name,
                content_type=f.content_type,
                file_data=f.read(),
                file_size=f.size,
            )
            return redirect("claims:claim-detail", pk=claim.pk)
    else:
        form = ClaimDocumentForm()

    return redirect("claims:claim-detail", pk=claim.pk)


@login_required
def claim_document_download(request, pk: int):
    doc = get_object_or_404(ClaimDocument, pk=pk)
    response = HttpResponse(doc.file_data, content_type=doc.content_type)
    response["Content-Disposition"] = f'attachment; filename="{doc.filename}"'
    return response


@login_required
def claim_document_delete(request, pk: int):
    doc = get_object_or_404(ClaimDocument, pk=pk)
    claim_pk = doc.claim_id

    if request.method == "POST":
        doc.delete()
        return redirect("claims:claim-detail", pk=claim_pk)

    return redirect("claims:claim-detail", pk=claim_pk)
