# Generated by Django 5.2 on 2025-05-03 20:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guests', '0004_remove_detectionhistory_result_count_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='detectionhistory',
            name='media_path',
        ),
        migrations.RemoveField(
            model_name='detectionhistory',
            name='media_type',
        ),
        migrations.AddField(
            model_name='detectionhistory',
            name='file_path',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='detectionhistory',
            name='request_type',
            field=models.CharField(choices=[('image', 'Изображение'), ('video', 'Видео'), ('rtsp', 'RTSP-поток')], default='image', max_length=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='detectionhistory',
            name='guest_count',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='detectionhistory',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
