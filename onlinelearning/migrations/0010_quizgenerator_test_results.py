# Generated by Django 3.1.1 on 2020-12-05 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('onlinelearning', '0009_learningtextlearningnote'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizgenerator',
            name='test_results',
            field=models.TextField(default='null'),
        ),
    ]
