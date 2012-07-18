from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'overtime.views.index', name='overtime'),
    url(r'^(?P<id>\d+)/$', 'overtime.views.show', name='show_overtime'),
    url(r'^new/$', 'overtime.views.new', name='new_overtime'),
    url(r'^(?P<id>\d+)/edit/$', 'overtime.views.edit', name='edit_overtime'),
    url(r'^(?P<id>\d+)/delete/$', 'overtime.views.delete', name='delete_overtime'),

)
