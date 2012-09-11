#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import login, logout
from django.views.generic.simple import direct_to_template

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', direct_to_template, {'template':'index.html'}),
    # url(r'^hrms/', include('hrms.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^overtime/', include('overtime.urls')),
    url(r'^about/$', direct_to_template, {'template':'about.html'}),
    url(r'^accounts/login/$', login, {'template_name':'login.html'}, name='login'),
    url(r'^accounts/logout/$', logout, {'next_page':'/'}, name='logout'),
)

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
