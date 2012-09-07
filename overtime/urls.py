#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'overtime.views.index', name='overtime'),
    url(r'^filter_all/$', 'overtime.views.filter_all', name='filter_all_overtime'),
    url(r'^filter_new/$', 'overtime.views.filter_new', name='filter_new_overtime'),
    url(r'^filter_applying/$', 'overtime.views.filter_applying', name='filter_applying_overtime'),
    url(r'^filter_approved/$', 'overtime.views.filter_approved', name='filter_approved_overtime'),
    url(r'^(?P<id>\d+)/$', 'overtime.views.show', name='show_overtime'),
    url(r'^new/$', 'overtime.views.new', name='new_overtime'),
    url(r'^overview/$', 'overtime.views.overview', name='overview_overtime'),
    url(r'^excel/$', 'overtime.views.excel', name='excel_overtime'),
    url(r'^(?P<id>\d+)/edit/$', 'overtime.views.edit', name='edit_overtime'),
    url(r'^(?P<id>\d+)/delete/$', 'overtime.views.delete', name='delete_overtime'),
    url(r'^(?P<id>\d+)/approve/$', 'overtime.views.approve', name='approve_overtime'),
    url(r'^(?P<id>\d+)/reject/$', 'overtime.views.reject', name='reject_overtime'),
    url(r'^(?P<id>\d+)/apply/$', 'overtime.views.apply', name='apply_overtime'),
    url(r'^(?P<id>\d+)/revoke/$', 'overtime.views.revoke', name='revoke_overtime'),
    url(r'^filter_date/$', 'overtime.views.filter_date', name='filter_date_overtime'),
)
