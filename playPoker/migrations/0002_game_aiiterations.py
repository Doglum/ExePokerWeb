# Generated by Django 3.1.6 on 2021-04-05 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('playPoker', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='aiIterations',
            field=models.IntegerField(default=0),
        ),
    ]
