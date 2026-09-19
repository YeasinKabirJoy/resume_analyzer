from django import forms
from .models import JobPosting, Position, Skill


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
                'placeholder': 'Enter position title',
            }),
        }


class SkillForm(forms.ModelForm):
    aliases = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
            'rows': 3,
            'placeholder': 'drf, django rest framework',
        }),
        help_text='Optional. Separate aliases with commas or new lines.',
    )

    class Meta:
        model = Skill
        fields = ['title', 'aliases']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
                'placeholder': 'Enter skill title',
            }),
        }


class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = ['position', 'title_override', 'department', 'location', 'required_experience', 'status']
        widgets = {
            'position': forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
            }),
            'title_override': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
                'placeholder': 'Optional job title override',
            }),
            'department': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
                'placeholder': 'Optional department',
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
                'placeholder': 'Optional location',
            }),
            'required_experience': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
            }),
        }
