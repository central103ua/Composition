# Generated by Django 2.1.3 on 2018-11-29 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crew', '0003_auto_20181129_0822'),
    ]

    operations = [
        migrations.AddField(
            model_name='crewdairy',
            name='call_card_id',
            field=models.CharField(max_length=32, null=True),
        ),
    ]
