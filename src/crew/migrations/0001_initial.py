# Generated by Django 2.1.3 on 2018-11-28 08:36

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('mis', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Crew',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('crew_id', models.CharField(max_length=32, unique=True)),
                ('mis_crew_id', models.CharField(max_length=32)),
                ('mis_facility_id', models.CharField(max_length=16, null=True)),
                ('mis_car_id', models.CharField(max_length=16, null=True)),
                ('shift_start', models.DateTimeField()),
                ('shift_end', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('car_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mis.Cars')),
            ],
            options={
                'verbose_name': 'Crew',
                'verbose_name_plural': 'Crews',
            },
        ),
        migrations.CreateModel(
            name='CrewDairy',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('crew_dairy_seq', models.IntegerField(default=1)),
                ('start_datetime', models.DateTimeField(default=django.utils.timezone.now)),
                ('end_datetime', models.DateTimeField(null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('crew_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crew.Crew')),
            ],
        ),
        migrations.CreateModel(
            name='CrewRoute',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('route_seq', models.IntegerField(default=1)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('crew_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crew.Crew')),
            ],
        ),
        migrations.CreateModel(
            name='CrewSlug',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('date_modified', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='CrewStatus',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('crewstatus_name', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='CrewTeam',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('crew_team_seq', models.IntegerField(default=1)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('crew_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crew.Crew')),
                ('crew_staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mis.Staff')),
            ],
        ),
        migrations.AddField(
            model_name='crewroute',
            name='crew_status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crew.CrewStatus'),
        ),
        migrations.AddField(
            model_name='crewdairy',
            name='crew_status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crew.CrewStatus'),
        ),
        migrations.AddField(
            model_name='crew',
            name='crew_status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crew.CrewStatus'),
        ),
        migrations.AddField(
            model_name='crew',
            name='facility_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mis.Facility'),
        ),
        migrations.AddField(
            model_name='crew',
            name='mis_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mis.Mis'),
        ),
    ]
