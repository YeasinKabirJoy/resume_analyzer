from django.contrib import admin
from django import forms

from .models import JobPosting, Position, Resume, Skill, SkillRequirements


class SkillAdminForm(forms.ModelForm):
    aliases = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "drf, django rest framework"}),
        help_text="Enter aliases separated by commas or new lines.",
    )

    class Meta:
        model = Skill
        fields = "__all__"

    def clean_aliases(self):
        raw_value = self.cleaned_data.get("aliases", "")
        if isinstance(raw_value, list):
            return raw_value

        aliases = []
        for chunk in str(raw_value).replace("\n", ",").split(","):
            alias = chunk.strip()
            if alias:
                aliases.append(alias)
        return aliases


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    form = SkillAdminForm
    list_display = ("title", "aliases")
    search_fields = ("title",)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "updated_at")
    search_fields = ("title",)


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ("display_title", "position", "status", "department", "location", "created_at")
    list_filter = ("status", "position")
    search_fields = ("position__title", "title_override", "department", "location")


admin.site.register(SkillRequirements)
admin.site.register(Resume)
