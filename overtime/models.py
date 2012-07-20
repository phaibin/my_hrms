from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from datetime import datetime

class ProfileBase(type):  
    def __new__(cls, name, bases, attrs):  
        module = attrs.pop('__module__')  
        parents = [b for b in bases if isinstance(b, ProfileBase)]  
        if parents:  
            fields = []  
            for obj_name, obj in attrs.items():  
                if isinstance(obj, models.Field): fields.append(obj_name)  
                User.add_to_class(obj_name, obj)  
            UserAdmin.fieldsets = list(UserAdmin.fieldsets)  
            UserAdmin.fieldsets.append((name, {'fields': fields}))  
        return super(ProfileBase, cls).__new__(cls, name, bases, attrs)  
          
class Profile(object):  
    __metaclass__ = ProfileBase  
  
class MyProfile(Profile):  
    pass

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
    participants = models.ManyToManyField(User)
    state = models.ForeignKey(ApplicationState, editable=False, blank=True)

    @property
    def participants_string(self):
        return ', '.join([person.username for person in self.participants.all()])
        
    @property
    def state_string(self):
        
        return ', '.join([person.username for person in self.participants.all()])

    def __unicode__(self):
        return self.subject
    

    
