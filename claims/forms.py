from django import forms

from .models import Claim, ClaimDocument


class ClaimForm(forms.ModelForm):
    class Meta:
        model = Claim
        fields = [
            "client",
            "claim_number",
            "status",
            "description",
            "insurance_company",
            "date_of_loss",
        ]
        widgets = {
            "date_of_loss": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client"].widget.attrs["class"] = "form-select"
        self.fields["client"].empty_label = ""
        self.fields["status"].widget.attrs["class"] = "form-select"
        for name in ("claim_number", "insurance_company"):
            w = self.fields[name].widget
            w.attrs.setdefault("class", "")
            w.attrs["class"] = (w.attrs["class"] + " form-control").strip()
        for name in ("date_of_loss", "description"):
            w = self.fields[name].widget
            w.attrs.setdefault("class", "")
            w.attrs["class"] = (w.attrs["class"] + " form-control").strip()

        # Claim number is always system-generated and read-only for users.
        if self.instance and self.instance.pk:
            generated_number = self.instance.claim_number
        else:
            generated_number = Claim.next_claim_number()
        self.fields["claim_number"].initial = generated_number
        self.fields["claim_number"].required = False
        self.fields["claim_number"].disabled = True
        self.fields["claim_number"].widget.attrs["readonly"] = "readonly"

    def save(self, commit=True):
        claim = super().save(commit=False)
        if not claim.pk:
            # Ignore client-side displayed value and generate server-side.
            claim.claim_number = ""
        if commit:
            claim.save()
        return claim


class ClaimNoteForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        label="Note",
    )


class ClaimDocumentForm(forms.Form):
    file = forms.FileField(label="Document")

    def clean_file(self):
        f = self.cleaned_data["file"]
        if f.size > ClaimDocument.MAX_FILE_SIZE:
            raise forms.ValidationError("File size must be 10 MB or less.")
        if f.content_type not in ClaimDocument.ALLOWED_CONTENT_TYPES:
            raise forms.ValidationError(
                "Only PDF, Word (.doc/.docx), and Excel (.xls/.xlsx) files are allowed."
            )
        return f
