import logging
from django.db import models
#from django.utils import timezone
#from django.conf import settings

from mis.models import Mis


class HeartBeat(models.Model):
    id = models.BigAutoField(primary_key=True)
    mis_id = models.ForeignKey('mis.Mis', on_delete=models.CASCADE)
    mis_heartbeat = models.DateTimeField(null=True)     # What we got from MIS
    timestamp = models.DateTimeField(auto_now=True)         # Actual time

    class Meta:
        indexes = [
            models.Index(fields=['timestamp', ]),
        ]


class Intercall(models.Model):
    id = models.BigAutoField(primary_key=True)
    mis_to = models.ForeignKey('mis.Mis', null=True, related_name='mis_ic_to', on_delete=models.CASCADE)
    mis_from = models.ForeignKey('mis.Mis', null=True, related_name='mis_ic_from', on_delete=models.CASCADE)
    related_cc = models.SlugField(max_length=32, null=True)
    status = models.ForeignKey('IntercallSatus', default=1, on_delete=models.CASCADE)

    callcard = models.ForeignKey('callcard.CallCard', related_name='intercall_cc', null=True, on_delete=models.CASCADE)

    date_modified = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'To:{self.mis_to}; From:{self.mis_from}; Status: {self.status}'


class IntercallSatus(models.Model):
    # 1-New, 2-Ready, 3-Sent, 4-Fail
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32)

    class Meta:
        verbose_name = "Intercall Queue Status"
        verbose_name_plural = "Intercall Queue Statuses"

    def __str__(self):
        return f'{self.id}: {self.name}'
