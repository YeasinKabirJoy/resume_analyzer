from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0013_resume_pipeline_metadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='resume',
            name='educations',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
