# Generated by Django 2.1.5 on 2019-03-29 06:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('callcard', '0006_auto_20190322_1940'),
        ('mis', '0002_mistype'),
        ('heartbeat', '0003_auto_20190322_1940'),
    ]

    operations = [
        migrations.CreateModel(
            name='Intercall',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('related_cc', models.SlugField(max_length=32, null=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('callcard', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='intercall_cc', to='callcard.CallCard')),
                ('mis_from', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mis_ic_from', to='mis.Mis')),
                ('mis_to', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mis_ic_to', to='mis.Mis')),
            ],
        ),
        migrations.CreateModel(
            name='IntercallQ',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('Intercall', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='heartbeat.Intercall')),
            ],
        ),
        migrations.CreateModel(
            name='IntercallQSatus',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=32)),
            ],
            options={
                'verbose_name': 'Intercall Queue Status',
                'verbose_name_plural': 'Intercall Queue Statuses',
            },
        ),
        migrations.AddField(
            model_name='intercallq',
            name='status',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='heartbeat.IntercallQSatus'),
        ),
    ]