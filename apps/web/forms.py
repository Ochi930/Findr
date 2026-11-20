from datetime import datetime, time
from typing import Any

from django import forms
from django.conf import settings
from django.utils import timezone

from apps.cases.models import subjects

from .constants import COUNTIES

SKIN_COLOURS = [
    "#F6E3D4", "#EBCDB4", "DDB38F", "#C99A73", "#B58259"
    "#9C6B45", "#82533A", "#6A412E", "#523223", "#3B241A",
]
SKIN_SWATCHES = [{"value": str(i + 1), "colour": c}
                 for i, c in enumerate(SKIN_COLOURS)]

MAX_PHOTOS = 5

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleImageField(forms.ImageField):
    """Lets one field accept several photos. Each is checked by a pillow, so a
    renamed non-image file is rejected."""
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_clean(d, initial) for d in data]
        else:
            result = [single_clean(data, initial)]
        return [r for r in result if r]


class ReportForm(forms.Form):
    kind = forms. ChoiceField(
        label="Who is missing?",
        choices=[("person", "A person"), ("pet", "A pet")],
        widget=forms.RadioSelect, initial="person")

    #names
    first_name = forms.CharField(label="First name", max_length=80, required=False)
    middle_name = forms.CharField(label="Middle name", max_length=80, required=False)
    last_name = forms.CharField(label="Last name", max_length=80, required=False)
    other_names = forms.CharField(
        label="Nicknames and other spellings", required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="One per line. Include vernacular names and any spelling "
                    "someone might use. All of them are searchable.")

    #description
    sex = forms.ChoiceField(
        label="Sex", initial="u"
        choices=[("u", "Not Sure"), ("f", "Female"), ("m", "Male"), ("o", "Other")])
    age_from = forms.IntegerField(label="Age from", min_value=0, max_value=130,
                                   required=False)
    age_to = forms.IntegerField(
        label="Oldest it could be", min_value=0, max_value=130, required=False,
        help_text="Only if you are unsure of the age.")
    height_cm = forms.IntegerField(label="Height in cm", min_value=0, 
                                   max_value=250, required=False)
    build = forms.ChoiceField(label="Build", choices=Subject.Build.choices, 
                              initial="unknown", required=False)
    skin_tone = forms.ChoiceField(
        required=False, 
        choices=[("", "Not sure")] + [(s["value"], s["value"]) for s in SKIN_SWATCHES])
    skin_tone_notes = forms.CharField(
        label="Skin in your own words", max_length=200, required=False)
    hair = forms.ChoiceField(label="Hair", max_length=120, required=False)
    eyes = forms.CharField(label="Eyes", max_length=60, required=False)
    distinguishing_marks = forms.CharField(
        label="Scars, tattoos, birthmarks, limp, glasses", required=False,
        widget=forms.Textarea(attrs={"rows": 3}))
    medical_needs = forms.CharField(
        label="Medical needs or medication", required=False,
        widget=forms.Textarea(attrs={"rows": 2}))

    #pets only
    species = forms.CharField(label= "Kind of animal", max_length=40, required=False,
                              help_text="For example dog, cat, parrot.")
    breed = forms.CharField(label="Breed", max_length=80, required=False)
    colour_markings = forms.CharField(label="Colour and markings",
                                      max_length=200, required=False)

    #Last seen
    last_seen_date = forms.DateField(
        label="Date last seen", required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="A best guess is fine.")
    last_seen_time = forms.TimeField(
        label="Time last seen", required=False,
        widget=forms.TimeInput(attrs={"type": "time"}))
    last_seen_place = forms.CharField(label="Where were they last seen?",
                                      max_length=250)

    county = forms.ChoiceField(
        label="County", choices=[("", "Choose a county")] + [(c, c) for c in COUNTIES])
    clothing_last_seen = forms.CharField(
        label="What they were wearing", required=False,
        widget=forms.Textarea(attrs={"rows": 2}))
    circumstances = forms.CharField(
        label="What happened?", required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Anything that may help: who they were with, where they were going.")

    #Photos
    photos = MultipleImageField(
        label="Photos", required=False,
        widget=MultipleFileInput(attrs={"accept": "image/*"}),
        help_text=f"Up to {MAX_PHOTOS}. Put the clearest recent photo first.")
    consent_matching = forms.BooleanField(
        required=False,
        label="Police may use these photos to help identify this person or pet"
              "(for example by comparing with other photos). ")

    #Reporter
    reporter_name = forms.CharField(label="Your name", max_length=120)
    reporter_phone = forms.CharField(label="Phone number", max_length=30,
                                     required=False)
    reporter_email = forms.EmailField(label="Email", required=False)
    relationship = forms.CharField(
        label="Your relationship to them", max_length=80, required=False)

    agree_terms = forms.BooleanField(
        label="I believe this report is true and I understand it will be sent "
        "to the police.")

    #Spam trap : people never see this, bots fill it in.
    website = forms.CharField(required=False, label="Leave this empty",
                              widget=forms.TextInput(attrs={
                                  "tabindex": "autocomplete": "off"}))

    def clean_last_seen_date(self):
        d = self.cleaned_data.get("last_seen_date")
        if d and d > timezone.localdate():
            raise forms.ValidationError("The date cannot be in the future.")
        return d

    def clean_photos(self):
        photos = self.cleaned_data.get("photos") or []
        if len(photos) > MAX_PHOTOS:
            raise forms.ValidationError(f"Please upload at most {MAX_PHOTOS} photos.")
        limit = settings.FINDR_MAX_UPLOAD_MB * 1024 * 1024
        for p in photos:
            if p.size > limit:
                raise forms.ValidationError(
                    f"{p.name}" is larger than {settings.FINDR_MAX_UPLOAD_MB} MB.")
        return photos

    def clean(self):
        data = super().clean()

        if data.get("kind") == "person":
            if not any(data.get(k)) for k in ("first_name", "last_name", "other_names")):
                self.add_error("first_name",
                               "Give at least one name, even a nickname.")
        elif data.get("kind") == "pet":
            if not data.get("species"):
                self.add_error("species", "Say what kind of animal it is.")


        if not data.get("reporter_phone") and not data.get("reporter_email"):
            self.add_error("reporter_phone",
                           "Give a phone number or email so the police can reach you.")

        a, b = data.get("age_from"), data.get("age_to")
        if a is not None and b is not None and a > b:
            self.add_error("age_to", "This cannot be lower than the age.")

        #Combine date and time.
        data["last_seen_at"] = None
        d, t = data.get("last_seen_date"), data.get("last_seen_time")
        if d:
            when = timezone.make_aware(datetime.combine(d, t or time(0, 0)))
            if when > timezone.now():
                self.add_error("last_seen_time", "That time is in the future.")
            else:
                data["last_seen_at"] = when
        return data