#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from datetime import datetime

class UserProfileManager(models.Manager):
    def userprofile_in_employee_and_PM(self):
        profiles = []
        group = Group.objects.get(name='员工')
        for user in group.user_set.all():
            profiles.append(user.userprofile)
        group = Group.objects.get(name='项目经理')
        for user in group.user_set.all():
            profiles.append(user.userprofile)
        return UserProfile.objects.filter(id__in=[o.id for o in profiles])

class UserProfile(models.Model):
    # This field is required.
    user = models.OneToOneField(User)

    # Other fields here
    superior = models.ForeignKey(User, null=True, related_name='subordinates')
    chinese_name = models.CharField(max_length=100)
    english_name = models.CharField(max_length=100, null=True)
    objects = UserProfileManager()
    
    def __unicode__(self):
        return self.chinese_name
    
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
    participants = models.ManyToManyField(User, null=True, related_name='joined_applications')
    state = models.ForeignKey(ApplicationState, editable=False, null=True)
    applicant = models.ForeignKey(User, related_name='applied_applications', editable=False)
    content = models.TextField()
    modified_by = models.ForeignKey(User, editable=False)
    modified_on = models.DateTimeField(auto_now=True, editable=False)

    @property
    def participants_string(self):
        return ', '.join([person.userprofile.chinese_name for person in self.participants.all()])
        
    def applicationflow_by_user(self, user):
        try:
            return self.applicationflow_set.get(applicant=user)
        except:
            return None
            
    def create(self, user, new_app):
        self.state = ApplicationState.objects.get(code='ReadyForDirectorApprove')
        self.applicant = user
        self.modified_by = user
        self.save()
        participants = []
        for userprofile in new_app['participants']:
            participants.append(userprofile.user)
        self.participants = participants
        
        # application flow for current user
        current_flow = ApplicationFlow()
        current_flow.application = self
        current_flow.applicant = self.applicant
        current_flow.set_applicant_state()
        current_flow.save()

        # application flow for participants
        for participant in self.participants.all():
            if participant != self.applicant:
                app_flow = ApplicationFlow()
                app_flow.application = self
                app_flow.applicant = participant
                app_flow.set_viewer_state()
                app_flow.save()

        # application flow for superior
        next_flow = ApplicationFlow()
        next_flow.application = self
        next_flow.applicant = user.userprofile.superior
        next_flow.parent = current_flow
        next_flow.set_reviewer_state()
        next_flow.save()
        
        # application history
        self.write_history(user)
        
        return user.userprofile.superior
        
    def update(self, new_app):
        """new_app is a dictionary"""
        # delete application flow for old participants
        for participant in self.participants.all():
            if participant != self.applicant:
                app_flow = self.applicationflow_by_user(participant)
                if app_flow is not None:
                    app_flow.delete()
          
        participants = []
        for userprofile in new_app['participants']:
            participants.append(userprofile.user)
        self.participants = participants
        
        # create application flow for new participants
        for participant in self.participants.all():
            if participant != self.applicant:
                app_flow = ApplicationFlow()
                app_flow.application = self
                app_flow.applicant = participant
                app_flow.set_viewer_state()
                app_flow.save() 
        
        self.save()
        
    def revoke(self, user):
        self.state = ApplicationState.objects.get(code='Revoke')
        self.save()
        
        flow = self.applicationflow_by_user(user)
        flow.set_revoke_state()
        flow.save()

        flow = self.applicationflow_by_user(user.userprofile.superior)
        flow.delete()
        
        # application history
        self.write_history(user)
        
        return user.userprofile.superior
        
    def apply(self, user):
        self.state = ApplicationState.objects.get(code='ReadyForDirectorApprove')
        self.save()
        
        current_flow = self.applicationflow_by_user(user)
        current_flow.set_applicant_state()
        current_flow.save()

        next_flow = ApplicationFlow()
        next_flow.application = self
        next_flow.applicant = user.userprofile.superior
        next_flow.parent = current_flow
        next_flow.set_reviewer_state()
        next_flow.save()
        
        # application history
        self.write_history(user)
        
        return user.userprofile.superior

    def reject(self, user):
        self.state = ApplicationState.objects.get(code='Reject')
        self.save()
        
        flow = self.applicationflow_by_user(user)
        # change parent flow state
        parent_flow = flow.parent
        parent_flow.set_revoke_state()
        parent_flow.save()
        # delete current flow
        flow.delete()
        
        # application history
        self.write_history(user)
        
        return parent_flow.applicant
        
    def approve(self, user):
        self.state = ApplicationState.objects.get(code='Approved')
        self.save()
        
        applicant_flow = self.applicationflow_by_user(self.applicant)
        applicant_flow.set_hidden_state()
        applicant_flow.save()
        
        current_flow = self.applicationflow_by_user(user)
        if user.userprofile.superior is None:
            current_flow.delete()
        else:
            current_flow.set_hidden_state()
            current_flow.save()

            next_flow = ApplicationFlow()
            next_flow.application = self
            next_flow.applicant = user.userprofile.superior
            next_flow.parent = current_flow
            next_flow.set_reviewer_state()
            next_flow.save()
            
        # application history
        self.write_history(user)
            
    def write_history(self, user):
        history = ApplicationHistory()
        history.application = self
        history.modified_by = user
        history.state = self.state
        history.save()
        self.modified_by = user
        self.save()
    
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
    can_revoke = models.BooleanField()  # 撤销
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
        
    def __unicode__(self):
        return str(self.id)
        
class ApplicationHistory(models.Model):
    application = models.ForeignKey(Application)
    modified_by = models.ForeignKey(User)
    modified_on = models.DateTimeField(auto_now_add=True)
    state = models.ForeignKey(ApplicationState)
