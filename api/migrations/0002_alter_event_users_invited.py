# Generated by Django 3.2.17 on 2023-03-09 18:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='users_invited',
            field=models.ManyToManyField(null=True, related_name='users_invited', to='api.User'),
        ),
    ]
