# Generated by Django 2.1.7 on 2019-02-24 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trel', '0008_auto_20190224_1634'),
    ]

    operations = [
        migrations.AlterField(
            model_name='complaint',
            name='state',
            field=models.IntegerField(db_index=True, verbose_name='State'),
        ),
    ]