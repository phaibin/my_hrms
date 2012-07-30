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

from models import Application, ApplicationState, ApplicationFlow, UserProfile

class ApplicationForm(forms.ModelForm):
    subject = forms.CharField(widget=forms.TextInput(), label=u'标题')
    start_time = forms.DateTimeField(label=u'开始时间')
    end_time = forms.CharField(label=u'结束时间')
    participants = forms.ModelMultipleChoiceField(label=u'参加人员', queryset=UserProfile.objects.userprofile_in_employee_and_PM())
    content = forms.CharField(label=u'备注', widget=forms.Textarea())
    class Meta:
        model = Application
        fields  = ['subject', 'start_time', 'end_time', 'participants', 'content']

@login_required
def index(request):
    hrgroup = Group.objects.get(name='人事')
    ctx = {}
    if hrgroup in request.user.groups.all():
        applications = Application.objects.all()
        ctx['applications'] = applications
        ctx['is_hr'] = True
        return render(request, 'overtime/index.html', ctx)
    else:
        application_flows = request.user.applicationflow_set.all()
        ctx['application_flows'] = application_flows
        ctx['is_hr'] = False
        return render(request, 'overtime/index.html', ctx)

@login_required    
def show(request, id):
    app = get_object_or_404(Application, id=id)
    return render(request, 'overtime/show.html', {'app': app})

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
    return render(request, 'overtime/form.html', {'form': appForm})

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
        return render(request, 'overtime/form.html', {'form':appForm})
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
