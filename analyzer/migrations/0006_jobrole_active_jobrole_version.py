# Generated by Django 5.2.3 on 2025-06-20 20:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0005_alter_skillrequirements_options_resume_linkedin_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobrole',
            name='active',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AddField(
            model_name='jobrole',
            name='version',
            field=models.PositiveIntegerField(blank=True, default=1),
        ),
    ]
