from django.db import models
from django.utils import timezone
from django.conf import settings


class Mis(models.Model):
    id = models.BigAutoField(primary_key=True)
    mis_user = models.OneToOneField(settings.AUTH_USER_MODEL, null=False, default=1, on_delete=models.CASCADE)
    mis_type = models.ForeignKey('MisType', null=False, default=1, on_delete=models.CASCADE)
    mis_name = models.CharField(max_length=255, null=False, default='Невідома МІС')
    mis_facility = models.IntegerField(null=False, default=0)
    state = models.ForeignKey('patients.State', null=True, default=None, on_delete=models.SET_NULL)
    mis_comment = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=False)
    accept_intercall = models.BooleanField(default=True, null=False)
    mis_heartbeat = models.DateTimeField(blank=True, null=True)
    date_modified = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.mis_name)

    class Meta:
        verbose_name = "Mis"
        verbose_name_plural = "Mis"


class SysAddress(models.Model):
    id = models.BigAutoField(primary_key=True)
    index = models.CharField(max_length=5, null=True, blank=False)
    district = models.CharField(max_length=64, null=True, blank=False)
    city = models.CharField(max_length=255, null=False)
    street = models.CharField(max_length=255, null=False)
    building = models.CharField(max_length=255, null=False)
    apartment = models.CharField(max_length=16, null=True, blank=False)
    # місто/село/дорога
    location_type = models.ForeignKey('LocationType', null=False, on_delete=models.CASCADE)
    # квартира/офіс/будинок/завод/публічне місце
    address_type = models.ForeignKey('AddressType', null=False, on_delete=models.CASCADE)
    longitude = models.CharField(max_length=64, null=True, blank=False)
    latitude = models.CharField(max_length=64, null=True, blank=False)
    address_comment = models.CharField(max_length=255, null=True, blank=False)
    date_modified = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.city)


class Facility(models.Model):
    id = models.BigAutoField(primary_key=True)
    mis_id = models.ForeignKey('Mis', on_delete=models.CASCADE)
    mis_facility_id = models.CharField(max_length=16, null=False)
    name = models.CharField(max_length=255, null=False)
    short_name = models.CharField(max_length=255, null=True, blank=False)
    address = models.ForeignKey('SysAddress', null=False, on_delete=models.CASCADE)
    facility_contact = models.CharField(max_length=255, null=True, blank=False)
    facility_phone = models.CharField(max_length=32, null=True, blank=False)
    # Центр/підстанція/ППБ
    facility_type = models.ForeignKey('FacilityType', null=False, on_delete=models.CASCADE)
    facility_comment = models.CharField(max_length=255, null=True, blank=False)
    is_active = models.BooleanField(default=True, null=False)
    facility_parent = models.CharField(max_length=16, null=False, default="0")
    date_modified = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('mis_id', 'mis_facility_id',)
        verbose_name = "Facility"
        verbose_name_plural = "Facilities"

    def __str__(self):
        return str(f'{self.mis_facility_id}')


class Staff(models.Model):
    id = models.BigAutoField(primary_key=True)
    mis_id = models.ForeignKey('Mis', on_delete=models.CASCADE)
    mis_staff_id = models.CharField(max_length=32, null=False, blank=False)
    facility_id = models.ForeignKey('Facility', null=False, on_delete=models.CASCADE)
    mis_facility_id = models.CharField(max_length=16, null=False)
    first_name = models.CharField(max_length=64, null=False, blank=False)
    family_name = models.CharField(max_length=64, null=True, blank=True)
    middle_name = models.CharField(max_length=64, null=True, blank=True)
    birthday = models.DateField(null=True, blank=False)
    sex = models.CharField(max_length=16, null=False, blank=False)
    phone = models.CharField(max_length=32, null=True, blank=False)
    title = models.ForeignKey('StaffTitle', null=False, on_delete=models.CASCADE)
    qualification = models.ForeignKey('StaffQualification', null=False, on_delete=models.CASCADE)
    experience_total = models.CharField(max_length=16, null=True, blank=False)
    experience_field = models.CharField(max_length=16, null=True, blank=False)
    ipn = models.CharField(max_length=16, null=True, blank=False)
    passport = models.CharField(max_length=32, null=True, blank=False)
    sertificate = models.CharField(max_length=32, null=True, blank=False)
    last_qualification_date = models.DateField(null=True, blank=False)

    #workload = model.DoubleField()

    is_active = models.BooleanField(default=True, null=False)
    staff_comment = models.CharField(max_length=255, null=True, blank=True)
    date_modified = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('mis_id', 'mis_staff_id')
        verbose_name = "Staff"
        verbose_name_plural = "Staff"

    def __str__(self):
        return str(f'{self.mis_staff_id}')


# class StaffWorkload(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     mis_id = models.ForeignKey('Mis', on_delete=models.CASCADE)
#     mis_staff_id = models.CharField(max_length=32, null=False, blank=False)
#     facility_id = models.ForeignKey('Facility', null=False, on_delete=models.CASCADE)

#     mis_facility_id = models.CharField(max_length=16, null=False)
#     date_modified = models.DateTimeField(auto_now=True)
#     timestamp = models.DateTimeField(auto_now_add=True)


class Cars(models.Model):
    id = models.BigAutoField(primary_key=True)
    mis_id = models.ForeignKey('Mis', null=False, on_delete=models.CASCADE)
    facility_id = models.ForeignKey('Facility', null=False, on_delete=models.CASCADE)
    mis_car_id = models.CharField(max_length=32, null=False, blank=False)
    mis_facility_id = models.CharField(max_length=16, null=False, blank=False)
    car_model = models.CharField(max_length=64, null=True, blank=False)
    car_type = models.ForeignKey('CarType', null=False, on_delete=models.CASCADE)
    year_made = models.IntegerField(null=False, blank=False, default=1980)
    year_start = models.IntegerField(null=False, blank=False, default=1980)
    gov_number = models.CharField(max_length=16, null=True, blank=False)
    car_status = models.ForeignKey('CarStatus', null=False, on_delete=models.CASCADE)
    car_owner = models.ForeignKey('CarOwner', null=False, on_delete=models.CASCADE)
    car_field_number = models.CharField(max_length=32, null=True, blank=False)
    car_comment = models.CharField(max_length=255, null=True, blank=False)
    is_active = models.BooleanField(default=True, null=False)
    date_modified = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('mis_id', 'mis_car_id')
        verbose_name = "Car"
        verbose_name_plural = "Cars"

    def __str__(self):
        return str(f'{self.mis_car_id}')


class CarType(models.Model):    # C/B/A1/A2/нестандарт
    id = models.BigAutoField(primary_key=True)
    cartype_name = models.CharField(max_length=64, null=False)

    def __str__(self):
        return str(f'{self.id}: {self.cartype_name}')


class CarStatus(models.Model):  # Робочій/не робочій
    id = models.BigAutoField(primary_key=True)
    carstatus_name = models.CharField(max_length=64, null=False)

    def __str__(self):
        return str(f'{self.id}: {self.carstatus_name}')


class CarOwner(models.Model):   # Власний/арендований
    id = models.BigAutoField(primary_key=True)
    carowner_name = models.CharField(max_length=64, null=False)

    def __str__(self):
        return str(f'{self.id}: {self.carowner_name}')


class StaffTitle(models.Model):
    id = models.BigAutoField(primary_key=True)
    title_name = models.CharField(max_length=64, null=False)

    def __str__(self):
        return str(f'{self.id}: {self.title_name}')


class StaffQualification(models.Model):
    id = models.BigAutoField(primary_key=True)
    qualification_name = models.CharField(max_length=64, null=False)

    def __str__(self):
        return str(f'{self.id}: {self.qualification_name}')


class FacilityType(models.Model):       # Центр/підстанція/ППБ
    id = models.BigAutoField(primary_key=True)
    facilitytype_name = models.CharField(max_length=64, null=False)

    def __str__(self):
        return str(f'{self.id}: {self.facilitytype_name}')


class LocationType(models.Model):       # місто/село/дорога
    id = models.BigAutoField(primary_key=True)
    locationtype_name = models.CharField(max_length=64, null=False)
    locationtype_short = models.CharField(max_length=8, null=False)

    def __str__(self):
        return str(f'{self.id}: {self.locationtype_name}')


class AddressType(models.Model):       # квартира/офіс/будинок/завод/публічне місце
    id = models.BigAutoField(primary_key=True)
    addresstype_name = models.CharField(max_length=64, null=False)
    addresstype_short = models.CharField(max_length=8, null=False)

    def __str__(self):
        return str(f'{self.id}: {self.addresstype_name}')


class MisType(models.Model):       # MIS/Extension/Test/Waiting
    id = models.BigAutoField(primary_key=True)
    mistype_name = models.CharField(max_length=16, null=False)
    mistype_comment = models.CharField(max_length=32, null=False)

    def __str__(self):
        return str(f'{self.id}: {self.mistype_name}')
