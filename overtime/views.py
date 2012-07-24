#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.contrib.auth.models import User

from models import Application, ApplicationState, ApplicationFlow

class ApplicationForm(forms.ModelForm):
    subject = forms.CharField(label=u'标题')
    start_time = forms.CharField(label=u'开始时间')
    end_time = forms.CharField(label=u'结束时间')
    participants = forms.ModelMultipleChoiceField(label=u'参加人员', queryset=User.objects.all())
    content = forms.CharField(label=u'备注', widget=forms.Textarea())
    class Meta:
        model = Application
        fields  = ['subject', 'start_time', 'end_time', 'participants', 'content']

@login_required
def index(request):
    application_flows = request.user.applicationflow_set.all()
    ctx = {}
    ctx['application_flows'] = application_flows
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
        new_app_state = ApplicationState.objects.get(code='ReadyForDirectorApprove')
        app = appForm.instance
        app.state = new_app_state
        app.applicant = request.user
        
        if appForm.is_valid():
            appForm.save()
            
            # application flow for current user
            app_flow = ApplicationFlow()
            app_flow.application = app
            app_flow.applicant = app.applicant
            app_flow.set_applicant_state()
            app_flow.save()
            
            # application flow for participants
            for user in app.participants.all():
                app_flow = ApplicationFlow()
                app_flow.application = app
                app_flow.applicant = user
                app_flow.set_viewer_state()
                app_flow.save()
                
            # application flow for superior
            
            
            return HttpResponseRedirect(reverse('overtime'))
    return render(request, 'overtime/form.html', {'form': appForm})

@login_required
def edit(request, id):
    app = get_object_or_404(Application, id=id)
    appForm = ApplicationForm(instance=app)
    if request.method=='POST':
        appForm = ApplicationForm(request.POST, instance=app)
        if appForm.is_valid():
            appForm.save()
            return HttpResponseRedirect(reverse('overtime'))
    return render(request, 'overtime/form.html', {'form':appForm})

@login_required
def delete(request, id):
    app = get_object_or_404(Application, id=id)
    app.delete()
    return HttpResponseRedirect(reverse('overtime'))
    
@login_required
def approve(request, id):
    app = get_object_or_404(Application, id=id)
    app.approve(request.user)
    return HttpResponseRedirect(reverse('overtime'))

@login_required
def reject(request, id):
    app = get_object_or_404(Application, id=id)
    app.reject(request.user)
    return HttpResponseRedirect(reverse('overtime'))
    
@login_required
def revoke(request, id):
    app = get_object_or_404(Application, id=id)
    app.revoke(request.user)
    return HttpResponseRedirect(reverse('overtime'))

@login_required
def apply(request, id):
    app = get_object_or_404(Application, id=id)
    app.apply(request.user)
    return HttpResponseRedirect(reverse('overtime'))
