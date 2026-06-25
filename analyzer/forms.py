from django import forms
from .models import JobRole, Skill


class JobRoleForm(forms.ModelForm):
    class Meta:
        model = JobRole
        fields = '__all__'

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
                'placeholder': 'Enter job title',
            }),
            'minimum_experience': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
            }),
            'version': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'rounded text-blue-600 bg-gray-800 border-gray-600 focus:ring-blue-500',
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

    def clean_aliases(self):
        raw_value = self.cleaned_data.get('aliases', '')
        if isinstance(raw_value, list):
            return raw_value

        aliases = []
        for chunk in str(raw_value).replace('\n', ',').split(','):
            alias = chunk.strip()
            if alias:
                aliases.append(alias)
        return aliases
