from django.db import models
from django.contrib.auth.models import User
from dateutil.rrule import *
from datetime import datetime, timedelta
from django.utils.timezone import utc
import pickle

# Create your models here.

FREQUENCY_CHOICES = (
    ('YEARLY','yearly'),
    ('MONTHLY','monthly'),
    ('WEEKLY','weekly'),
    ('DAILY','daily'),
)

class RecurrenceRule(models.Model):
    '''
    This class stores an rrule object from python-dateutil as a django model for saving to the database. 
    '''
    name = models.CharField(max_length=36)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    params = models.BinaryField(blank=True)
    def get_params(self):
        if self.params:
            return pickle.loads(self.params)

    def save(self, *args, **kwargs):
        if self.params:
            self.params = pickle.dumps(self.params)
        super(RecurrenceRule, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

class Event(models.Model):
    '''
    This class defines a calendar event instance, which may be one-time or recurring via ForeignKey relation to a RecurrenceRule object
    '''
    name = models.CharField(max_length=36)
    creator = models.ForeignKey(User)
    rule = models.ForeignKey(RecurrenceRule, blank=True, null=True)
    startdatetime = models.DateTimeField(blank=True, null=True)
    enddatetime = models.DateTimeField(blank=True, null=True)
    allday = models.BooleanField(default=False)

    def get_recurrence_rule(self):
        '''
        Returns the dateutil.rrule object instance associated with this Event
        '''
        if self.rule:
            return rrule(eval(self.rule.frequency), dtstart=self.startdatetime, **self.rule.get_params())
        return None

    def get_event_occurrences(self, start, end):
        '''
        Accepts start and end datetime objects and returns a list of Event objects that fall between the start and end date arguments,
        representing occurrences of this particular event. 
        '''
        if self.rule:
            rule = self.get_recurrence_rule()
            recurrence_dates = rule.between(start, end, inc=True)
            duration = self.enddatetime - self.startdatetime
            events = [Event(
                name=self.name, 
                creator=self.creator, 
                rule=self.rule, 
                startdatetime=date,
                enddatetime=date+duration,
                allday=self.allday,
            ) for date in recurrence_dates]
            return events
        else:
            if (self.startdatetime >= start):
                return [self]
            else: 
                return []

    def get_occurrences(self, start, end):
        '''
        Accepts start and end datetime objects and returns a list of datetime objects that fall between the start and end date arguments
        according to this event's rrule instance.
        TODO: return both calculated recurrence dates and persistent Occurrence objects.
        '''
        rule = self.get_recurrence_rule()
        return rule.between(start, end, inc=True)

    def get_month_event_occurrences(self, *args, **kwargs):
        '''
        Takes a year and month as arguments and returns a list of datetime objects representing the 
        occurrences of the event during the specified month
        '''
        year = kwargs['year']
        month = kwargs['month']
        if month not in range(1, 13):
            raise Exception("Month must be between 1 and 12.")
        occurrences = self.get_occurrences(start=datetime(year, month, 1, tzinfo=utc), end=datetime(year, month+1, 1, tzinfo=utc))
        return occurrences 

    def get_week_event_occurrences(self, *args, **kwargs):
        '''
        Takes a year, and week as arguments and returns a list of datetime objects representing the occurrences 
        of the event during the specified week
        '''
        year = kwargs['year']
        week = kwargs['week']
        start_of_week = datetime.strptime(str(year) + str(week) +"0+0000","%Y%U%w%z")
        if week not in range(1,54):
            raise Exception("Week must be between 1 and 53")
        occurrences = self.get_occurrences(start=start_of_week, end=start_of_week+timedelta(weeks=1))
        return occurrences

class Occurrence(models.Model):
    '''
    Persists an occurrence instance of a recurring event to the database so that other objects can be associated to an occurrence.
    '''
    event = models.ForeignKey(Event)