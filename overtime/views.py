#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.contrib.auth.models import User, Group
from django.core.mail import EmailMessage
from django.template import loader, Context
from django.conf import settings
import datetime
from models import Application, ApplicationState, ApplicationFlow, UserProfile
import xlwt
import re
from django.utils.encoding import smart_str

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

    start_time, end_time, date_filter = get_filter(request)
    ctx['date_filter'] = date_filter
        
    if hrgroup in request.user.groups.all():
        # applications = Application.objects.all()
        applications = {
            'all': Application.objects.all(),
            'new': Application.objects.filter(state__in=[revoke_state, reject_state]),
            'applying': Application.objects.exclude(state__in=[revoke_state, reject_state, approved_state]),
            'approved': Application.objects.filter(state=approved_state),
        }[filter]
        applications = applications.filter(application_date__range=(start_time, end_time)).order_by('-modified_on')
        ctx['applications'] = applications
        ctx['is_hr'] = True
        ctx['filter'] = filter
        return myrender(request, 'overtime/index.html', ctx)
    else:
        application_flows = {
            'all': request.user.applicationflow_set.all(),
            'new': request.user.applicationflow_set.filter(application__state__in=[revoke_state, reject_state]),
            'applying': request.user.applicationflow_set.exclude(application__state__in=[revoke_state, reject_state, approved_state]),
            'approved': request.user.applicationflow_set.filter(application__state=approved_state),
        }[filter]
        application_flows = application_flows.filter(application__application_date__range=(start_time, end_time)).order_by('-application__modified_on')
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
def filter_date(request):
    request.session['date_filter'] = request.GET.get('quickDateRanges', '0')
    request.session['date_from'] = request.GET.get('date_from', '')
    request.session['date_to'] = request.GET.get('date_to', '')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

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
def overview(request):
    ctx = {}
    start_time, end_time, date_filter = get_filter(request)
    ctx['date_filter'] = date_filter
    approved_state = ApplicationState.objects.get(code='Approved')
    application_flows = request.user.applicationflow_set.filter(application__state=approved_state)
    application_flows = application_flows.filter(application__application_date__range=(start_time, end_time)).order_by('-application__modified_on')
    ctx['application_flows'] = application_flows
    return myrender(request, 'overtime/overview.html', ctx)
    
@login_required
def excel(request):
    start_time, end_time, date_filter = get_filter(request)
    approved_state = ApplicationState.objects.get(code='Approved')
    application_flows = request.user.applicationflow_set.filter(application__state=approved_state)
    application_flows = application_flows.filter(application__application_date__range=(start_time, end_time)).order_by('-application__modified_on')
    
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Sheet')

    ws.write(0, 0, u'基本信息')
    ws.write(1, 0, u'姓名')
    ws.write(1, 1, request.user.userprofile.chinese_name)
    ws.write(2, 0, u'部门')
    ws.write(3, 0, u'入职日期')
    ws.write(4, 0, u'已休年假天数')
    ws.write(5, 0, u'年假剩余天数')
    
    ws.write(7, 0, u'加班信息')
    ws.write(8, 1, u'标题')
    ws.write(8, 2, u'开始时间')
    ws.write(8, 3, u'结束时间')
    ws.write(8, 4, u'加班时间(小时)')
    
    i = 0
    for flow in application_flows:
        ws.write(9+i, 0, i+1)
        ws.write(9+i, 1, flow.application.subject)
        ws.write(9+i, 2, unicode(flow.application.start_time.strftime('%Y年%m月%d日 %H:%M'), 'utf-8'))
        ws.write(9+i, 3, unicode(flow.application.end_time.strftime('%Y年%m月%d日 %H:%M'), 'utf-8'))
        ws.write(9+i, 4, flow.application.total_time)
        i = i + 1

    fname = datetime.datetime.now().strftime('%Y%m%d.xls')
    response = HttpResponse(mimetype="application/x-download")
    response['Content-Disposition'] ='attachment; filename=%s' % smart_str(fname) #解决文件名乱码/不显示的问题
    wb.save(response)
    return response

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
    
def get_filter(request):
    start_time = ''
    end_time = ''
    date_filter = request.session.get('date_filter', '7')
    # date_filter = '1'
    if date_filter == '0':  # custom
        start_time = datetime.datetime.strptime(request.session.get('date_from', ''), '%Y-%m-%d')
        end_time = datetime.datetime.strptime(request.session.get('date_to', ''), '%Y-%m-%d')
        end_time = datetime.datetime(end_time.year, end_time.month, end_time.day, 23, 59, 59)
        date_filter = u'时间范围：' + request.session.get('date_from', '') + ' - ' + request.session.get('date_to', '')
    elif date_filter == '1':  # today
        now = datetime.datetime.now()
        start_time = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
        end_time = datetime.datetime(now.year, now.month, now.day, 23, 59, 59)
        date_filter = u'时间范围：' + datetime.datetime.strftime(now, '%Y-%m-%d')
    elif date_filter == '2':  # yestoday
        now = datetime.datetime.now()
        yestoday = now - datetime.timedelta(days=1)
        start_time = datetime.datetime(yestoday.year, yestoday.month, yestoday.day, 0, 0, 0)
        end_time = datetime.datetime(yestoday.year, yestoday.month, yestoday.day, 23, 59, 59)
        date_filter = u'时间范围：' + datetime.datetime.strftime(yestoday, '%Y-%m-%d')
    elif date_filter == '3':  # this week
        now = datetime.datetime.now()
        monday = now - datetime.timedelta(days=now.isoweekday()-1)
        sunday = monday + datetime.timedelta(days=6)
        start_time = datetime.datetime(monday.year, monday.month, monday.day, 0, 0, 0)
        end_time = datetime.datetime(sunday.year, sunday.month, sunday.day, 23, 59, 59)
        date_filter = u'时间范围：' + datetime.datetime.strftime(start_time, '%Y-%m-%d') + ' - ' + datetime.datetime.strftime(end_time, '%Y-%m-%d')
    elif date_filter == '4':  # last week
        now = datetime.datetime.now()
        last_monday = now - datetime.timedelta(days=now.isoweekday()-1+7)
        last_sunday = last_monday + datetime.timedelta(days=6)
        start_time = datetime.datetime(last_monday.year, last_monday.month, last_monday.day, 0, 0, 0)
        end_time = datetime.datetime(last_sunday.year, last_sunday.month, last_sunday.day, 23, 59, 59)
        date_filter = u'时间范围：' + datetime.datetime.strftime(start_time, '%Y-%m-%d') + ' - ' + datetime.datetime.strftime(end_time, '%Y-%m-%d')
    elif date_filter == '5':  # this month
        now = datetime.datetime.now()
        first_day_of_month = datetime.datetime(now.year, now.month, 1, 0, 0, 0)
        last_day_of_month = datetime.datetime(now.year, now.month+1, 1, 0, 0, 0) - datetime.timedelta(days=1)
        start_time = datetime.datetime(first_day_of_month.year, first_day_of_month.month, first_day_of_month.day, 0, 0, 0)
        end_time = datetime.datetime(last_day_of_month.year, last_day_of_month.month, last_day_of_month.day, 23, 59, 59)
        date_filter = first_day_of_month.strftime('时间范围：%Y年%m月')
    elif date_filter == '6':  # last month
        now = datetime.datetime.now()
        first_day_of_month = datetime.datetime(now.year, now.month-1, 1, 0, 0, 0)
        last_day_of_month = datetime.datetime(now.year, now.month, 1, 0, 0, 0) - datetime.timedelta(days=1)
        start_time = datetime.datetime(first_day_of_month.year, first_day_of_month.month, first_day_of_month.day, 0, 0, 0)
        end_time = datetime.datetime(last_day_of_month.year, last_day_of_month.month, last_day_of_month.day, 23, 59, 59)
        date_filter = first_day_of_month.strftime('时间范围：%Y年%m月')
    elif date_filter == '7':  # this year
        now = datetime.datetime.now()
        start_time = datetime.datetime(now.year, 1, 1, 0, 0, 0)
        end_time = datetime.datetime(now.year, 12, 31, 23, 59, 59)
        # date_filter = u'时间范围：' + u'%s年' % (now.year)
        date_filter = now.strftime('时间范围：%Y年')
    elif date_filter == '8':  # last year
        now = datetime.datetime.now()
        start_time = datetime.datetime(now.year-1, 1, 1, 0, 0, 0)
        end_time = datetime.datetime(now.year-1, 12, 31, 23, 59, 59)
        date_filter = u'时间范围：' + u'%d年' % (now.year-1)

    return (start_time, end_time, date_filter)