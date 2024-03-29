# Generated by Django 2.2.2 on 2020-10-26 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LogInformation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('last_modified_time', models.DateTimeField(auto_now=True)),
                ('filename', models.CharField(max_length=200)),
                ('file_path', models.CharField(max_length=200)),
                ('file_size', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'log_information',
            },
        ),
    ]
