from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from claims.models import Claim, ClaimDocument, ClaimNote
from scheduling.models import Appointment

STALE_CLAIM_DAYS = 14


@login_required
def dashboard(request):
    now = timezone.now()
    today = timezone.localdate()
    tz = timezone.get_current_timezone()
    start_of_today = timezone.make_aware(datetime.combine(today, datetime.min.time()), tz)
    end_of_today = start_of_today + timedelta(days=1)
    start_of_month = timezone.make_aware(
        datetime.combine(today.replace(day=1), datetime.min.time()), tz
    )
    week_ago = now - timedelta(days=7)
    stale_cutoff = now - timedelta(days=STALE_CLAIM_DAYS)

    # KPI row
    counts_by_status = dict(
        Claim.objects.values_list("status").annotate(n=Count("id"))
    )
    open_count = counts_by_status.get(Claim.STATUS_OPEN, 0)
    under_review_count = counts_by_status.get(Claim.STATUS_UNDER_REVIEW, 0)
    closed_count = counts_by_status.get(Claim.STATUS_CLOSED, 0)
    denied_count = counts_by_status.get(Claim.STATUS_DENIED, 0)
    active_count = open_count + under_review_count

    new_this_month = Claim.objects.filter(created_at__gte=start_of_month).count()
    notes_this_week = ClaimNote.objects.filter(created_at__gte=week_ago).count()

    # Today's appointments
    todays_appointments = list(
        Appointment.objects.select_related("client", "claim")
        .filter(start__gte=start_of_today, start__lt=end_of_today)
        .exclude(status="cancelled")
        .order_by("start")[:10]
    )

    # Stale claims: open/under_review with no note, no document, and no claim edit
    # in the last STALE_CLAIM_DAYS.
    active_claims = (
        Claim.objects.select_related("client")
        .filter(status__in=[Claim.STATUS_OPEN, Claim.STATUS_UNDER_REVIEW])
        .annotate(
            last_note_at=Max("notes__created_at"),
            last_doc_at=Max("documents__uploaded_at"),
        )
    )
    stale_claims = []
    for claim in active_claims:
        activity_times = [
            t for t in (claim.updated_at, claim.last_note_at, claim.last_doc_at) if t
        ]
        last_activity = max(activity_times) if activity_times else claim.created_at
        if last_activity < stale_cutoff:
            claim.last_activity = last_activity
            stale_claims.append(claim)
    stale_claims.sort(key=lambda c: c.last_activity)
    stale_claims = stale_claims[:10]

    # Recent activity feed — merge last N of each event kind.
    recent_notes = ClaimNote.objects.select_related(
        "claim", "claim__client", "created_by"
    ).order_by("-created_at")[:5]
    recent_docs = ClaimDocument.objects.select_related(
        "claim", "claim__client", "uploaded_by"
    ).order_by("-uploaded_at")[:5]
    recent_claims = Claim.objects.select_related("client").order_by("-created_at")[:5]

    events = []
    for note in recent_notes:
        events.append({"kind": "note", "at": note.created_at, "obj": note})
    for doc in recent_docs:
        events.append({"kind": "document", "at": doc.uploaded_at, "obj": doc})
    for claim in recent_claims:
        events.append({"kind": "claim", "at": claim.created_at, "obj": claim})
    events.sort(key=lambda e: e["at"], reverse=True)
    recent_events = events[:10]

    status_total = open_count + under_review_count + closed_count + denied_count
    context = {
        "kpis": {
            "active": active_count,
            "open": open_count,
            "under_review": under_review_count,
            "new_this_month": new_this_month,
            "notes_this_week": notes_this_week,
        },
        "status_breakdown": {
            "labels": ["Open", "Under Review", "Closed", "Denied"],
            "values": [open_count, under_review_count, closed_count, denied_count],
        },
        "status_total": status_total,
        "todays_appointments": todays_appointments,
        "stale_claims": stale_claims,
        "stale_days": STALE_CLAIM_DAYS,
        "recent_events": recent_events,
    }
    return render(request, "core/dashboard.html", context)


def healthz(request):
    return JsonResponse({"status": "ok"})
