# Generated by Django 5.1.3 on 2024-11-16 15:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('family', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='family',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='family.familyinfo'),
        ),
    ]