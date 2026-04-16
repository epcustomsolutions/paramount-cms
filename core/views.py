from django.http import JsonResponse
from django.shortcuts import redirect


def app_home(request):
    return redirect("scheduling:schedule")


def healthz(request):
    return JsonResponse({"status": "ok"})
