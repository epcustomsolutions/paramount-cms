from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from claims.models import Claim
from clients.models import Client
from .models import Appointment


DATETIME_LOCAL_INPUT_FORMATS = [
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%dT%H:%M:%S",
]


class AppointmentForm(forms.ModelForm):
    start = forms.DateTimeField(
        input_formats=DATETIME_LOCAL_INPUT_FORMATS,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
    )
    end = forms.DateTimeField(
        input_formats=DATETIME_LOCAL_INPUT_FORMATS,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
    )

    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        required=False,
        empty_label="(No Client)",
        label="Client",
    )
    claim = forms.ModelChoiceField(
        queryset=Claim.objects.none(),
        required=False,
        empty_label="(No Claim)",
        label="Claim",
    )

    class Meta:
        model = Appointment
        fields = [
            "client",
            "claim",
            "start",
            "end",
            "status",
            "location",
            "reason",
            "internal_notes",
        ]
        widgets = {
            "location": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "reason": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "internal_notes": forms.Textarea(attrs={"rows": 6, "class": "form-control"}),
        }

    def clean_client(self):
        client = self.cleaned_data.get("client")
        if client is None:
            raise forms.ValidationError("Client is required.")
        return client

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["start"].widget.attrs.setdefault("class", "")
        self.fields["start"].widget.attrs["class"] = (
            (self.fields["start"].widget.attrs["class"] + " form-control").strip()
        )
        self.fields["end"].widget.attrs.setdefault("class", "")
        self.fields["end"].widget.attrs["class"] = (
            (self.fields["end"].widget.attrs["class"] + " form-control").strip()
        )
        self.fields["status"].widget.attrs["class"] = "form-select"

        self.fields["client"].widget.attrs.update(
            {
                "hx-get": "/schedule/claims/",
                "hx-trigger": "change",
                "hx-target": "#id_claim",
                "hx-swap": "outerHTML",
                "hx-include": "#id_claim",
                "class": "form-select",
            }
        )
        self.fields["claim"].widget.attrs["class"] = "form-select"

        client_id = (
            self.data.get("client")
            or self.initial.get("client")
            or getattr(self.instance, "client_id", None)
        )
        if client_id:
            self.fields["claim"].queryset = Claim.objects.filter(client_id=client_id).order_by("-created_at")
        else:
            self.fields["claim"].queryset = Claim.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start")
        end = cleaned_data.get("end")

        if start is None or end is None:
            return cleaned_data

        if timezone.is_naive(start):
            start = timezone.make_aware(start, timezone.get_current_timezone())
        if timezone.is_naive(end):
            end = timezone.make_aware(end, timezone.get_current_timezone())

        cutoff = timezone.make_aware(
            timezone.datetime.combine(
                start.date(),
                timezone.datetime.min.time().replace(hour=18, minute=0),
            ),
            timezone.get_current_timezone(),
        )

        def on_quarter_hour(dt):
            return (
                dt.second == 0
                and dt.microsecond == 0
                and (dt.minute % 15) == 0
            )

        if not on_quarter_hour(start):
            raise ValidationError({"start": "Start time must be in 15-minute increments."})
        if not on_quarter_hour(end):
            raise ValidationError({"end": "End time must be in 15-minute increments."})

        if start >= cutoff:
            raise ValidationError({"start": "Start time must be before 6:00pm."})
        if end > cutoff:
            raise ValidationError({"end": "End time must be 6:00pm or earlier."})

        return cleaned_data
