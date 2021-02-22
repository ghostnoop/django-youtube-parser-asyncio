# Generated by Django 3.1.1 on 2021-02-01 19:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(blank=True, default='', max_length=200)),
                ('channel_id', models.CharField(blank=True, default='', max_length=200)),
                ('parsed', models.BooleanField(default=False)),
            ],
            options={
                'unique_together': {('username', 'channel_id')},
            },
        ),
        migrations.CreateModel(
            name='YoutubeKey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=255, unique=True)),
                ('alive', models.BooleanField(default=True)),
                ('banned', models.CharField(default='', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Subscriber',
            fields=[
                ('subscriber_id', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('fullname', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('keywords', models.TextField()),
                ('country', models.CharField(max_length=200)),
                ('view_count', models.CharField(max_length=200)),
                ('subscriber_count', models.CharField(max_length=200)),
                ('video_count', models.CharField(max_length=200)),
                ('custom_url', models.CharField(max_length=200)),
                ('published_at', models.CharField(max_length=200)),
                ('channel_pk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parsing.channel')),
            ],
        ),
    ]
