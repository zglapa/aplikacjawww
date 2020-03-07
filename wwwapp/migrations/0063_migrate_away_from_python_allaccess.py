# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-03-07 06:29
from __future__ import unicode_literals

from django.db import migrations
from allaccess.models import AccountAccess
from social_django.models import UserSocialAuth

# After the migration is applied in production just comment out code depending on the allaccess library
def forwards_func(apps, schema_editor):
    for access in AccountAccess.objects.all():
        if access.provider.name == 'facebook':
            UserSocialAuth(provider='facebook', uid=access.identifier, user=access.user, extra_data=access.access_token).save()
        elif access.provider.name == 'google':
            UserSocialAuth(provider='google-oauth2', uid=access.user.email, user=access.user, extra_data=access.access_token).save()

def reverse_func(apps, schema_editor):
    raise RuntimeError("Migration not reversible")

class Migration(migrations.Migration):

    dependencies = [
        ('wwwapp', '0062_auto_20200816_1023'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
        migrations.RunSQL('''
        drop table if exists allaccess_provider;
        drop table if exists allaccess_accountaccess;
        delete from auth_permission where content_type_id in (select id from django_content_type where app_label = '{app_label}');
        delete from django_admin_log where content_type_id in (select id from django_content_type where app_label = '{app_label}');
        delete from django_content_type where app_label = '{app_label}';
        delete from django_migrations where app='{app_label}';
        '''.format(app_label='allaccess'))
    ]
