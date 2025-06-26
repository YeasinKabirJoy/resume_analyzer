from rest_framework import serializers
from analyzer.models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['job_role','resume']