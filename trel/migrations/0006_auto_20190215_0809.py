# Generated by Django 2.1.7 on 2019-02-15 01:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trel', '0005_auto_20190214_2308'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='log',
            name='complaint',
        ),
        migrations.DeleteModel(
            name='Log',
        ),
    ]
