# Generated by Django 2.1.7 on 2019-05-08 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iotmp', '0004_auto_20190508_1032'),
    ]

    operations = [
        migrations.AddField(
            model_name='server',
            name='port',
            field=models.IntegerField(default=None),
        ),
    ]
