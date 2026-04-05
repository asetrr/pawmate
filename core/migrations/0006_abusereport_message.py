import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_moderation_and_blocking'),
    ]

    operations = [
        migrations.AddField(
            model_name='abusereport',
            name='message',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='core.message'),
        ),
    ]
