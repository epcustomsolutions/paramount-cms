from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["first_name", "last_name", "phone", "email", "address", "notes"]
        labels = {
            "notes": "Notes",
        }
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("first_name", "last_name", "phone", "email"):
            w = self.fields[name].widget
            w.attrs.setdefault("class", "")
            w.attrs["class"] = (w.attrs["class"] + " form-control").strip()
        for name in ("address", "notes"):
            w = self.fields[name].widget
            w.attrs.setdefault("class", "")
            w.attrs["class"] = (w.attrs["class"] + " form-control").strip()

