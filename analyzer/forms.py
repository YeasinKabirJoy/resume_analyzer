from django import forms
from .models import JobRole


class JobRoleForm(forms.ModelForm):
    class Meta:
        model = JobRole
        fields = '__all__'

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
                'placeholder': 'Enter job title',
            }),
            'minimum_expreience': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
            }),
            'version': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 rounded bg-gray-900 text-white border border-gray-600',
            }),
            'active': forms.CheckboxInput(attrs={
                'class': 'rounded text-blue-600 bg-gray-800 border-gray-600 focus:ring-blue-500',
            }),
        }