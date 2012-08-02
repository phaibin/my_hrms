#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.contrib.auth.models import User, Group
from django.core.mail import EmailMessage
from django.template import loader, Context
from django.conf import settings

from models import Application, ApplicationState, ApplicationFlow, UserProfile

char_field_errors = {
    'required': '必填字段'
}
datetime_field_errors = {
    'required': '必填字段',
    'invalid': '格式错误'
}

class ApplicationForm(forms.ModelForm):
    subject = forms.CharField(widget=forms.TextInput(), label=u'标题', error_messages=char_field_errors)
    start_time = forms.DateTimeField(label=u'开始时间', error_messages=datetime_field_errors)
    end_time = forms.DateTimeField(label=u'结束时间', error_messages=datetime_field_errors)
    participants = forms.ModelMultipleChoiceField(label=u'参加人员', queryset=UserProfile.objects.userprofile_in_employee_and_PM(), error_messages=char_field_errors)
    content = forms.CharField(label=u'备注', widget=forms.Textarea(), error_messages=char_field_errors)
    class Meta:
        model = Application
        fields  = ['subject', 'start_time', 'end_time', 'participants', 'content']

def myrender(request, *args, **kwargs):
    kwargs['current_app'] = 'overtime'
    return render(request, *args, **kwargs)

@login_required
def index(request, filter='all'):
    hrgroup = Group.objects.get(name='人事')
    ctx = {}
    # not applyed
    revoke_state = ApplicationState.objects.get(code='Revoke')
    reject_state = ApplicationState.objects.get(code='Reject')
    # approved
    approved_state = ApplicationState.objects.get(code='Approved')
    if hrgroup in request.user.groups.all():
        # applications = Application.objects.all()
        applications = {
            'all': Application.objects.all().order_by('-modified_on'),
            'new': Application.objects.filter(state__in=[revoke_state, reject_state]).order_by('-modified_on'),
            'applying': Application.objects.exclude(state__in=[revoke_state, reject_state, approved_state]).order_by('-modified_on'),
            'approved': Application.objects.filter(state=approved_state).order_by('-modified_on'),
        }[filter]
        ctx['applications'] = applications
        ctx['is_hr'] = True
        ctx['filter'] = filter
        return myrender(request, 'overtime/index.html', ctx)
    else:
        # application_flows = request.user.applicationflow_set.all()
        application_flows = {
            'all': request.user.applicationflow_set.all().order_by('-application__modified_on'),
            'new': request.user.applicationflow_set.filter(application__state__in=[revoke_state, reject_state]).order_by('-application__modified_on'),
            'applying': request.user.applicationflow_set.exclude(application__state__in=[revoke_state, reject_state, approved_state]).order_by('-application__modified_on'),
            'approved': request.user.applicationflow_set.filter(application__state=approved_state).order_by('-application__modified_on'),
        }[filter]
        ctx['application_flows'] = application_flows
        ctx['is_hr'] = False
        ctx['filter'] = filter
        return myrender(request, 'overtime/index.html', ctx)

@login_required
def filter_all(request):
    return index(request)

@login_required
def filter_new(request):
    return index(request, 'new')

@login_required
def filter_applying(request):
    return index(request, 'applying')

@login_required
def filter_approved(request):
    return index(request, 'approved')

@login_required    
def show(request, id):
    app = get_object_or_404(Application, id=id)
    return myrender(request, 'overtime/show.html', {'app': app})

@login_required
def new(request):
    appForm = ApplicationForm()
    if request.method == 'POST':
        appForm = ApplicationForm(request.POST)
        app = appForm.instance
        
        if appForm.is_valid():
            next_user = app.create(request.user, appForm.cleaned_data)
            
            # send email
            subject = '[my_hrms] 新加班申请'        
            _send_flow_email(request, app, subject, next_user)
            
            return HttpResponseRedirect(reverse('overtime'))
    return myrender(request, 'overtime/form.html', {'form': appForm})

@login_required
def edit(request, id):
    app = get_object_or_404(Application, id=id)
    app_flow = app.applicationflow_by_user(request.user)
    if app_flow is not None and app_flow.can_update:
        appForm = ApplicationForm(instance=app)
        if request.method == 'POST':
            appForm = ApplicationForm(request.POST, instance=app)
            if appForm.is_valid():
                new_app = appForm.save(commit=False)
                next_user = new_app.update(appForm.cleaned_data)
                
                # send email
                subject = '[my_hrms] 加班更新'        
                _send_flow_email(request, app, subject, next_user)
                
                return HttpResponseRedirect(reverse('overtime'))
        return myrender(request, 'overtime/form.html', {'form':appForm})
    else:
        return HttpResponseRedirect(reverse('overtime'))

@login_required
def delete(request, id):
    app = get_object_or_404(Application, id=id)
    app_flow = app.applicationflow_by_user(request.user)
    if app_flow is not None and app_flow.can_delete:
        app.delete()
        
        return HttpResponseRedirect(reverse('overtime'))
    else:
        return HttpResponseRedirect(reverse('overtime'))
    
@login_required
def approve(request, id):
    app = get_object_or_404(Application, id=id)
    app_flow = app.applicationflow_by_user(request.user)
    if app_flow is not None and app_flow.can_approve:
        next_user = app.approve(request.user)
        
        # send email
        subject = '[my_hrms] 加班通过'       
        _send_flow_email(request, app, subject, next_user)
        
        return HttpResponseRedirect(reverse('overtime'))
    else:
        return HttpResponseRedirect(reverse('overtime'))

@login_required
def reject(request, id):
    app = get_object_or_404(Application, id=id)
    app_flow = app.applicationflow_by_user(request.user)
    if app_flow is not None and app_flow.can_reject:
        next_user = app.reject(request.user)
        
        # send email
        subject = '[my_hrms] 加班拒绝'       
        _send_flow_email(request, app, subject, next_user)
        
        return HttpResponseRedirect(reverse('overtime'))
    else:
        return HttpResponseRedirect(reverse('overtime'))
    
@login_required
def revoke(request, id):
    app = get_object_or_404(Application, id=id)
    app_flow = app.applicationflow_by_user(request.user)
    if app_flow is not None and app_flow.can_revoke:
        next_user = app.revoke(request.user)
        
        # send email
        subject = '[my_hrms] 加班撤销'      
        _send_flow_email(request, app, subject, next_user)
        
        return HttpResponseRedirect(reverse('overtime'))
    else:
        return HttpResponseRedirect(reverse('overtime'))

@login_required
def apply(request, id):
    app = get_object_or_404(Application, id=id)
    app_flow = app.applicationflow_by_user(request.user)
    if app_flow is not None and app_flow.can_apply:
        next_user = app.apply(request.user)
        
        # send email
        subject = '[my_hrms] 新加班申请'        
        _send_flow_email(request, app, subject, next_user)
        
        return HttpResponseRedirect(reverse('overtime'))
    else:
        return HttpResponseRedirect(reverse('overtime'))

def _send_email(subject, mail_from, mail_to_list, template, context):
    if settings.SENDING_EMAIL:
        msg = EmailMessage(subject, loader.get_template(template).render(Context(context)), mail_from, mail_to_list)
        msg.content_subtype = 'html'
        msg.send()
    
def _send_flow_email(request, app, subject, next_user):
    mail_from = 'admin@my_hrms.com'
    mail_to_list = set([app.applicant.email])
    for participant in app.participants.all():
        mail_to_list.add(participant.email)
    if next_user is not None:
        mail_to_list.add(next_user.email)
    if '' in mail_to_list:
        mail_to_list.remove('')
    template = 'overtime/email.html'
    context = {'app': app, 'app_url': request.build_absolute_uri(reverse('show_overtime', args=[app.id]))}
    _send_email(subject, mail_from, list(mail_to_list), template, context)
