import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.db.models import F
from django.db.models.expressions import OrderBy
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .models import MileageEntry


def _mileage_entries_payload(user):
    entries = (
        MileageEntry.objects.filter(user=user)
        .order_by(
            "-date",
            OrderBy(F("start_mileage"), descending=True, nulls_last=True),
            "-id",
        )
        .values("id", "date", "start_mileage", "end_mileage")
    )
    return [
        {
            "id": row["id"],
            "date": row["date"].isoformat() if row["date"] else "",
            "start_mileage": row["start_mileage"],
            "end_mileage": row["end_mileage"],
        }
        for row in entries
    ]


@login_required
def tools_home(request):
    return render(request, "tools/tools_home.html")


@ensure_csrf_cookie
@login_required
@require_http_methods(["GET", "POST"])
def mileage_tracker(request):
    if request.method == "GET":
        return render(
            request,
            "tools/mileage_tracker.html",
            {
                "entries_payload": _mileage_entries_payload(request.user),
                "today": timezone.localdate(),
            },
        )

    # POST: JSON save
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponseBadRequest("Invalid JSON")

    entries_in = body.get("entries")
    deleted_ids = body.get("deleted_ids") or []
    if entries_in is None:
        return HttpResponseBadRequest("Missing entries")
    if not isinstance(entries_in, list):
        return HttpResponseBadRequest("entries must be a list")
    if not isinstance(deleted_ids, list):
        return HttpResponseBadRequest("deleted_ids must be a list")

    user = request.user
    errors = []

    if deleted_ids:
        try:
            deleted_ids = list({int(x) for x in deleted_ids})
        except (TypeError, ValueError):
            return HttpResponseBadRequest("Invalid deleted_ids")
        if MileageEntry.objects.filter(user=user, id__in=deleted_ids).count() != len(deleted_ids):
            return HttpResponseBadRequest("Invalid deleted_ids")

    parsed_rows = []
    for idx, row in enumerate(entries_in):
        if not isinstance(row, dict):
            errors.append({"index": idx, "message": "Row must be an object"})
            continue
        row_id = row.get("id")
        if row_id is not None and row_id != "":
            try:
                row_id = int(row_id)
            except (TypeError, ValueError):
                errors.append({"index": idx, "message": "Invalid id"})
                continue
        else:
            row_id = None

        date_str = row.get("date")
        if not date_str:
            errors.append({"index": idx, "message": "Date is required"})
            continue
        try:
            from datetime import datetime

            if isinstance(date_str, str):
                date_val = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
            else:
                errors.append({"index": idx, "message": "Invalid date"})
                continue
        except ValueError:
            errors.append({"index": idx, "message": "Invalid date format"})
            continue

        def parse_int(v):
            if v is None or v == "":
                return None
            try:
                n = int(v)
            except (TypeError, ValueError):
                raise ValueError("invalid int")
            if n < 0:
                raise ValueError("negative")
            return n

        try:
            start_m = parse_int(row.get("start_mileage"))
            end_m = parse_int(row.get("end_mileage"))
        except ValueError:
            errors.append(
                {"index": idx, "message": "Start and end must be non-negative whole numbers"}
            )
            continue

        parsed_rows.append(
            {
                "index": idx,
                "id": row_id,
                "date": date_val,
                "start_mileage": start_m,
                "end_mileage": end_m,
            }
        )

    if errors:
        return JsonResponse({"ok": False, "errors": errors}, status=400)

    try:
        with transaction.atomic():
            if deleted_ids:
                MileageEntry.objects.filter(user=user, id__in=deleted_ids).delete()

            now = timezone.now()
            for pr in parsed_rows:
                row_id = pr["id"]
                if row_id is not None:
                    entry = MileageEntry.objects.select_for_update().filter(user=user, id=row_id).first()
                    if entry is None:
                        raise ValidationError(["Entry not found or access denied."])
                else:
                    entry = MileageEntry(user=user)

                prev_start = entry.start_mileage if entry.pk else None
                prev_end = entry.end_mileage if entry.pk else None

                entry.date = pr["date"]
                entry.start_mileage = pr["start_mileage"]
                entry.end_mileage = pr["end_mileage"]

                if entry.start_mileage is not None and prev_start is None:
                    entry.start_recorded_at = now
                if entry.end_mileage is not None and prev_end is None:
                    entry.end_recorded_at = now

                entry.full_clean()
                entry.save()

    except ValidationError as e:
        msgs = []
        err_dict = getattr(e, "message_dict", None) or getattr(e, "error_dict", None)
        if err_dict:
            for field, errs in err_dict.items():
                for err in errs:
                    msgs.append({"message": f"{field}: {err}"})
        else:
            for m in getattr(e, "messages", [str(e)]):
                msgs.append({"message": m})
        return JsonResponse({"ok": False, "errors": msgs}, status=400)

    messages.success(request, "Mileage saved.")
    return JsonResponse(
        {
            "ok": True,
            "entries": _mileage_entries_payload(user),
        }
    )
