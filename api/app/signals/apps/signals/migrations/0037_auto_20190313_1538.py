# Generated by Django 2.1.7 on 2019-03-13 14:38

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('signals', '0036_auto_20190313_1222'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SubCategory',
            new_name='Category',
        ),
        migrations.RenameField(
            model_name='categoryassignment',
            old_name='sub_category',
            new_name='category',
        ),

    ]
