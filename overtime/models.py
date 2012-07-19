from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class ApplicationState(models.Model):
    state = models.CharField(max_length=100)

    def __unicode__(self):
        return self.state
                
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

    def __unicode__(self):
        return self.subject
    

    
