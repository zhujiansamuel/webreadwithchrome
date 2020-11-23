# Generated by Django 3.1.1 on 2020-11-23 13:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Learningtext',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('online_text', models.TextField()),
                ('online_text_url', models.TextField()),
                ('online_text_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('online_text_expand_contest', models.TextField(default='no online_text_expand_contest')),
                ('text_question', models.TextField(default='no text_question')),
                ('text_question_answer', models.TextField(default='no text_question_answer')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
