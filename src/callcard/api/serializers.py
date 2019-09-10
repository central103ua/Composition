import json
import time
import logging
import random
from datetime import date, datetime
from collections import Mapping, OrderedDict
from django.utils import timezone
from django.conf import settings
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.fields import get_error_detail, set_value
from rest_framework.settings import api_settings
from rest_framework.fields import (
    CreateOnlyDefault, CurrentUserDefault, SkipField, empty
)

from django.db import transaction
from sequences import get_next_value

from callcard.models import CallCard, CallStations, CallResult, CallPriority, CallRecord, CallCardSlug, CCIntercall
from patients.serializers import PatientSerializer, AddressSerializer, ComplainSerializer
from patients.models import Patient, Address, Complain
from mis.models import Mis, Staff
from crew.models import Crew


class CCIntercallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CCIntercall
        fields = [
            'mis_to',
            'mis_from',
            'related_cc',
        ]

    # def to_internal_value(self, data):
    #     logging.info("CCIntercallSerializer: to_internal_value")
    #     ret = super().to_internal_value(data=data)
    #     return ret


class CallRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallRecord
        fields = [
            'id',
            'card_id',
            'mis_id',
            'call_record_seq',
            'start_datetime',
            'end_datetime',
            'operator_id',
            'call_station',
            'crew_id',
            'call_record_comment'
        ]

    def to_internal_value(self, data):
        #logging.info("CallRecordSerializer: To to_internal_value")
        c_c = data.get('call_record_comment', None)
        if c_c:
            if type(c_c) == str:
                if len(c_c) > 254:
                    data['call_record_comment'] = c_c[:254]
                    logging.warning("Stripping call_record_comment")

        ret = super().to_internal_value(data=data)
        return ret


class CallCardSerializer(serializers.ModelSerializer):
    complain = ComplainSerializer(allow_null=True)
    patient = PatientSerializer(allow_null=True)
    call_address = AddressSerializer(allow_null=True)
    intercall = CCIntercallSerializer(allow_null=True)

    class Meta:
        model = CallCard
        fields = [
            'id',
            'call_card_id',
            'mis_id',
            'mis_user',
            'operator_id',
            'mis_call_card_id',
            'caller_number',
            'start_datetime',
            'end_datetime',
            'call_priority',
            'call_result',
            'call_station',
            'complain',
            'patient',
            'call_address',
            'intercall',
            'crew_id',
            'call_comment',
            'date_modified',
            'timestamp'
        ]
        #read_only_fields = ["start_datetime"]

    def to_internal_value(self, data):
        logging.info("CallCardSerializer: To to_internal_value")
        ret = OrderedDict()
        errors = OrderedDict()

        if not 'mis_id' in data:
            mis_obj = Mis.objects.get(mis_user=data['mis_user'])
            data['mis_id'] = mis_obj.id
            data['mis_user'] = mis_obj.mis_user.id
        data['start_datetime'] = data.get('start_datetime', timezone.now().isoformat())
        try:
            instance_start = datetime.fromisoformat(data['start_datetime'])
        except Exception as ex:
            logging.error(f"CallCardSerializer:: invalid start_datetime: {data['start_datetime']}")
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [ex]})

        data['call_station'] = data.get('call_station', "1")
        if data['start_datetime'] == "":
            error = "start_date_time may not be an empty string"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})

        crew_id = data.get('crew_id', False)
        if crew_id:
            crew_q = Crew.objects.filter(mis_id=data['mis_id'],
                                         crew_id=data['crew_id'])
            if crew_q.exists():
                crew_obj = crew_q.first()
                if int(crew_obj.mis_id.id) != int(data['mis_id']):
                    error = f"Crew [{data['crew_id']}] doesnt belong to MIS [{data['mis_id']}]"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
                data['crew_id'] = crew_obj.id
            else:
                error = f"Bad mis_id:crew_id: {data['mis_id']}: {data['crew_id']}"
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})

        call_station = data.get('call_station', "1")
        if (type(call_station) == int) or call_station.isdigit():
            station_obj = CallStations.objects.get(id=call_station)
            if station_obj == None:
                error = f"Bad callStation: {call_station}"
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
            data['call_station'] = station_obj.id
        else:
            station_obj = CallStations.objects.filter(station_name=call_station).first()
            if station_obj == None:
                error = f"Bad callStation: {call_station}"
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
            data['call_station'] = station_obj.id
        call_priority = data.get('call_priority', False)
        if call_priority:
            if (type(call_priority) == int) or call_priority.isdigit():
                priority_obj = CallPriority.objects.get(id=call_priority)
                if priority_obj == None:
                    error = f"Bad call_priority: {call_priority}"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
                data['call_priority'] = priority_obj.id
            else:
                priority_obj = CallPriority.objects.filter(priority_name=call_priority).first()
                if priority_obj == None:
                    error = f"Bad call_priority: {call_priority}"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
                data['call_priority'] = priority_obj.id

        call_result = data.get('call_result', False)
        if call_result:
            if (type(call_result) == int) or call_result.isdigit():
                result_obj = CallResult.objects.get(id=call_result)
                if result_obj == None:
                    error = f"Bad call_result: {call_result}"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
                data['call_result'] = result_obj.id
            else:
                result_obj = CallResult.objects.filter(result_name=call_result).first()
                if result_obj == None:
                    error = f"Bad call_result: {call_result}"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
                data['call_result'] = result_obj.id

        # Comments to CallCard only by Operator103
        c_c = data.get('call_comment', None)
        if c_c:
            if data['call_station'] != 2:
                data.pop('call_comment')
            else:
                c_c = str(c_c)
                if len(c_c) > 254:
                    logging.warning("Stripping call_comment")
                    data['call_comment'] = c_c[:254]
                else:
                    data['call_comment'] = c_c

        # end_datetime is required
        end_datetime = data.get('end_datetime', None)
        if not end_datetime:
            error = "Error: end_datetime is required"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        # operator_id required
        operator_id = data.get('operator_id', None)
        if not operator_id:
            error = "Error: operator_id is required"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        # operator_id must be in Staff list
        staff_qs = Staff.objects.filter(mis_id=data['mis_id'], mis_staff_id=operator_id)
        if not staff_qs.exists():
            error = "Error: operator_id must be in staff list"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        # Only Operator103 goes to CallCard
        operator_id_pk = staff_qs.first().id
        if data['call_station'] <= 2 | (not self.instance):
            data['operator_id'] = operator_id_pk
        else:
            data.pop('operator_id')

        # print(f'data[start_datetime]: {data["start_datetime"]}')
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

        data['operator_id'] = operator_id_pk

        # Check if already Archive
        if self.instance and self.instance.call_station:
            if self.instance.call_station.station_name == "Архів":
                cc_slug = ret.get('call_card_id', None)
                logging.warning(f"CallCardSerializer:: The card# {cc_slug} is in Archive already. ")
                callrecord_start = datetime.fromisoformat(data['start_datetime'])
                logging.warning(f'callrecord_start : {callrecord_start.isoformat()}')
                logging.warning(f'callcard_end_time: {self.instance.end_datetime.isoformat()}')
                # logging.warning("CallCardSerializer:: puting call_station to Archive back")
                # ret['call_station'] = CallStations.objects.get(station_name="Архів")
                if callrecord_start < self.instance.end_datetime:
                    logging.warning("CallCardSerializer:: puting call_station to Archive back")
                    ret['call_station'] = CallStations.objects.get(station_name="Архів")

        #ret = super().to_internal_value(data=data)
        # print(f'ret [start_datetime]: {ret["start_datetime"]}')
        # print(ret)
        return ret

    def to_representation(self, instance):
        cc_data = super().to_representation(instance)
        del cc_data['id']
        del cc_data['mis_user']
        del cc_data['mis_id']

        if cc_data['crew_id']:
            crew_obj = Crew.objects.get(id=cc_data['crew_id'])
            cc_data['crew_id'] = crew_obj.crew_id

        # CallStation reverse presentation
        station_obj = CallStations.objects.get(id=cc_data['call_station'])
        cc_data['call_station'] = station_obj.station_name

        # CallResult reverse presentation
        if cc_data['call_result']:
            result_obj = CallResult.objects.get(id=cc_data['call_result'])
            cc_data['call_result'] = result_obj.result_name

        # CallPriority reverse presentation
        priority_obj = CallPriority.objects.get(id=cc_data['call_priority'])
        cc_data['call_priority'] = priority_obj.priority_name

        cc_data['operator_id'] = Staff.objects.get(id=cc_data['operator_id']).mis_staff_id

        # if not cc_data['intercall']:
        #     del cc_data['intercall']

        return cc_data

    def update(self, instance, validated_data):
        # logging.info(f'CallCardSerializer: update()')
        validated_data = self.doCPC(validated_data=validated_data, instance=instance)
        validated_data.pop("start_datetime")

        instance = super().update(instance=instance, validated_data=validated_data)
        return instance

    def create(self, validated_data):
        if 'id' in validated_data:
            return None

        validated_data = self.doCPC(validated_data=validated_data)
        with transaction.atomic():
            validated_data['call_card_id'] = self.createCCSlug()
            cc_obj = CallCard.objects.create(**validated_data)

        return cc_obj

    def createCCSlug(self):
        today = date.today()
        if not CallCardSlug.objects.filter(id=1).exists():
            slugdate = CallCardSlug()
            slugdate.save()
        else:
            slugdate = CallCardSlug.objects.get(id=1)

        if slugdate.date_modified.date() != today:
            val = get_next_value('callCard_number')
            number_int = get_next_value('callCard_number', reset_value=(val + 1))
        else:
            number_int = get_next_value('callCard_number')

        slugdate.save()

        number_str = str(number_int).zfill(6)
        slug = f'ER-{today.isoformat()}-{number_str}'
        return slug

    def doCPC(self, validated_data, instance=None):
        d_intercall = validated_data.get('intercall', False)
        if d_intercall:
            if instance is not None:
                if instance.intercall is not None:
                    intercall_obj = super().update(instance.intercall, d_intercall)
                    validated_data['intercall'] = intercall_obj
                else:
                    intercall_obj = CCIntercall.objects.create(**d_intercall)
                    validated_data['intercall'] = intercall_obj
            else:
                intercall_obj = CCIntercall.objects.create(**d_intercall)
                validated_data['intercall'] = intercall_obj
        d_patient = validated_data.get('patient', False)
        if d_patient:
            if instance is not None:
                if instance.patient is not None:
                    patient_obj = super().update(instance.patient, d_patient)
                    validated_data['patient'] = patient_obj
                else:
                    patient_obj = Patient.objects.create(**d_patient)
                    validated_data['patient'] = patient_obj
            else:
                patient_obj = Patient.objects.create(**d_patient)
                validated_data['patient'] = patient_obj

        d_complain = validated_data.get('complain', False)
        if d_complain:
            if instance is not None:
                if instance.complain is not None:
                    complain_obj = super().update(instance.complain, d_complain)
                    validated_data['complain'] = complain_obj
                else:
                    complain_obj = Complain.objects.create(**d_complain)
                    validated_data['complain'] = complain_obj
            else:
                complain_obj = Complain.objects.create(**d_complain)
                validated_data['complain'] = complain_obj

        d_call_address = validated_data.get('call_address', False)
        if d_call_address:
            if instance is not None:
                if instance.call_address is not None:
                    call_address_obj = super().update(instance.call_address, d_call_address)
                    validated_data['call_address'] = call_address_obj
                else:
                    call_address_obj = Address.objects.create(**d_call_address)
                    validated_data['call_address'] = call_address_obj
            else:
                call_address_obj = Address.objects.create(**d_call_address)
                validated_data['call_address'] = call_address_obj

        return validated_data
