from django.db import models
from django.utils.translation import gettext_lazy as _
from callcard.models import CallCard, CallStations, CallPriority
from patients.models import ChiefComplain
from mis.models import LocationType, AddressType


class PushQueue(models.Model):
    id = models.BigAutoField(primary_key=True)
    push_filter = models.ForeignKey('PushFilter', on_delete=models.CASCADE)
    call_card = models.ForeignKey('callcard.CallCard', on_delete=models.CASCADE)
    status = models.ForeignKey('PushStatus', default=1, on_delete=models.CASCADE)
    push_url = models.URLField(null=True)
    telegram_bot = models.ForeignKey('TelegramBot', on_delete=models.SET_NULL, blank=True, null=True)
    message = models.CharField(max_length=1024, null=True)
    date_sent = models.DateTimeField(null=True)
    date_modified = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Push Queue"
        verbose_name_plural = "Push Queue"

    def __str__(self):
        return f'{self.id}:{self.push_filter}'


class PushFilter(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(_('Filter name'), max_length=64)
    customer = models.ForeignKey('PushCustomer', on_delete=models.CASCADE)

    is_push_url = models.BooleanField(default=False, null=False)
    push_url = push_url = models.URLField(null=True)
    is_bot = models.BooleanField(default=False, null=False)
    telegram_bot = models.ForeignKey('TelegramBot', on_delete=models.SET_NULL, blank=True, null=True)

    mis_id_logic = models.ForeignKey('FilterLogic', default=2, related_name='mis_id_logic', on_delete=models.CASCADE)
    mis_id = models.ForeignKey('mis.Mis', on_delete=models.CASCADE)
    call_station_logic = models.ForeignKey('FilterLogic', default=1, related_name='call_station_logic', on_delete=models.CASCADE)
    call_station = models.ForeignKey('callcard.CallStations', null=True, blank=True, on_delete=models.SET_NULL)
    call_result_logic = models.ForeignKey('FilterLogic', default=1, related_name='call_result_logic', on_delete=models.CASCADE)
    call_result = models.ForeignKey('callcard.CallResult', null=True, blank=True, on_delete=models.SET_NULL)
    call_priority_logic = models.ForeignKey('FilterLogic', default=1, related_name='call_priority_logic', on_delete=models.CASCADE)
    call_priority = models.ForeignKey('callcard.CallPriority', null=True, blank=True, on_delete=models.SET_NULL)

    complain_code_logic = models.ForeignKey('FilterLogic', default=1, related_name='complain_logic_code', on_delete=models.CASCADE)
    chief_complain_code = models.ForeignKey('patients.ChiefComplain', null=True, blank=True, on_delete=models.CASCADE)
    complain_text_logic = models.ForeignKey('FilterLogic', default=1, related_name='complain_logic_text', on_delete=models.CASCADE)
    chief_complain_text = models.CharField(max_length=64, null=True, blank=True)

    address_district_logic = models.ForeignKey('FilterLogic', default=1, related_name='address_district_logic', on_delete=models.CASCADE)
    address_district = models.CharField(max_length=64, null=True, blank=True)
    address_city_logic = models.ForeignKey('FilterLogic', default=1, related_name='address_city_logic', on_delete=models.CASCADE)
    address_city = models.CharField(max_length=64, null=True, blank=True)
    address_locationtype_logic = models.ForeignKey('FilterLogic', default=1, related_name='address_locationtype_logic', on_delete=models.CASCADE)
    address_locationtype = models.ForeignKey('mis.LocationType', default=1, null=False, on_delete=models.CASCADE)  # місто/село/дорога

    is_active = models.BooleanField(default=True, null=False)
    date_modified = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Push Filter"
        verbose_name_plural = "Push Filters"

    def __str__(self):
        return self.name


class PushCustomer(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=64, null=False, blank=False)

    class Meta:
        verbose_name = "Push Customer"
        verbose_name_plural = "Push Customers"

    def __str__(self):
        return self.name


class PushStatus(models.Model):
    # 1-New, 2-Sent, 3-Archive
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32)

    class Meta:
        verbose_name = "Push Queue Status"
        verbose_name_plural = "Push Queue Statuses"

    def __str__(self):
        return self.name


class FilterLogic(models.Model):
    # Logic: 1-Ignore, 2-Equal, 3-Contain
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32)

    class Meta:
        verbose_name = "FilterLogic"
        verbose_name_plural = "FilterLogic"

    def __str__(self):
        return self.name


class TelegramBot(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32)
    token = models.CharField(max_length=64)
    chanel = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True, null=False)

    class Meta:
        verbose_name = "TelegramBot"
        verbose_name_plural = "TelegramBots"

    def __str__(self):
        return self.name
