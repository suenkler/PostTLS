from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, TLSNotification, TLSLogEntry


# Custom User Model
# see: Two Scoops of Django, page 258
# see: https://www.youtube.com/watch?v=0bAJV0zNWQw
@admin.register(User)
class UserAdmin(UserAdmin):
    pass


class TLSNotificationAdmin(admin.ModelAdmin):
    list_display = ('queue_id', 'notification')


class TLSLogEntryAdmin(admin.ModelAdmin):
    list_display = ('queue_id', 'sender', 'recipients', 'action', 'date')


admin.site.register(TLSNotification, TLSNotificationAdmin)
admin.site.register(TLSLogEntry, TLSLogEntryAdmin)

