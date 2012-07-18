from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    # Examples:
    url(r'^ot/$', 'overtime.views.index', name='ot_idx'),
    url(r'^ot/new/$', 'overtime.views.new', name='ot_new'),
    url(r'^ot/(?P<id>\d+)/edit/$', 'overtime.views.edit', name='ot_edit'),
    url(r'^ot/(?P<id>\d+)/delete/$', 'overtime.views.delete', name='ot_delete'),

)
