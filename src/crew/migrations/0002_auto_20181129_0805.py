# Generated by Django 2.1.3 on 2018-11-29 08:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mis', '0001_initial'),
        ('crew', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='crewdairy',
            name='end_datetime',
        ),
        migrations.RemoveField(
            model_name='crewdairy',
            name='start_datetime',
        ),
        migrations.AddField(
            model_name='crewdairy',
            name='crew_slug',
            field=models.CharField(default='CR-2018-11-29-000000', max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='crewdairy',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='crewdairy',
            name='mis_id',
            field=models.ForeignKey(default=10, on_delete=django.db.models.deletion.CASCADE, to='mis.Mis'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='crewteam',
            name='crew_slug',
            field=models.CharField(default='CR-2018-11-29-000000', max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='crewteam',
            name='mis_id',
            field=models.ForeignKey(default=10, on_delete=django.db.models.deletion.CASCADE, to='mis.Mis'),
            preserve_default=False,
        ),
    ]
