# Generated by Django 2.1.5 on 2019-03-22 19:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mis', '0002_mistype'),
        ('callcard', '0005_auto_20190209_1245'),
    ]

    operations = [
        migrations.CreateModel(
            name='CCIntercall',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('related_cc', models.SlugField(max_length=32, null=True)),
                ('mis_from', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mis_ccic_from', to='mis.Mis')),
                ('mis_to', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mis_ccic_to', to='mis.Mis')),
            ],
        ),
        migrations.AddField(
            model_name='callcard',
            name='intercall',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='callcard.CCIntercall'),
        ),
    ]
