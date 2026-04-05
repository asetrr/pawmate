from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_presence_and_meeting_confirm'),
    ]

    operations = [
        migrations.AddField(
            model_name='pet',
            name='photo',
            field=models.ImageField(blank=True, upload_to='pets/'),
        ),
    ]
