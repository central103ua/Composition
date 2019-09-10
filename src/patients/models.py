from django.db import models
from django.utils import timezone
from django.conf import settings
from mis.models import LocationType, AddressType


class Patient(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=64, null=False, blank=True, default='НЕВІДОМИЙ')
    first_name = models.CharField(max_length=64, null=True, blank=True)
    family_name = models.CharField(max_length=64, null=True, blank=True)
    middle_name = models.CharField(max_length=64, null=True, blank=True)
    age = models.CharField(max_length=64, null=True, blank=False)
    sex = models.CharField(max_length=16, null=True, blank=False)
    phone = models.CharField(max_length=32, null=True, blank=True)
    date_modified = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


class Address(models.Model):
    id = models.BigAutoField(primary_key=True)
    index = models.CharField(max_length=5, null=True, blank=False)
    district = models.CharField(max_length=64, null=True, blank=False)
    distr = models.ForeignKey('District', null=True, on_delete=models.SET_NULL)
    city = models.CharField(max_length=255, null=True, blank=False)
    street = models.CharField(max_length=255, null=True, blank=False)
    building = models.CharField(max_length=255, null=True, blank=True)
    apartment = models.CharField(max_length=16, null=True, blank=False)
    location_type = models.ForeignKey('mis.LocationType', null=False, on_delete=models.CASCADE)  # місто/село/дорога
    address_type = models.ForeignKey('mis.AddressType', null=False, on_delete=models.CASCADE)  # квартира/офіс/будинок/завод/публічне місце
    address_comment = models.CharField(max_length=255, null=True, blank=False)
    longitude = models.CharField(max_length=64, null=True, blank=False)   # Георграфічна долгота
    latitude = models.CharField(max_length=64, null=True, blank=False)    # Географічна широта
    date_modified = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.city)


class Complain(models.Model):
    id = models.BigAutoField(primary_key=True)
    # Chief complain; Головна скарга
    complain1 = models.CharField(max_length=255, null=True, blank=True)
    # Vital signs; Життеві показники
    complain2 = models.CharField(max_length=255, null=True, blank=True)
    # Patient status details; Стан пацієнта
    complain3 = models.CharField(max_length=255, null=True, blank=True)
    # Sircumstances; Обставини подій
    complain4 = models.CharField(max_length=255, null=True, blank=True)
    # Code Complain
    code_complain = models.CharField(max_length=10, null=True, blank=True)
    # Code Situation
    code_sit = models.ForeignKey('Situation', null=True, on_delete=models.CASCADE)
    chief_complain = models.ForeignKey('ChiefComplain', null=True, on_delete=models.CASCADE)
    breath_state = models.ForeignKey('BreathState', null=True, on_delete=models.CASCADE)
    consc_state = models.ForeignKey('ConscState', null=True, on_delete=models.CASCADE)
    patient_state = models.ForeignKey('PatientState', null=True, on_delete=models.CASCADE)

    date_modified = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class ChiefComplain(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)

    def __str__(self):
        return self.name


class PatientState(models.Model):
    id = models.AutoField(primary_key=True)
    chief_complain = models.ForeignKey('ChiefComplain', null=False, on_delete=models.CASCADE)
    sub_code = models.IntegerField(null=False)
    code = models.CharField(max_length=5, null=False, unique=True)
    name = models.CharField(max_length=255, null=False)

    def __str__(self):
        return self.code


class BreathState(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=2, null=False, unique=True)
    name = models.CharField(max_length=64, null=False)

    def __str__(self):
        return self.code


class ConscState(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=2, null=False, unique=True)
    name = models.CharField(max_length=64, null=False)

    def __str__(self):
        return self.code


class Situation(models.Model):
    id = models.AutoField(primary_key=True)
    code_dsns = models.IntegerField(null=False)
    name = models.CharField(max_length=64, null=False)

    def __str__(self):
        return self.code_dsns

class State(models.Model):
    id = models.AutoField(primary_key=True)
    level1 = models.CharField(max_length=10, null=False)
    name = models.CharField(max_length=32, null=False)
    capital = models.CharField(max_length=32, null=False)

    def __str__(self):
        return self.name

class District(models.Model):
    id = models.AutoField(primary_key=True)
    state = models.ForeignKey('State', null=False, on_delete=models.CASCADE)
    level1 = models.CharField(max_length=10, null=False)
    level2 = models.CharField(max_length=10, null=False)
    name = models.CharField(max_length=32, null=False)
    capital = models.CharField(max_length=32, null=False)

    def __str__(self):
        return self.name