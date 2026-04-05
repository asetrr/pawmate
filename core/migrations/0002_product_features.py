import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('match', 'Новый мэтч'), ('message', 'Новое сообщение'), ('meeting', 'План встречи')], max_length=16)),
                ('text', models.CharField(max_length=220)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='UserSwipePreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('species', models.CharField(blank=True, max_length=64)),
                ('city', models.CharField(blank=True, max_length=64)),
                ('min_age', models.PositiveSmallIntegerField(default=0)),
                ('max_age', models.PositiveSmallIntegerField(default=30)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='swipe_pref', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MeetingPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('place', models.CharField(blank=True, max_length=120)),
                ('starts_at', models.DateTimeField(blank=True, null=True)),
                ('note', models.CharField(blank=True, max_length=220)),
                ('status', models.CharField(choices=[('draft', 'Черновик'), ('proposed', 'Предложено'), ('confirmed', 'Подтверждено'), ('done', 'Завершено')], default='draft', max_length=16)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('match', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='meeting_plan', to='core.match')),
            ],
        ),
    ]
