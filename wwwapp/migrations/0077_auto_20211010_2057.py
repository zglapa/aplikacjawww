# Generated by Django 3.1.13 on 2021-10-10 18:57

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wwwapp', '0076_newspost'),
    ]

    operations = [
        migrations.AddField(
            model_name='newspost',
            name='author',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='newspost',
            name='date_posted',
            field=models.DateTimeField(default=datetime.datetime(2021, 10, 10, 18, 57, 44, 642727, tzinfo=utc)),
        ),
    ]
