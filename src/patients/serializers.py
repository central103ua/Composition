import time
import logging
from rest_framework import serializers
from django.utils import timezone
#from dateutil.parser import parse
#from heartbeat.models import HeartBeat, Intercall
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.settings import api_settings
from .models import Patient, Address, Complain
from .models import ChiefComplain, PatientState, BreathState, ConscState, Situation
from .models import State, District
from mis.models import LocationType, AddressType

# Non-field imports, but public API
from rest_framework.fields import (  # NOQA # isort:skip
    CreateOnlyDefault, CurrentUserDefault, SkipField, empty
)


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
            'id',
            'name',
            'first_name',
            'family_name',
            'middle_name',
            'age',
            'sex',
            'phone',
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        del ret['id']
        return ret

    def validate_sex(self, value):
        #logging.info("Validating SEX!")
        if value in ('Ч', 'Ж', 'Не відомо'):
            return value
        else:
            raise serializers.ValidationError("Field sex must be 'Ч/Ж/Не відомо' range")


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id',
            'index',
            'district',
            'distr',
            'city',
            'street',
            'building',
            'apartment',
            'location_type',  # місто/село
            'address_type',  # квартира/офіс/будинок/завод
            'longitude',
            'latitude',
            'date_modified'
        ]

    def validate_building(self, value):
        if value == None:
            return None
        if len(value) == 0:
            return None
        else:
            return value

    def to_internal_value(self, data):
        logging.info("AddressSerializer: to_internal_value")
        location_type = data.get('location_type', False)
        if location_type:
            if type(location_type) == int:
                data['location_type'] = location_type
            elif location_type.isdigit():
                data['location_type'] = int(location_type)
            else:
                q_lt = LocationType.objects.filter(locationtype_name=location_type)
                if q_lt.exists():
                    data['location_type'] = q_lt.first().id
                else:
                    error = f"Error: location_type is unknown: {location_type}"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        else:
            data['location_type'] = None

        address_type = data.get('address_type', False)
        if address_type:
            if type(address_type) == int:
                # logging.info(f"AddressType is INT {address_type}")
                data['address_type'] = address_type
            elif address_type.isdigit():
                logging.info(f"AddressType isdigit() {address_type}")
                data['address_type'] = int(address_type)
            else:
                at_qs = AddressType.objects.filter(addresstype_name=address_type)
                if at_qs.exists():
                    data['address_type'] = at_qs.first().id
                else:
                    error = f"Error: address_type is unknown: {address_type}"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        else:
            data['address_type'] = None

        district_s = data.get('district', None)
        if district_s:
            #logging.warning(f'original district_s: {district_s}')
            space_n = district_s.find(" ")
            # logging.warning(f'space_n: {space_n}')
            if space_n != -1:
                district_s = district_s[:space_n]
            # logging.warning(f'real district_s: {district_s}')
            district_qs = District.objects.filter(name__iexact=district_s)
            if district_qs.exists():
                data['distr'] = district_qs.first().id
                #logging.warning(f'AddressSerializer:: found District {district_s}, id={data["distr"]}')
            else:
                data['distr'] = None
                logging.warning(f'AddressSerializer:: District {district_s} not found')
        # else:
        #     logging.warning(f'AddressSerializer:: district is empty')
        #     data['distr'] = None

        valid_data = super().to_internal_value(data=data)
        return valid_data

    # Remove null fields
    def to_representation(self, instance):
        ret = super().to_representation(instance)

        if ret['address_type']:
            ret['address_type'] = AddressType.objects.get(id=ret['address_type']).addresstype_name

        if ret['location_type']:
            ret['location_type'] = LocationType.objects.get(id=ret['location_type']).locationtype_name

        # Delete NULL and id
        del ret['id']
        fields = self._writable_fields
        for field in fields:
            value = ret.get(field.source_attrs[0], False)
            # print(f'{field.field_name}: {value}')
            if value == None:
                del ret[field.field_name]

        return ret


class ComplainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complain
        fields = [
            'id',
            'complain1',
            'complain2',
            'complain3',
            'complain4',
            'code_complain',
            'chief_complain',
            'breath_state',
            'consc_state',
            'patient_state',
            'code_sit'
        ]

    def to_internal_value(self, data):
        logging.info("ComplainSerializer: to_internal_value")
        code_complain = data.get('code_complain', None)
        if code_complain:
            cc, pb, pc, des = self._validate_code_complain(code_complain)
            data['complain1'] = cc.name
            data['complain2'] = f'{pb.name}, {pc.name}'
            data['complain3'] = des.name
            data['chief_complain'] = cc.id
            data['breath_state'] = pb.id
            data['consc_state'] = pc.id
            data['patient_state'] = des.id
        code_sit = data.get('code_sit', None)
        if code_sit:
            code_sit_int = int(code_sit)
            code_sit_qs = Situation.objects.filter(id=code_sit_int)
            if code_sit_qs.exists():
                code_sit_obj = code_sit_qs.first()
                # logging.info(f'Situation: {code_sit_obj.name}')
            else:
                error = f"Wrong Situation in code_sit: {code_sit}"
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
            data['complain4'] = code_sit_obj.name
        ret = super().to_internal_value(data=data)
        return ret

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        code_sit = ret.get('code_sit', None)
        if code_sit:
            ret['code_sit'] = f'{code_sit}'

        if ret.get('chief_complain', None):
            del ret['chief_complain']
        if ret.get('breath_state', None):
            del ret['breath_state']
        if ret.get('consc_state', None):
            del ret['consc_state']

        # Delete NULL and id
        del ret['id']
        fields = self._writable_fields
        for field in fields:
            value = ret.get(field.source_attrs[0], False)
            # print(f'{field.field_name}: {value}')
            if value == None:
                del ret[field.field_name]

        return ret

    def _validate_code_complain(self, code_complain):
        try:
            cc, ps, des = code_complain.split('-', 3)
            cc_int = int(cc)
            des_int = int(des)
            bs = ps[:2]
            cs = ps[2:]
        except ValueError:
            error = f"Wrong code_complain: {code_complain}"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        # Chief Complain
        cc_qs = ChiefComplain.objects.filter(id=cc_int)
        if cc_qs.exists():
            cc_obj = cc_qs.first()
            # logging.info(f"ChiefComplain: {cc_obj.name}")
        else:
            error = f"Wrong ChiefComplain in code_complain: {code_complain}"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})

        # Patient state
        state_code = f'{cc_obj.id}.{des_int}'
        des_qs = PatientState.objects.filter(code=state_code)
        if des_qs.exists():
            des_obj = des_qs.first()
            # logging.info(f"PatientState: {des_obj.name}")
        else:
            error = f"Wrong PatientState in code_complain: {code_complain}"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})

        bs_qs = BreathState.objects.filter(code=bs)
        if bs_qs.exists():
            bs_obj = bs_qs.first()
            # logging.info(f"BreathSate: {bs_obj.name}")
        else:
            error = f"Wrong BreathSate in code_complain: {code_complain}"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})

        cs_qs = ConscState.objects.filter(code=cs)
        if cs_qs.exists():
            cs_obj = cs_qs.first()
            # logging.info(f"ConscState: {cs_obj.name}")
        else:
            error = f"Wrong ConscState in code_complain: {code_complain}"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})

        return cc_obj, bs_obj, cs_obj, des_obj
