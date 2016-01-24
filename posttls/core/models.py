from django.db import models

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User Model
    see: Two Scoops of Django, page 258
    see: https://www.youtube.com/watch?v=0bAJV0zNWQw
    """
    pass


class TLSNotification(models.Model):
    """Log entries for notifications"""

    queue_id = models.CharField('Queue ID', max_length=20)
    notification = models.DateTimeField('Notification')  # Time of the last notification

    def __str__(self):
        return self.queue_id