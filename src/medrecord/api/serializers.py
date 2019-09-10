import time
import logging
import random
from datetime import date
from rest_framework import serializers
from collections import Mapping, OrderedDict
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.serializers import ModelSerializer
from rest_framework.fields import get_error_detail, set_value
from rest_framework.settings import api_settings
from django.db import transaction
from django.conf import settings
from sequences import get_next_value
#from mis.models import Cars, Staff, Facility
from crew.models import Crew
from mis.models import Mis, Staff
from callcard.models import CallCard
from patients.models import Patient, Address, Complain
from patients.serializers import PatientSerializer, AddressSerializer, ComplainSerializer
from medrecord.models import MedRecord, MedRecordSlug, AddrDocType
from medrecord.models import NoResult, MRResult, TheResult, ResultAction, MRDiagnosis, MRHospital
from medrecord.models import MKXfull

# Non-field imports, but public API
from rest_framework.fields import (  # NOQA # isort:skip
    CreateOnlyDefault, CurrentUserDefault, SkipField, empty
)


class HospitalSerializer(serializers.ModelSerializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        self.medrecord = kwargs.pop('mr_id', None)
        self.med_record_id = kwargs.pop('mr_slug', None)
        self.callcard = kwargs.pop('cc_id', None)
        self.seq = 1
        logging.info(f'__init__: HospitalSerializer: {self.medrecord}')
        super(ModelSerializer, self).__init__(instance=instance, data=data, **kwargs)

    class Meta:
        model = MRHospital
        fields = [
            'id',
            'medrecord',
            'hospital_seq',
            'callcard',
            'med_record_id',
            'the_place',
            'the_doctor',
            'document',
            'event_datetime',
            'timestamp',
        ]
        read_only_fields = ['id']

    def to_internal_value(self, data):
        logging.info("HospitalSerializer: To to_internal_value")
        data['medrecord'] = self.medrecord
        data['callcard'] = self.callcard
        data['med_record_id'] = self.med_record_id
        data['hospital_seq'] = self.seq
        self.seq += 1

        ret = super().to_internal_value(data=data)
        return ret

    def to_representation(self, instance):
        logging.info("HospitalSerializer: to_represintation")
        mrh_data = super().to_representation(instance)
        del mrh_data['id']

        return mrh_data


class DiagnosisSerializer(serializers.ModelSerializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        self.medrecord = kwargs.pop('mr_id', None)
        self.med_record_id = kwargs.pop('mr_slug', None)
        self.callcard = kwargs.pop('cc_id', None)
        self.seq = 1
        logging.info(f'__init__: DiagnosisSerializer: {self.medrecord}')
        super(ModelSerializer, self).__init__(instance=instance, data=data, **kwargs)

    class Meta:
        model = MRDiagnosis
        fields = [
            'id',
            'medrecord',
            'diagnosis_seq',
            'callcard',
            'med_record_id',
            'mkx',
            'd_text',
            'is_crew',
            'doctor_name',
            'timestamp',
        ]
        read_only_fields = ['id']

    def to_internal_value(self, data):
        logging.info("DiagnosisSerializer: To to_internal_value")
        data['medrecord'] = self.medrecord
        data['callcard'] = self.callcard
        data['med_record_id'] = self.med_record_id
        data['diagnosis_seq'] = self.seq
        self.seq += 1
        mkx = data.get('mkx', False)
        if mkx:
            mkx_q = MKXfull.objects.filter(code_full=mkx)
            if mkx_q.exists():
                data['mkx'] = mkx_q.first().id
            else:
                error = f"DiagnosisSerializer: MKX-10: {mkx} does not exist"
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        # else:
        #     error = "DiagnosisSerializer: MKX-10 is required"
        #     logging.error(error)
        #     raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        ret = super().to_internal_value(data=data)
        return ret

    def to_representation(self, instance):
        logging.info("DiagnosisSerializer: to_represintation")
        mrd_data = super().to_representation(instance)
        del mrd_data['id']

        mkx_obj = MKXfull.objects.get(id=mrd_data['mkx'])
        mrd_data['mkx'] = mkx_obj.code_full
        mrd_data['mkx-text'] = mkx_obj.name

        return mrd_data


class MRResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = MRResult
        fields = [
            'the_result',
            'death_datetime',
            'result_action',
            'is_hospital'
        ]

    def to_internal_value(self, data):
        logging.info("MRResultSerializer: To to_internal_value")

        the_result = data.get('the_result', None)
        if the_result:
            the_result_qs = TheResult.objects.filter(name=the_result)
            if the_result_qs.exists():
                the_result_obj = the_result_qs.first()
                data['the_result'] = the_result_obj.id
            else:
                error = f"Bad the_result: {data['the_result']}"
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        else:
            data['the_result'] = 1     # Покращення

        result_action = data.get('result_action', None)
        if result_action:
            result_action_qs = ResultAction.objects.filter(name=result_action)
            if result_action_qs.exists():
                result_action_obj = result_action_qs.first()
                data['result_action'] = result_action_obj.id
            else:
                error = f"Bad result_action: {data['result_action']}"
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        else:
            data['result_action'] = 1     # Залишений на місці

        ret = super().to_internal_value(data=data)
        return ret

    def to_representation(self, instance):
        result_data = super().to_representation(instance)

        result_data['the_result'] = TheResult.objects.get(id=result_data['the_result']).name
        result_data['result_action'] = ResultAction.objects.get(id=result_data['result_action']).name

        return result_data


class MedRecordSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(allow_null=True)
    patient_address = AddressSerializer(allow_null=True)
    call_address = AddressSerializer(allow_null=True)
    mr_result = MRResultSerializer(allow_null=True)

    class Meta:
        model = MedRecord
        fields = [
            'id',
            'med_record_id',
            'call_card_id',
            'mis_id',
            'callcard',
            'crew',
            'operator_id',
            'mis_medrecord_id',

            'start_datetime',
            'time_crew',
            'time_depart',
            'time_patient',
            'time_transport',
            'time_hospital',
            'end_datetime',

            'patient',
            'patient_address',
            'call_address',
            'patient_address_src',
            'patient_document',

            'noresult',
            'mr_result',
            'is_hospital_record',
            'is_diagnosis_record',

            'mr_comment',
            'date_modified',
            'timestamp'
        ]

    def to_internal_value(self, data):
        logging.info("MedRecordSerializer: To to_internal_value")
        ret = OrderedDict()
        errors = OrderedDict()
        # operator_id required
        # if not 'operator_id' in data:
        operator_id = data.get('operator_id', None)
        if not operator_id:
            error = "Error: operator_id is required"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        else:
            # operator_id must be in Staff list
            operator_id = data.get('operator_id', False)
            staff_q = Staff.objects.filter(mis_id=data['mis_id'], mis_staff_id=operator_id)
            if not staff_q.exists():
                error = "Error: operator_id must be in staff list"
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
            data['operator_id'] = staff_q.first().id

        patient_address_src = data.get('patient_address_src', None)
        if patient_address_src:
            patient_address_src_qs = AddrDocType.objects.filter(name=patient_address_src)
            if patient_address_src_qs.exists():
                patient_address_src_obj = patient_address_src_qs.first()
                data['patient_address_src'] = patient_address_src_obj.id
            else:
                error = f"Bad patient_address_src: {data['patient_address_src']}"
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        else:
            data['patient_address_src'] = 1     # Невідомо

        noresult = data.get('noresult', None)
        if noresult:
            noresult_qs = NoResult.objects.filter(name=noresult)
            if noresult_qs.exists():
                noresult_obj = noresult_qs.first()
                data['noresult'] = noresult_obj.id
            else:
                error = f"Bad noresult: {data['noresult']}"
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        else:
            data['noresult'] = 1  # Результативний

        hospital = data.get('hospital', None)
        if hospital:
            data['is_hospital_record'] = True
        else:
            data['is_hospital_record'] = False

        if not self.instance:
            call_card_id = data.get('call_card_id', False)
            if not call_card_id:
                error = "Error: call_card_id is required!"
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
            else:
                #call_card_id = data.get('call_card_id', False)
                call_card_qs = CallCard.objects.filter(call_card_id=call_card_id)
                if call_card_qs.exists():
                    call_card_obj = call_card_qs.first()
                    if int(call_card_obj.mis_id.id) != int(data['mis_id']):
                        error = f"CallCard [{data['call_card_id']}] doesnt belong to MIS [{data['mis_id']}]"
                        logging.error(error)
                        raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
                    data['callcard'] = call_card_obj.id
                    if call_card_obj.crew_id:
                        data['crew'] = call_card_obj.crew_id.id
                    else:
                        error = f"MedRecord: No crew in related CallCard {call_card_obj.call_card_id}"
                        logging.error(error)
                        raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
                else:
                    error = f"Bad call_card_id: {data['call_card_id']}"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})

        fields = self._writable_fields
        for field in fields:
            validate_method = getattr(self, 'validate_' + field.field_name, None)
            primitive_value = data.get(field.source_attrs[0], False)
            if primitive_value:
                try:
                    validated_value = field.run_validation(primitive_value)
                    if validate_method is not None:
                        validated_value = validate_method(validated_value)
                except ValidationError as exc:
                    errors[field.field_name] = exc.detail
                except DjangoValidationError as exc:
                    errors[field.field_name] = get_error_detail(exc)
                except SkipField:
                    pass
                else:
                    set_value(ret, field.source_attrs, validated_value)

        if errors:
            raise ValidationError(errors)

        #ret = super().to_internal_value(data=data)
        return ret

    def to_representation(self, instance):
        mr_data = super().to_representation(instance)
        del mr_data['id']
        del mr_data['mis_id']
        del mr_data['callcard']

        mr_data['operator_id'] = Staff.objects.get(id=mr_data['operator_id']).mis_staff_id
        if mr_data['crew']:
            crew_obj = Crew.objects.get(id=mr_data['crew'])
            mr_data['crew'] = crew_obj.crew_id
        mr_data['noresult'] = NoResult.objects.get(id=mr_data['noresult']).name
        mr_data['patient_address_src'] = AddrDocType.objects.get(id=mr_data['patient_address_src']).name

        return mr_data

    def update(self, instance, validated_data):
        # logging.info(f'MedRecordSerializer: update()')
        validated_data = self.doMRCPC(validated_data=validated_data, instance=instance)
        # validated_data.pop("start_datetime")

        instance = super().update(instance=instance, validated_data=validated_data)
        return instance

    def create(self, validated_data):
        if 'id' in validated_data:
            return None

        validated_data = self.doMRCPC(validated_data=validated_data)
        with transaction.atomic():
            validated_data['med_record_id'] = self.createMRSlug()
            cc_obj = MedRecord.objects.create(**validated_data)

        return cc_obj

    def createMRSlug(self):
        today = date.today()
        if not MedRecordSlug.objects.filter(id=1).exists():
            slugdate = MedRecordSlug()
            slugdate.save()
        else:
            slugdate = MedRecordSlug.objects.get(id=1)

        if slugdate.date_modified.date() != today:
            logging.info("Next Day. Have to flush sequence")
            val = get_next_value('medrecord_number')
            number_int = get_next_value('medrecord_number', reset_value=(val + 1))
            logging.info(f"val: {val}, val1: {number_int}")
        else:
            #print("The same date. Keep sequence")
            number_int = get_next_value('medrecord_number')

        slugdate.save()

        number_str = str(number_int).zfill(6)
        slug = f'MR-{today.isoformat()}-{number_str}'
        return slug

    def doMRCPC(self, validated_data, instance=None):
        d_patient = validated_data.get('patient', False)
        if d_patient:
            #print('patient in validated_data')
            if instance is not None:
                if instance.patient is not None:
                    #print('instance exists')
                    patient_obj = super().update(instance.patient, d_patient)
                    validated_data['patient'] = patient_obj
                else:
                    #print('Creating patient instance1')
                    patient_obj = Patient.objects.create(**d_patient)
                    validated_data['patient'] = patient_obj
            else:
                #print('Creating patient instance2')
                patient_obj = Patient.objects.create(**d_patient)
                validated_data['patient'] = patient_obj

        d_complain = validated_data.get('complain', False)
        if d_complain:
            #print('complain in validated_data')
            if instance is not None:
                if instance.complain is not None:
                    #print('instance exists')
                    complain_obj = super().update(instance.complain, d_complain)
                    validated_data['complain'] = complain_obj
                else:
                    #print('Creating complain instance1')
                    complain_obj = Complain.objects.create(**d_complain)
                    validated_data['complain'] = complain_obj
            else:
                #print('Creating complain instance2')
                complain_obj = Complain.objects.create(**d_complain)
                validated_data['complain'] = complain_obj

        d_patient_address = validated_data.get('patient_address', False)
        if d_patient_address:
            if instance is not None:
                if instance.patient_address is not None:
                    patient_address_obj = super().update(instance.patient_address, d_patient_address)
                    validated_data['patient_address'] = patient_address_obj
                else:
                    patient_address_obj = Address.objects.create(**d_patient_address)
                    validated_data['patient_address'] = patient_address_obj
            else:
                patient_address_obj = Address.objects.create(**d_patient_address)
                validated_data['patient_address'] = patient_address_obj

        d_call_address = validated_data.get('call_address', False)
        if d_call_address:
            if instance is not None:
                if instance.call_address is not None:
                    call_address_obj = super().update(instance.call_address, d_call_address)
                    validated_data['call_address'] = call_address_obj
                else:
                    call_address_obj = Address.objects.create(**d_patient_address)
                    validated_data['call_address'] = call_address_obj
            else:
                call_address_obj = Address.objects.create(**d_call_address)
                validated_data['call_address'] = call_address_obj

        d_mr_result = validated_data.get('mr_result', False)
        if d_mr_result:
            if instance is not None:
                if instance.mr_result is not None:
                    mr_result_obj = super().update(instance.mr_result, d_mr_result)
                    validated_data['mr_result'] = mr_result_obj
                else:
                    mr_result_obj = MRResult.objects.create(**d_mr_result)
                    validated_data['mr_result'] = mr_result_obj
            else:
                mr_result_obj = MRResult.objects.create(**d_mr_result)
                validated_data['mr_result'] = mr_result_obj

        return validated_data
