#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'overtime.views.index', name='overtime'),
    url(r'^(?P<id>\d+)/$', 'overtime.views.show', name='show_overtime'),
    url(r'^new/$', 'overtime.views.new', name='new_overtime'),
    url(r'^(?P<id>\d+)/edit/$', 'overtime.views.edit', name='edit_overtime'),
    url(r'^(?P<id>\d+)/delete/$', 'overtime.views.delete', name='delete_overtime'),
    url(r'^(?P<id>\d+)/approve/$', 'overtime.views.approve', name='approve_overtime'),
    url(r'^(?P<id>\d+)/reject/$', 'overtime.views.reject', name='reject_overtime'),
    url(r'^(?P<id>\d+)/apply/$', 'overtime.views.apply', name='apply_overtime'),
)
