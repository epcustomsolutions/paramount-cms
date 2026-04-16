from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.db.models import Q
import json
from datetime import datetime

from .forms import AppointmentForm
from .models import Appointment
from claims.models import Claim


def _is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


@login_required
def calendar(request):
    q = request.GET.get("q", "").strip()
    return render(request, "scheduling/calendar.html", {"q": q})


@login_required
def appointment_events(request):
    start = request.GET.get("start")
    end = request.GET.get("end")
    q = request.GET.get("q", "").strip()

    start_dt = parse_datetime(start) if start else None
    end_dt = parse_datetime(end) if end else None

    qs = (
        Appointment.objects.select_related("client", "claim")
        .exclude(status="cancelled")
        .order_by("start")
    )

    if start_dt and end_dt:
        qs = qs.filter(start__lt=end_dt, end__gt=start_dt)

    if q:
        qs = qs.filter(
            Q(client__first_name__icontains=q)
            | Q(client__last_name__icontains=q)
            | Q(client__phone__icontains=q)
            | Q(claim__claim_number__icontains=q)
        )

    events = []
    for appt in qs:
        title = appt.client.full_name
        if appt.claim_id:
            title = f"{title} - {appt.claim.claim_number}"

        events.append(
            {
                "id": appt.id,
                "title": title,
                "start": appt.start.isoformat(),
                "end": appt.end.isoformat(),
                "url": reverse("scheduling:appointment-edit", args=[appt.id]),
            }
        )

    return JsonResponse(events, safe=False)


@login_required
def appointment_create(request):
    htmx = _is_htmx(request)

    def parse_local_datetime(val: str):
        raw = (val or "").strip()
        if not raw:
            return None
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            return None
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            if htmx:
                response = HttpResponse()
                response["HX-Trigger"] = "closeAppointmentModal, refetchCalendar"
                return response
            return redirect("scheduling:schedule")
    else:
        initial = {}
        start = parse_local_datetime(request.GET.get("start", ""))
        end = parse_local_datetime(request.GET.get("end", ""))
        if start:
            initial["start"] = start
        if end:
            initial["end"] = end
        form = AppointmentForm(initial=initial)

    if htmx:
        return render(
            request,
            "scheduling/partials/appointment_form_modal.html",
            {"form": form, "mode": "create", "post_url": reverse("scheduling:appointment-create")},
        )

    return render(request, "scheduling/appointment_form.html", {"form": form, "mode": "create"})


@login_required
def appointment_edit(request, pk: int):
    appt = get_object_or_404(Appointment, pk=pk)
    htmx = _is_htmx(request)

    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appt)
        if form.is_valid():
            form.save()
            if htmx:
                response = HttpResponse()
                response["HX-Trigger"] = "closeAppointmentModal, refetchCalendar"
                return response
            return redirect("scheduling:schedule")
    else:
        form = AppointmentForm(instance=appt)

    if htmx:
        return render(
            request,
            "scheduling/partials/appointment_form_modal.html",
            {
                "form": form,
                "mode": "edit",
                "appointment": appt,
                "post_url": reverse("scheduling:appointment-edit", args=[appt.pk]),
            },
        )

    return render(request, "scheduling/appointment_form.html", {"form": form, "mode": "edit", "appointment": appt})


@login_required
def appointment_delete(request, pk: int):
    appt = get_object_or_404(Appointment, pk=pk)
    htmx = _is_htmx(request)

    if request.method == "POST":
        appt.delete()
        if htmx:
            response = HttpResponse()
            response["HX-Trigger"] = "closeAppointmentModal, refetchCalendar"
            return response
        return redirect("scheduling:schedule")

    if htmx:
        return render(
            request,
            "scheduling/partials/appointment_delete_modal.html",
            {"appointment": appt},
        )

    return render(request, "scheduling/appointment_confirm_delete.html", {"appointment": appt})


@login_required
def appointment_reschedule(request, pk: int):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)

    appt = get_object_or_404(Appointment, pk=pk)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)

    def parse_local(val: str):
        raw = (val or "").strip()
        if not raw:
            return None
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            return None
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt

    start = parse_local(payload.get("start"))
    end = parse_local(payload.get("end"))
    if not start or not end:
        return JsonResponse({"ok": False, "error": "Start/end required."}, status=400)

    def on_quarter_hour(dt):
        return dt.second == 0 and dt.microsecond == 0 and (dt.minute % 15) == 0

    if not on_quarter_hour(start) or not on_quarter_hour(end):
        return JsonResponse(
            {"ok": False, "error": "Times must be in 15-minute increments."},
            status=400,
        )

    cutoff = timezone.make_aware(
        timezone.datetime.combine(
            start.date(),
            timezone.datetime.min.time().replace(hour=18, minute=0),
        ),
        timezone.get_current_timezone(),
    )
    if start >= cutoff:
        return JsonResponse({"ok": False, "error": "Start must be before 6:00pm."}, status=400)
    if end > cutoff:
        return JsonResponse({"ok": False, "error": "End must be 6:00pm or earlier."}, status=400)

    appt.start = start
    appt.end = end
    try:
        appt.full_clean()
        appt.save()
    except ValidationError as e:
        msg = getattr(e, "message_dict", None) or getattr(e, "error_dict", None)
        if isinstance(msg, dict) and msg:
            first = next(iter(msg.values()))
            if isinstance(first, (list, tuple)) and first:
                return JsonResponse({"ok": False, "error": str(first[0])}, status=400)
            return JsonResponse({"ok": False, "error": str(first)}, status=400)
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

    return JsonResponse({"ok": True})


@login_required
def claims_for_client(request):
    """
    HTMX endpoint: update the claim dropdown when the client changes.
    Expects `client` and optionally `claim` in the querystring.
    """
    client_id = request.GET.get("client")
    selected_claim_id = request.GET.get("claim")

    claims_qs = Claim.objects.none()
    if client_id:
        claims_qs = Claim.objects.filter(client_id=client_id).order_by("-created_at")

    return render(
        request,
        "scheduling/partials/claim_select.html",
        {"claims": claims_qs, "selected_claim_id": selected_claim_id},
    )
