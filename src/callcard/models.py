from django.db import models
from django.utils import timezone
from django.conf import settings
from patients.models import Patient, Address


class CallCardSlug(models.Model):
    id = models.BigAutoField(primary_key=True)
    date_modified = models.DateTimeField(auto_now=True)


class CallCard(models.Model):
    id = models.BigAutoField(primary_key=True)
    call_card_id = models.SlugField(max_length=32, null=False, unique=True)
    mis_id = models.ForeignKey('mis.Mis', on_delete=models.CASCADE)
    mis_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    operator_id = models.ForeignKey('mis.Staff', on_delete=models.CASCADE)
    mis_call_card_id = models.CharField(max_length=64, null=False, blank=False)
    caller_number = models.CharField(max_length=64, null=True, blank=False)
    call_priority = models.ForeignKey('CallPriority', on_delete=models.CASCADE, default=6)
    call_result = models.ForeignKey('CallResult', on_delete=models.CASCADE, null=True)
    call_station = models.ForeignKey('CallStations', on_delete=models.CASCADE)

    complain = models.ForeignKey('patients.Complain', null=True, on_delete=models.SET_NULL)
    patient = models.ForeignKey('patients.Patient', null=True, on_delete=models.SET_NULL)
    call_address = models.ForeignKey('patients.Address', null=True, on_delete=models.SET_NULL)
    intercall = models.ForeignKey('CCIntercall', null=True, on_delete=models.CASCADE)
    crew_id = models.ForeignKey('crew.Crew', null=True, on_delete=models.SET_NULL)
    call_comment = models.CharField(max_length=255, null=True)

    start_datetime = models.DateTimeField(null=False, default=timezone.now, blank=False)
    end_datetime = models.DateTimeField(null=False, blank=False)
    date_modified = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['timestamp', ]),
            models.Index(fields=['start_datetime', ]),
        ]

    def __str__(self):
        ret = f'{self.mis_id}:{self.call_card_id}'
        return ret


class CallRecord(models.Model):
    id = models.BigAutoField(primary_key=True)
    card_id = models.ForeignKey('CallCard', on_delete=models.CASCADE)
    mis_id = models.ForeignKey('mis.Mis', on_delete=models.CASCADE)
    mis_call_card_id = models.CharField(max_length=64, null=False, blank=False)
    call_record_seq = models.IntegerField(null=False)
    start_datetime = models.DateTimeField(null=False)
    end_datetime = models.DateTimeField(null=False)
    operator_id = models.ForeignKey('mis.Staff', on_delete=models.CASCADE)
    call_station = models.ForeignKey('CallStations', on_delete=models.CASCADE, default=0)
    crew_id = models.ForeignKey('crew.Crew', null=True, on_delete=models.SET_NULL)
    call_record_comment = models.CharField(max_length=255, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['start_datetime', ]),
        ]


class CCIntercall(models.Model):
    id = models.BigAutoField(primary_key=True)
    mis_to = models.ForeignKey('mis.Mis', null=True, related_name='mis_ccic_to', on_delete=models.CASCADE)
    mis_from = models.ForeignKey('mis.Mis', null=True, related_name='mis_ccic_from', on_delete=models.CASCADE)
    related_cc = models.SlugField(max_length=32, null=True)

    def __str__(self):
        return self.mis_to


class CallPriority(models.Model):
    id = models.AutoField(primary_key=True)
    priority_name = models.CharField(max_length=32, null=False)
    priority_comment = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.priority_name


class CallStations(models.Model):
    id = models.AutoField(primary_key=True)
    station_name = models.CharField(max_length=32, null=False)
    station_comment = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.station_name


class CallResult(models.Model):
    id = models.AutoField(primary_key=True)
    result_name = models.CharField(max_length=32, null=False)
    result_comment = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.result_name
