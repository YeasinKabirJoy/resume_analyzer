from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0011_rename_minimum_expreience_to_minimum_experience'),
    ]

    operations = [
        migrations.AddField(
            model_name='skill',
            name='aliases',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
