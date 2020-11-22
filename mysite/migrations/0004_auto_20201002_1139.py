# Generated by Django 3.1.1 on 2020-10-02 06:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mysite', '0003_auto_20201001_1806'),
    ]

    operations = [
        migrations.AddField(
            model_name='lecture',
            name='lecture_slug',
            field=models.SlugField(default='-'),
        ),
        migrations.AlterField(
            model_name='lecture',
            name='course',
            field=models.ForeignKey(blank=True, default='', on_delete=django.db.models.deletion.CASCADE, to='mysite.course'),
            preserve_default=False,
        ),
    ]
