from django.conf.urls import patterns, include, url
from django.contrib import admin

import core.views

urlpatterns = [

    # Redirect or delete mail in queue:
    # /?id=06DA1A40B9B&action=redirect/delete
    url(r'^$', core.views.mailaction, name='mailaction'),

    # Django admin
    url(r'^admin/', admin.site.urls),

]
