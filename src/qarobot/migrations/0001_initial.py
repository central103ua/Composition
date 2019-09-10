# Generated by Django 2.1.5 on 2019-03-02 20:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('mis', '0002_mistype'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyTest',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('is_active', models.BooleanField(default=False)),
                ('call_count', models.BooleanField(default=False)),
                ('call_complete', models.BooleanField(default=False)),
                ('er_no_crew', models.BooleanField(default=False)),
                ('er_with_arrival', models.BooleanField(default=False)),
                ('mis', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='mis.Mis')),
            ],
        ),
    ]
