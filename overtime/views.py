#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

from models import Application, ApplicationState, ApplicationFlow

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application

@login_required
def index(request):
    ctx = {}
    ctx['applications'] = Application.objects.all()
    return render(request, 'overtime/index.html', ctx)

@login_required    
def show(request, id):
    show_app = get_object_or_404(Application, id=id)
    current_flow = show_app.applicationflow_set.filter(applicant=request.user)[0]
    return render(request, 'overtime/show.html', {'app': show_app, 'current_flow': current_flow})

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
            
            app_flow = ApplicationFlow()
            app_flow.application = app
            app_flow.applicant = app.applicant
            app_flow.set_applicant_state()
            app_flow.save()
            
            return HttpResponseRedirect(reverse('overtime'))
    return render(request, 'overtime/form.html', {'form': appForm})

@login_required
def edit(request, id):
    edit_app = get_object_or_404(Application, id=id)
    appForm = ApplicationForm(instance=edit_app)
    if request.method=='POST':
        appForm = ApplicationForm(request.POST, instance=edit_app)
        if appForm.is_valid():
            appForm.save()
            return HttpResponseRedirect(reverse('overtime'))
    return render(request, 'overtime/form.html', {'form':appForm})

@login_required
def delete(request, id):
    del_app = get_object_or_404(Application, id=id)
    del_app.delete()
    return HttpResponseRedirect(reverse('overtime/overtime'))
    
@login_required
def approve(request, id):
    del_app = get_object_or_404(Application, id=id)
    del_app.approve(request.user)
    return HttpResponseRedirect(reverse('overtime/overtime'))

@login_required
def reject(request, id):
    del_app = get_object_or_404(Application, id=id)
    del_app.reject(request.user)
    return HttpResponseRedirect(reverse('overtime/overtime'))

@login_required
def apply(request, id):
    del_app = get_object_or_404(Application, id=id)
    del_app.apply(request.user)
    return HttpResponseRedirect(reverse('overtime/overtime'))
