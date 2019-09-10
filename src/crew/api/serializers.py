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
from sequences import get_next_value
from mis.models import Cars, Staff, Facility
from crew.models import Crew, CrewTeam, CrewStatus, CrewSlug, CrewDairy

# Non-field imports, but public API
from rest_framework.fields import (  # NOQA # isort:skip
    CreateOnlyDefault, CurrentUserDefault, SkipField, empty
)


class CrewDairySerializer(serializers.ModelSerializer):
    class Meta:
        model = CrewDairy
        fields = [
            'id',
            'crew_id',
            'mis_id',
            'crew_slug',
            'call_card_id',
            'call_station',
            'crew_dairy_seq',
            'crew_status',
            'is_active',
            'timestamp'
        ]


class CrewTeamSerializer(serializers.ModelSerializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        self.crew_id = kwargs.pop('crew_id', None)
        self.mis_id = kwargs.pop('mis_id', None)
        self.seq = 1
        logging.info(f'__init__: mis_id: {self.mis_id}, crew_id: {self.crew_id}')
        super(ModelSerializer, self).__init__(instance=instance, data=data, **kwargs)

    class Meta:
        model = CrewTeam
        fields = [
            'id',
            'crew_id',
            'crew_team_seq',
            'crew_staff',
            'timestamp',
        ]
        read_only_fields = ['id']

    def to_internal_value(self, data):
        logging.info("CrewTeamSerializer: To to_internal_value")
        data['crew_id'] = self.crew_id
        data['crew_team_seq'] = self.seq
        self.seq += 1
        crew_staff = data.get('crew_staff', False)
        if crew_staff:
            crew_staff_q = Staff.objects.filter(mis_id=self.mis_id,
                                                mis_staff_id=crew_staff)
            if crew_staff_q.exists():
                data['crew_staff'] = crew_staff_q.first().id
            else:
                error = "CrewSerializer. Crew crew_staff does not exist"
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        else:
            error = "CrewSerializer. Crew crew_staff required"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        ret = super().to_internal_value(data=data)
        return ret

    def to_representation(self, instance):
        logging.info("CrewTeamSerializer: to_represintation")
        crew_data = super().to_representation(instance)
        del crew_data['id']
        #del crew_data['mis_id']

        if crew_data['crew_staff']:
            crew_data['crew_staff'] = Staff.objects.get(id=crew_data['crew_staff']).mis_staff_id

        return crew_data


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = [
            'id',
            'mis_id',
            'crew_id',
            'mis_crew_id',
            'facility_id',
            'mis_facility_id',
            'car_id',
            'mis_car_id',
            'shift_start',
            'shift_end',
            'crew_status',
            'crew_comment',
            'is_active',
            'timestamp'
        ]
        read_only_fields = ['crew_id']

    def to_internal_value(self, data):
        logging.info("CrewSerializer: To to_internal_value")
        ret = OrderedDict()
        errors = OrderedDict()
        mis_car_id = data.get('mis_car_id', False)
        if self.instance == None:
            if mis_car_id:
                mis_car_q = Cars.objects.filter(mis_id=data['mis_id'],
                                                mis_car_id=mis_car_id)
                if mis_car_q.exists():
                    data['car_id'] = mis_car_q.first().id
                else:
                    error = "CrewSerializer. Crew mis_car_id does not exist"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
            else:
                crew_comment = data.get('crew_comment', None)
                if crew_comment:
                    data['car_id'] = None
                    logging.info(f'CrewSerializer: setting car_id to null')
                else:
                    error = "CrewSerializer. Crew mis_car_id or crew_comment required"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})

            mis_facility_id = data.get('mis_facility_id', False)
            if mis_facility_id:
                facility_q = Facility.objects.filter(mis_id=data['mis_id'],
                                                     mis_facility_id=mis_facility_id)
                if facility_q.exists():
                    data['facility_id'] = facility_q.first().id
                else:
                    error = "CrewSerializer. Crew mis_facility_id does not exist"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
            else:
                if self.instance == None:
                    error = "CrewSerializer. Crew mis_facility_id required"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})

        crew_status = data.get('crew_status', False)
        if crew_status:
            if crew_status.isdigit():
                data['crew_status'] = crew_status
            else:
                q_qs = CrewStatus.objects.filter(crewstatus_name=crew_status)
                if q_qs.exists():
                    data['crew_status'] = q_qs.first().id
                else:
                    error = f"Error: crew_status is unknown: {crew_status}"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: error})
        else:
            if self.instance == None:
                data['crew_status'] = None

        if self.instance == None:
            ret = super().to_internal_value(data=data)
        else:
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
                        # print(f'Setting: {field.source_attrs}:{validated_value}')
                        set_value(ret, field.source_attrs, validated_value)

            if errors:
                raise ValidationError(errors)

        return ret

    def to_representation(self, instance):
        logging.info("CrewSerializer: to_represintation")
        crew_data = super().to_representation(instance)
        del crew_data['id']
        del crew_data['mis_id']

        # if crew_data['mis_car']:
        #     crew_data['mis_car'] = Cars.objects.get(id=crew_data['mis_car']).mis_car_id
        if crew_data['crew_status']:
            crew_data['crew_status'] = CrewStatus.objects.get(id=crew_data['crew_status']).crewstatus_name

        return crew_data

    def create(self, validated_data):
        if 'id' in validated_data:
            return None

        with transaction.atomic():
            validated_data['crew_id'] = self.createSlug()
            cc_obj = Crew.objects.create(**validated_data)

        return cc_obj

    def createSlug(self):
        today = date.today()
        if not CrewSlug.objects.filter(id=1).exists():
            slugdate = CrewSlug()
            slugdate.save()
        else:
            slugdate = CrewSlug.objects.get(id=1)

        if slugdate.date_modified.date() != today:
            logging.info("Next Day. Have to flush sequence")
            val = get_next_value('crew_number')
            number_int = get_next_value('crew_number', reset_value=(val + 1))
            logging.info(f"val: {val}, val1: {number_int}")
        else:
            #print("The same date. Keep sequence")
            number_int = get_next_value('crew_number')

        slugdate.save()

        number_str = str(number_int).zfill(6)
        slug = f'CR-{today.isoformat()}-{number_str}'
        return slug
