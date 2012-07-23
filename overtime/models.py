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
        
    @property
    def applicationflow_by_user(self, user):
        return self.applicationflow_set.filter(applicant=user)[0]
        
    def approve(self, user):
        current_flow = ApplicationFlow.objects.get(application=self, applicant=user)
        pass
        
    def reject(self, user):
        pass
        
    def apply(self, user):
        pass

    def __unicode__(self):
        return self.subject
        
class ApplicationFlow(models.Model):
    application = models.ForeignKey(Application)
    applicant = models.ForeignKey(User)
    parent = models.ForeignKey('self', null=True)
    #permissions
    read = models.BooleanField()
    update = models.BooleanField()
    delete = models.BooleanField()
    apply = models.BooleanField()
    reject = models.BooleanField()
    approve = models.BooleanField()
    
    # 申请人    
    def set_applicant_state(self):
        self.read = True
        self.update = False
        self.delete = True
        self.apply = False
        self.reject = False
        self.approve = False
     
    # 批准过的人
    def set_hidden_state(self):
        self.read = False
        self.update = False
        self.delete = False
        self.apply = False
        self.reject = False
        self.approve = False

    # 审核人
    def set_reviewer_state(self):
        self.read = True
        self.update = False
        self.delete = False
        self.apply = False
        self.reject = True
        self.approve = True
        
class ApplicationHistory(models.Model):
    application = models.ForeignKey(Application)
    modified_by = models.ForeignKey(User)
    modified_on = models.DateTimeField(auto_now_add=True)
    state = models.ForeignKey(ApplicationState)
