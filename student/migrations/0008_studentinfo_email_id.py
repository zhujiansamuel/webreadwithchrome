# Generated by Django 3.1.1 on 2020-11-04 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0007_auto_20201104_1238'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentinfo',
            name='email_id',
            field=models.EmailField(default='-', max_length=254),
        ),
    ]
