from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0010_resume_reason'),
    ]

    operations = [
        migrations.RenameField(
            model_name='jobrole',
            old_name='minimum_expreience',
            new_name='minimum_experience',
        ),
    ]
