from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0012_skill_aliases'),
    ]

    operations = [
        migrations.AddField(
            model_name='resume',
            name='educations',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='resume',
            name='confidence_score',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='resume',
            name='error_message',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='resume',
            name='processed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='resume',
            name='text_quality_score',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
