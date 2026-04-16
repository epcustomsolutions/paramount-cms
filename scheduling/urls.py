from django.urls import path

from . import views

app_name = "scheduling"

urlpatterns = [
    path("", views.calendar, name="schedule"),
    path("events/", views.appointment_events, name="appointment-events"),
    path("appointments/new/", views.appointment_create, name="appointment-create"),
    path("appointments/<int:pk>/edit/", views.appointment_edit, name="appointment-edit"),
    path("appointments/<int:pk>/delete/", views.appointment_delete, name="appointment-delete"),
    path(
        "appointments/<int:pk>/reschedule/",
        views.appointment_reschedule,
        name="appointment-reschedule",
    ),
    path("claims/", views.claims_for_client, name="claims-for-client"),
]
