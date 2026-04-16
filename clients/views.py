from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ClientForm
from .models import Client


def _is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


@login_required
def client_list(request):
    q = request.GET.get("q", "").strip()
    clients = Client.objects.all().order_by("last_name", "first_name")
    if q:
        clients = clients.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone__icontains=q)
        )

    return render(request, "clients/client_list.html", {"clients": clients, "q": q})


@login_required
def client_detail(request, pk: int):
    client = get_object_or_404(Client, pk=pk)
    return render(
        request,
        "clients/client_detail.html",
        {"client": client, "claims": client.claims.all().order_by("-created_at")},
    )


@login_required
def client_create(request):
    htmx = _is_htmx(request)
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            if htmx:
                response = HttpResponse()
                response["HX-Redirect"] = reverse("clients:client-detail", args=[client.pk])
                return response
            return redirect("clients:client-detail", pk=client.pk)
    else:
        form = ClientForm()

    if htmx:
        return render(
            request,
            "clients/partials/client_form_modal.html",
            {
                "form": form,
                "mode": "create",
                "post_url": reverse("clients:client-create"),
            },
        )
    return render(request, "clients/client_form.html", {"form": form, "mode": "create"})


def _client_edit_modal_context(form, client):
    return {
        "form": form,
        "mode": "edit",
        "client": client,
        "post_url": reverse("clients:client-edit", args=[client.pk]),
    }


@login_required
def client_edit(request, pk: int):
    client = get_object_or_404(Client, pk=pk)
    htmx = _is_htmx(request)

    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            if htmx:
                response = HttpResponse()
                response["HX-Redirect"] = reverse("clients:client-detail", args=[client.pk])
                return response
            return redirect("clients:client-detail", pk=client.pk)
        if htmx:
            return render(
                request,
                "clients/partials/client_form_modal.html",
                _client_edit_modal_context(form, client),
            )
    else:
        form = ClientForm(instance=client)

    if htmx:
        return render(
            request,
            "clients/partials/client_form_modal.html",
            _client_edit_modal_context(form, client),
        )

    return render(
        request,
        "clients/client_form.html",
        {"form": form, "mode": "edit", "client": client},
    )


@login_required
def client_delete(request, pk: int):
    client = get_object_or_404(Client, pk=pk)
    htmx = _is_htmx(request)

    if request.method == "POST":
        client.delete()
        if htmx:
            response = HttpResponse()
            response["HX-Redirect"] = reverse("clients:client-list")
            return response
        return redirect("clients:client-list")

    if htmx:
        return render(
            request,
            "clients/partials/client_delete_modal.html",
            {"client": client},
        )

    return render(request, "clients/client_confirm_delete.html", {"client": client})
