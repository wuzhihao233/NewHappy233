# Generated by Django 4.1.3 on 2023-03-06 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pst', '0002_delete_rewardpoint'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='reward_points',
            field=models.IntegerField(blank=True),
        ),
    ]
