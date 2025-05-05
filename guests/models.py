from django.db import models

class DetectionHistory(models.Model):
    TYPE_CHOICES = [
        ('image', 'Изображение'),
        ('video', 'Видео'),
        ('rtsp', 'RTSP-поток'),
    ]

    request_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    file_path = models.CharField(max_length=255, blank=True)
    guest_count = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_request_type_display()} — {self.guest_count} гостей — {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
