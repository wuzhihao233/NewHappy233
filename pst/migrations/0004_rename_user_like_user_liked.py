# Generated by Django 4.1.3 on 2023-03-01 17:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pst', '0003_remove_post_likes_like'),
    ]

    operations = [
        migrations.RenameField(
            model_name='like',
            old_name='user',
            new_name='user_liked',
        ),
    ]
