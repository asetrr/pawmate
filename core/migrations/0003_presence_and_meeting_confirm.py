import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_product_features'),
    ]

    operations = [
        migrations.AddField(
            model_name='userswipepreference',
            name='active_today',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='meetingplan',
            name='confirmed_by_owner',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='meetingplan',
            name='confirmed_by_user',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='notification',
            name='match',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='core.match'),
        ),
    ]
