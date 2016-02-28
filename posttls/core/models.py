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


class TLSLogEntry(models.Model):
    """Log entries for handled mails (forwarded/deleted)"""

    queue_id = models.CharField('Queue ID', max_length=20)
    sender = models.CharField('Sender', max_length=255)
    recipients = models.CharField('Recipients', max_length=255, null=True)
    action = models.CharField('Action', max_length=100)
    date = models.DateTimeField('Date')

    def __str__(self):
        return self.queue_id


class MandatoryTLSDomains(models.Model):
    """For these domains the user shouln't be allowed to send emails unencrypted"""

    domain = models.CharField('Domain', max_length=100)

    def __str__(self):
        return self.domain