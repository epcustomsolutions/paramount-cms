from django.urls import path

from . import views

app_name = "claims"

urlpatterns = [
    path("", views.claim_list, name="claim-list"),
    path("<int:pk>/", views.claim_detail, name="claim-detail"),
    path("new/", views.claim_create, name="claim-create"),
    path("<int:pk>/edit/", views.claim_edit, name="claim-edit"),
    path("<int:pk>/delete/", views.claim_delete, name="claim-delete"),
    path("<int:pk>/notes/add/", views.claim_note_create, name="claim-note-create"),
    path("<int:pk>/documents/upload/", views.claim_document_upload, name="claim-document-upload"),
    path(
        "documents/<int:pk>/download/",
        views.claim_document_download,
        name="claim-document-download",
    ),
    path(
        "documents/<int:pk>/delete/",
        views.claim_document_delete,
        name="claim-document-delete",
    ),
]
