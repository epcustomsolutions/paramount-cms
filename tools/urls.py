from django.urls import path

from . import views

app_name = "tools"

urlpatterns = [
    path("", views.tools_home, name="tools-home"),
    path("mileage/", views.mileage_tracker, name="mileage-tracker"),
]

