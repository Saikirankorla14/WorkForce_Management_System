# Generated by Django 3.2.23 on 2024-02-23 10:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_scheduler'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheduler',
            name='end_date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='scheduler',
            name='start_date',
            field=models.DateField(),
        ),
    ]
