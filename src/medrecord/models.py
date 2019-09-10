from django.db import models
from django.utils import timezone
from django.conf import settings
from patients.models import Patient, Address


class MedRecordSlug(models.Model):
    id = models.BigAutoField(primary_key=True)
    date_modified = models.DateTimeField(auto_now=True)


class MedRecord(models.Model):
    id = models.BigAutoField(primary_key=True)
    med_record_id = models.SlugField(max_length=32, null=False, unique=True)
    call_card_id = models.SlugField(max_length=32, null=False)
    mis_id = models.ForeignKey('mis.Mis', null=False, on_delete=models.CASCADE)
    callcard = models.ForeignKey('callcard.CallCard', null=False, on_delete=models.CASCADE)
    crew = models.ForeignKey('crew.Crew', null=False, on_delete=models.CASCADE)
    operator_id = models.ForeignKey('mis.Staff', null=False, on_delete=models.CASCADE)
    mis_medrecord_id = models.CharField(max_length=64, null=False, blank=False)

    start_datetime = models.DateTimeField(null=False, blank=False)
    time_crew = models.DateTimeField(null=False, blank=False)
    time_depart = models.DateTimeField(null=False, blank=False)
    time_patient = models.DateTimeField(null=True, blank=False)
    time_transport = models.DateTimeField(null=True, blank=False)
    time_hospital = models.DateTimeField(null=True, blank=False)
    end_datetime = models.DateTimeField(null=False, blank=False)

    patient = models.OneToOneField('patients.Patient', null=True, on_delete=models.SET_NULL)
    patient_address_src = models.ForeignKey('AddrDocType', null=False, on_delete=models.CASCADE)
    patient_document = models.CharField(max_length=64, null=True, blank=True)
    patient_address = models.OneToOneField('patients.Address',
                                           null=True,
                                           on_delete=models.SET_NULL,
                                           related_name='patient_address_medrecord')
    call_address = models.OneToOneField('patients.Address',
                                        null=True,
                                        on_delete=models.SET_NULL,
                                        related_name='call_address_medrecord')
    noresult = models.ForeignKey('NoResult', null=False, default=1, on_delete=models.CASCADE)

    primary_exam = models.CharField(max_length=64, null=True, blank=False)
    secondary_exam = models.CharField(max_length=64, null=True, blank=False)

    medical_history = models.CharField(max_length=1024, null=True, blank=True)
    therapy_materials = models.CharField(max_length=1024, null=True, blank=True)
    alergy = models.CharField(max_length=1024, null=True, blank=True)

    help_privided = models.CharField(max_length=256, null=True, blank=True)
    reanimation = models.CharField(max_length=256, null=True, blank=True)

    medicine_applyed = models.BooleanField(default=False, null=False)

    mr_result = models.ForeignKey('MRResult', null=True, on_delete=models.SET_NULL)

    is_hospital_record = models.BooleanField(default=False, null=False)
    is_diagnosis_record = models.BooleanField(default=False, null=False)

    mr_comment = models.CharField(max_length=255, null=True)

    date_modified = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "MedRecord"
        verbose_name_plural = "MedRecords"

    def __str__(self):
        return self.medrecord_id


class MRDiagnosis(models.Model):
    id = models.BigAutoField(primary_key=True)
    medrecord = models.ForeignKey('MedRecord', null=False, on_delete=models.CASCADE)
    diagnosis_seq = models.IntegerField(null=False)
    callcard = models.ForeignKey('callcard.CallCard', on_delete=models.CASCADE)
    med_record_id = models.SlugField(max_length=32, null=False)

    mkx = models.ForeignKey('MKXfull', null=True, on_delete=models.SET_NULL)
    d_text = models.CharField(max_length=256, null=True)
    is_crew = models.BooleanField(default=True, null=False)
    doctor_name = models.CharField(max_length=64, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.medrecord_id}:{mrd_num}'


class MRHospital(models.Model):
    id = models.BigAutoField(primary_key=True)
    hospital_seq = models.IntegerField(null=False)
    medrecord = models.ForeignKey('MedRecord', null=False, on_delete=models.CASCADE)
    callcard = models.ForeignKey('callcard.CallCard', on_delete=models.CASCADE)
    med_record_id = models.SlugField(max_length=32, null=False)

    the_place = models.CharField(max_length=255, null=False)
    the_doctor = models.CharField(max_length=255, null=False)
    document = models.CharField(max_length=32, null=True)
    event_datetime = models.DateTimeField(null=False, blank=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.medrecord_id}:{mrh_num}'


class MRResult(models.Model):
    id = models.BigAutoField(primary_key=True)
    the_result = models.ForeignKey('TheResult', null=False, default=1, on_delete=models.CASCADE)
    result_action = models.ForeignKey('ResultAction', null=False, default=1, on_delete=models.CASCADE)
    death_datetime = models.DateTimeField(null=True)
    is_hospital = models.BooleanField(default=False, null=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.the_result


# OK/не застали/адреса не знайдена/...
class NoResult(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32, null=False)

    def __str__(self):
        return self.name


# Покращення/Без змін/Погіршення/Хибний виклик/...
class TheResult(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=32, null=False)

    def __str__(self):
        return self.name


# Залишений/Самостійно/на руках/на ношах/на щиті
class ResultAction(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=32, null=False)

    def __str__(self):
        return self.name


class AddrDocType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64, null=False)
    comment = models.CharField(max_length=64, null=False)

    def __str__(self):
        return self.name


class MKXcode1(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=8, null=False)
    code_start = models.CharField(max_length=8, null=False)
    code_end = models.CharField(max_length=8, null=False)
    code_name = models.CharField(max_length=256, null=False)

    def __str__(self):
        return self.code


class MKXcode2(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=8, null=False)
    code_start = models.CharField(max_length=8, null=False)
    code_end = models.CharField(max_length=8, null=False)
    code_name = models.CharField(max_length=256, null=False)

    def __str__(self):
        return self.code


class MKXcode3(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=8, null=False)
    code_name = models.CharField(max_length=256, null=False)

    def __str__(self):
        return self.code


# class MKX(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     code1 = models.ForeignKey('MKXcode1', null=True, on_delete=models.SET_NULL)
#     code2 = models.ForeignKey('MKXcode2', null=True, on_delete=models.SET_NULL)
#     code3 = models.ForeignKey('MKXcode3', null=True, on_delete=models.SET_NULL)
#     code3_code = models.CharField(max_length=4, null=False)
#     code_full = models.CharField(max_length=8, null=False)
#     name = models.CharField(max_length=256, null=False)
#     code_big = models.CharField(max_length=8, null=False)

#     def __str__(self):
#         return self.code_full


class MKXfull(models.Model):
    id = models.BigAutoField(primary_key=True)
    level = models.IntegerField(null=False)
    code_full = models.CharField(max_length=10, null=False)
    name = models.CharField(max_length=512, null=False)
    name_en = models.CharField(max_length=512, null=False)

    def __str__(self):
        return self.code_full
