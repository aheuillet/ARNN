# Generated by Django 2.1.3 on 2019-03-19 12:46

from django.db import migrations

def populate_observables(apps, schema_editor):
    Observable = apps.get_model('ARNN', 'Observable')
    spectral_radius = Observable(name="Spectral Radius")
    NRMSE = Observable(name="Normalized Root-Mean-Squarred Error")
    spectral_radius.save()
    NRMSE.save()

class Migration(migrations.Migration):

    dependencies = [
        ('ARNN', '0011_auto_20190319_1337'),
    ]

    operations = [
        migrations.RunPython(populate_observables)
    ]
