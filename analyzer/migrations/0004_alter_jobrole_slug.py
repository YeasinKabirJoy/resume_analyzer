# Generated by Django 5.2.3 on 2025-06-14 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0003_rename_githubb_resume_github'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobrole',
            name='slug',
            field=models.SlugField(blank=True, max_length=60, unique=True),
        ),
    ]
