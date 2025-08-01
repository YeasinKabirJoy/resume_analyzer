# Generated by Django 5.2.3 on 2025-06-14 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0004_alter_jobrole_slug'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='skillrequirements',
            options={'ordering': ['job_role', 'skill'], 'verbose_name': 'Skill Requirement', 'verbose_name_plural': 'Skill Requirements'},
        ),
        migrations.AddField(
            model_name='resume',
            name='linkedin',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='resume',
            name='skills',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
