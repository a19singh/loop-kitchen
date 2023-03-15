import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class StoreStatus(models.Model):
    """
    Model to keep store status
    """
    store_id = models.ForeignKey('base.StoreZone', to_field='store_id',
                                 on_delete=models.CASCADE)
    status = models.CharField(max_length=10, default='')
    timestamp = models.DateTimeField()


class MenuHours(models.Model):
    """
    Model to monitor store opening and closing time
    """
    class WeekDays(models.IntegerChoices):
        Monday = 0, _('Monday')
        Tuesday = 1, _('Tuesday')
        Wednesday = 2, _('Wednesday')
        Thursday = 3, _('Thursday')
        Friday = 4, _('Friday')
        Saturday = 5, _('Saturday')
        Sunday = 6, _('Sunday')

    store_id = models.ForeignKey('base.StoreZone', to_field='store_id',
                                 on_delete=models.CASCADE)
    dayOfWeek = models.IntegerField(default=WeekDays.Monday,
                                    choices=WeekDays.choices)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()


class StoreZone(models.Model):
    """
    Model to map store to their location timezone
    """
    store_id = models.BigAutoField(primary_key=True, db_column='store_id')
    timezone = models.CharField(max_length=50, default='America/Chicago')
    open24x7 = models.BooleanField(default=True)


class Report(models.Model):
    """
    Model to store report data
    report_id: to store unique uuid
    report_status: To store status of report
        whether the report is ready to be fetched or not
    file: Report endpoint
    """
    report_id = models.UUIDField(unique=True, default=uuid.uuid4)
    status = models.CharField(max_length=10, default="running")
    path = models.TextField(default='')
