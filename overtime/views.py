#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.contrib.auth.models import User, Group

from models import Application, ApplicationState, ApplicationFlow

class ApplicationForm(forms.ModelForm):
    subject = forms.CharField(widget=forms.TextInput(), label=u'标题')
    start_time = forms.CharField(label=u'开始时间')
    end_time = forms.CharField(label=u'结束时间')
    participants = forms.ModelMultipleChoiceField(label=u'参加人员', queryset=User.objects.all())
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
    current_flow = app.applicationflow_set.filter(applicant=request.user)[0]
    return render(request, 'overtime/show.html', {'app': app, 'current_flow': current_flow})

@login_required
def new(request):
    appForm = ApplicationForm()
    if request.method == 'POST':
        appForm = ApplicationForm(request.POST)
        app = appForm.instance
        
        if appForm.is_valid():
            app.create(request.user, appForm.cleaned_data)
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
                new_app.update(appForm.cleaned_data)
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
        app.approve(request.user)
        return HttpResponseRedirect(reverse('overtime'))
    else:
        print request
        return HttpResponseRedirect(reverse('overtime'))

@login_required
def reject(request, id):
    app = get_object_or_404(Application, id=id)
    app_flow = app.applicationflow_by_user(request.user)
    if app_flow is not None and app_flow.can_reject:
        app.reject(request.user)
        return HttpResponseRedirect(reverse('overtime'))
    else:
        return HttpResponseRedirect(reverse('overtime'))
    
@login_required
def revoke(request, id):
    app = get_object_or_404(Application, id=id)
    app_flow = app.applicationflow_by_user(request.user)
    if app_flow is not None and app_flow.can_revoke:
        app.revoke(request.user)
        return HttpResponseRedirect(reverse('overtime'))
    else:
        return HttpResponseRedirect(reverse('overtime'))

@login_required
def apply(request, id):
    app = get_object_or_404(Application, id=id)
    app_flow = app.applicationflow_by_user(request.user)
    if app_flow is not None and app_flow.can_apply:
        app.apply(request.user)
        return HttpResponseRedirect(reverse('overtime'))
    else:
        return HttpResponseRedirect(reverse('overtime'))
