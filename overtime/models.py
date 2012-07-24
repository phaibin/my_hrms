#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from datetime import datetime

class UserProfile(models.Model):
    # This field is required.
    user = models.OneToOneField(User)

    # Other fields here
    superior = models.ForeignKey(User, null=True, related_name='subordinates')        

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        
post_save.connect(create_user_profile, sender=User)

class ApplicationState(models.Model):
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name
                
class Application(models.Model):
    subject = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    application_date = models.DateTimeField(auto_now_add=True)
    participants = models.ManyToManyField(User, null=True)
    state = models.ForeignKey(ApplicationState, editable=False, null=True)
    applicant = models.ForeignKey(User, related_name='applied_applications', editable=False)
    content = models.TextField()

    @property
    def participants_string(self):
        return ', '.join([person.username for person in self.participants.all()])
        
    @property
    def state_string(self):
        return ', '.join([person.username for person in self.participants.all()])
        
    def applicationflow_by_user(self, user):
        return self.applicationflow_set.filter(applicant=user)[0]
        
    def approve(self, user):
        current_flow = ApplicationFlow.objects.get(application=self, applicant=user)
        pass
        
    def reject(self, user):
        pass
        
    def apply(self, user):
         pass
         
    def revoke(self, user):
         flow = self.applicationflow_by_user(user)
         flow.set_revoke_state()
         flow.save()
 
    def __unicode__(self):
        return self.subject
        
class ApplicationFlow(models.Model):
    application = models.ForeignKey(Application)
    applicant = models.ForeignKey(User)
    parent = models.ForeignKey('self', null=True)
    #permissions
    can_read = models.BooleanField()    # 列表
    can_update = models.BooleanField()  # 修改
    can_delete = models.BooleanField()  # 删除
    can_apply = models.BooleanField()   # 提交
    can_revoke = models.BooleanField() # 撤销
    can_reject = models.BooleanField()  # 拒绝
    can_approve = models.BooleanField() # 通过
    
    # 申请人    
    def set_applicant_state(self):
        self.reset_state()
        self.can_read = True
        self.can_revoke = True
        
    # 申请人撤销
    def set_revoke_state(self):
        self.reset_state()
        self.can_update = True
        self.can_delete = True
        self.can_apply = True
    
    # 参加人
    def set_viewer_state(self):
        self.reset_state()
        self.can_read = True
     
    # 批准过的人
    def set_hidden_state(self):
        self.reset_state()

    # 审核人
    def set_reviewer_state(self):
        self.reset_state()
        self.can_read = True
        self.can_reject = True
        self.can_approve = True
        
    def reset_state(self):
        self.can_read = False
        self.can_update = False
        self.can_delete = False
        self.can_apply = False
        self.can_revoke = False
        self.can_reject = False
        self.can_approve = False
        
class ApplicationHistory(models.Model):
    application = models.ForeignKey(Application)
    modified_by = models.ForeignKey(User)
    modified_on = models.DateTimeField(auto_now_add=True)
    state = models.ForeignKey(ApplicationState)
