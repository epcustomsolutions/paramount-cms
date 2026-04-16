from django.urls import path

from . import views

app_name = "clients"

urlpatterns = [
    path("", views.client_list, name="client-list"),
    path("<int:pk>/", views.client_detail, name="client-detail"),
    path("new/", views.client_create, name="client-create"),
    path("<int:pk>/edit/", views.client_edit, name="client-edit"),
    path("<int:pk>/delete/", views.client_delete, name="client-delete"),
]

