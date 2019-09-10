import sys
import traceback
import logging
from rest_framework import serializers
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.settings import api_settings
from mis.models import Mis, Facility, SysAddress, Staff, Cars
from mis.models import FacilityType, LocationType, AddressType
from mis.models import StaffQualification, StaffTitle
from mis.models import CarType, CarStatus, CarOwner


class CarSerializer(serializers.ModelSerializer):

    class Meta:
        model = Cars
        fields = [
            'id',
            'mis_id',
            'mis_car_id',
            'facility_id',
            'mis_facility_id',
            'car_model',
            'car_type',
            'year_made',
            'year_start',
            'gov_number',
            'car_status',
            'car_owner',
            'car_field_number',
            'car_comment',
            'is_active',
            'date_modified',
        ]

    # def validate_car_field_number(self, value):
    #     logging.warning(f'validate_car_field_number')
    #     #traceback.print_stack()
    #     return value[:23]

    def to_internal_value(self, data):
        #logging.info("CarSerializer: to_internal_value")
        mis_facility_id = data.get('mis_facility_id', False)
        if mis_facility_id:
            facility_q = Facility.objects.filter(mis_id=data['mis_id'],
                                                 mis_facility_id=mis_facility_id)
            if facility_q.exists():
                data['facility_id'] = facility_q.first().id
            else:
                error = "CarSerializer. Cars mis_facility_id does not exist"
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
                # return HttpResponse(error, status=status.HTTP_400_BAD_REQUEST)
        else:
            error = "CarSerializer. Cars mis_facility_id required"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})

        car_type = data.get('car_type', False)
        if car_type:
            if (type(car_type) == int) | car_type.isdigit():
                data['car_type'] = car_type
            else:
                q_ct = CarType.objects.filter(cartype_name=car_type)
                if q_ct.exists():
                    data['car_type'] = q_ct.first().id
                else:
                    error = f"Error: car_type is unknown: {car_type}"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: error})
        else:
            data['car_type'] = None

        car_owner = data.get('car_owner', False)
        if car_owner:
            if (type(car_owner) == int) | car_owner.isdigit():
                data['car_owner'] = car_owner
            else:
                q_co = CarOwner.objects.filter(carowner_name=car_owner)
                if q_co.exists():
                    data['car_owner'] = q_co.first().id
                else:
                    error = f"Error: car_owner is unknown: {car_owner}"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: error})
        else:
            data['car_owner'] = None

        car_status = data.get('car_status', False)
        if car_status:
            if (type(car_status) == int) | car_status.isdigit():
                data['car_status'] = car_status
            else:
                q_cs = CarStatus.objects.filter(carstatus_name=car_status)
                if q_cs.exists():
                    data['car_status'] = q_cs.first().id
                else:
                    error = f"Error: car_status is unknown: {car_status}"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: error})
        else:
            data['car_status'] = None

        car_field_number_v = data.get('car_field_number', None)
        if car_field_number_v:
            data['car_field_number'] = car_field_number_v[:31]

        valid_data = super().to_internal_value(data=data)

        return valid_data

    def to_representation(self, instance):
        #logging.info("CarSerializer: to_representation")
        car_data = super().to_representation(instance)
        #del cc_data['id']
        #del cc_data['mis_id']
        # if cc_data['address']:
        #     address_obj = SysAddress.objects.get(id=cc_data['address'])
        #     cc_data['address'] = SysAddressSerializer(address_obj).data

        if car_data['car_type']:
            car_data['car_type'] = CarType.objects.get(id=car_data['car_type']).cartype_name
        if car_data['car_owner']:
            car_data['car_owner'] = CarOwner.objects.get(id=car_data['car_owner']).carowner_name
        if car_data['car_status']:
            car_data['car_status'] = CarStatus.objects.get(id=car_data['car_status']).carstatus_name
        return car_data


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = [
            'id',
            'mis_id',
            'mis_staff_id',
            'facility_id',
            'mis_facility_id',
            'first_name',
            'family_name',
            'middle_name',
            'birthday',
            'sex',
            'phone',
            'title',
            'qualification',
            'experience_total',
            'experience_field',
            'ipn',
            'passport',
            'sertificate',
            'last_qualification_date',
            'is_active',
            'staff_comment',
            'date_modified',
        ]

    def to_internal_value(self, data):
        #logging.info("StaffSerializer: to_internal_value")

        # dealing with mis_facility
        mis_facility_id = data.get('mis_facility_id', False)
        if mis_facility_id:
            facility_q = Facility.objects.filter(mis_id=data['mis_id'],
                                                 mis_facility_id=mis_facility_id)
            if facility_q.exists():
                data['facility_id'] = facility_q.first().id
            else:
                error = "StaffCreateView POST. Staff mis_facility_id does not exist"
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        else:
            error = "StaffCreateView POST. Staff mis_facility_id required"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
            # return HttpResponse(error, status=status.HTTP_400_BAD_REQUEST)
        staff_title = data.get('title', False)
        if staff_title:
            if (type(staff_title) == int) | staff_title.isdigit():
                data['title'] = staff_title
            else:
                q_t = StaffTitle.objects.filter(title_name=staff_title)
                if q_t.exists():
                    data['title'] = q_t.first().id
                else:
                    error = f"Error: staff_title is unknown: {staff_title}"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        else:
            data['title'] = None

        staff_qualification = data.get('qualification', False)
        if staff_qualification:
            if (type(staff_qualification) == int) | staff_qualification.isdigit():
                data['qualification'] = staff_qualification
            else:
                q_q = StaffQualification.objects.filter(qualification_name=staff_qualification)
                if q_q.exists():
                    data['qualification'] = q_q.first().id
                else:
                    error = f'Error: location_type is unknown: {staff_qualification}'
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        else:
            data['qualification'] = None

        valid_data = super().to_internal_value(data=data)
        return valid_data

    def to_representation(self, instance):
        #logging.info("StaffSerializer: to_representation")
        sc_data = super().to_representation(instance)

        if sc_data['qualification']:
            qn = StaffQualification.objects.get(id=sc_data['qualification']).qualification_name
            sc_data['qualification'] = qn

        if sc_data['title']:
            sc_data['title'] = StaffTitle.objects.get(id=sc_data['title']).title_name

        return sc_data

    def validate_phone(self, value):
        if value == None:
            return None
        if len(value) == 0:
            return None
        else:
            return value

    def validate_sex(self, value):
        # if value == None:
        #     return None
        # if len(value) == 0:
        #     return None
        # else:
        if value in ('Ч', 'Ж'):
            return value
        else:
            raise serializers.ValidationError("Field sex must be 'Ч/Ж' range")

    def validate_first_name(self, value):
        if value == None:
            return None
        if len(value) == 0:
            return None
        else:
            return value

    def validate_family_name(self, value):
        if value == None:
            return None
        if len(value) == 0:
            return None
        else:
            return value

    def validate_middle_name(self, value):
        if value == None:
            return None
        if len(value) == 0:
            return None
        else:
            return value

    def validate_experience_total(self, value):
        if value == None:
            return None
        if len(value) == 0:
            return None
        else:
            return value

    def validate_experience_field(self, value):
        if value == None:
            return None
        if len(value) == 0:
            return None
        else:
            return value

    def validate_ipn(self, value):
        if value == None:
            return None
        if len(value) == 0:
            return None
        else:
            return value

    def validate_passport(self, value):
        if value == None:
            return None
        if len(value) == 0:
            return None
        else:
            return value

    def validate_sertificate(self, value):
        if value == None:
            return None
        if len(value) == 0:
            return None
        else:
            return value

    def validate_staff_comment(self, value):
        if value == None:
            return None
        if len(value) == 0:
            return None
        else:
            return value


class SysAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysAddress
        fields = [
            'id',
            'index',
            'district',
            'city',
            'street',
            'building',
            'apartment',
            'location_type',
            'address_type',
            'longitude',
            'latitude',
            'address_comment',
            'date_modified',
        ]

    def to_internal_value(self, data):
        #logging.info("SysAddressSerializer: to_internal_value")
        location_type = data.get('location_type', False)
        if location_type:
            if location_type.isdigit():
                data['location_type'] = location_type
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
            if address_type.isdigit():
                data['address_type'] = address_type
            else:
                q_at = AddressType.objects.filter(addresstype_name=address_type)
                if q_at.exists():
                    data['address_type'] = q_at.first().id
                else:
                    error = f"Error: address_type is unknown: {address_type}"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        else:
            data['address_type'] = None

        valid_data = super().to_internal_value(data=data)
        return valid_data

    def to_representation(self, instance):
        #logging.info("SysAddressSerializer: to_representation")
        cc_data = super().to_representation(instance)

        if cc_data['address_type']:
            cc_data['address_type'] = AddressType.objects.get(id=cc_data['address_type']).addresstype_name

        if cc_data['location_type']:
            cc_data['location_type'] = LocationType.objects.get(id=cc_data['location_type']).locationtype_name

        return cc_data


class FacilitySerializer(serializers.ModelSerializer):
    address = SysAddressSerializer()

    class Meta:
        model = Facility
        fields = [
            'id',
            'mis_id',
            'mis_facility_id',
            'name',
            'short_name',
            'address',
            'facility_contact',
            'facility_phone',
            'is_active',
            'facility_parent',
            'facility_type',
            'facility_comment',
            'date_modified',
        ]

    def to_internal_value(self, data):
        facility_type = data.get('facility_type', False)
        if facility_type:
            if (type(facility_type) == int) | facility_type.isdigit():
                data['facility_type'] = facility_type
            else:
                q_ft = FacilityType.objects.filter(facilitytype_name=facility_type)
                if q_ft.exists():
                    data['facility_type'] = q_ft.first().id
                else:
                    error = f"Error: facility_type is unknown: {facility_type}"
                    logging.error(error)
                    raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: error})

        valid_data = super().to_internal_value(data=data)
        return valid_data

    def to_representation(self, instance):
        #logging.info("FacilitySerializer: to_representation")
        cc_data = super().to_representation(instance)
        #del cc_data['id']
        #del cc_data['mis_id']
        # if cc_data['address']:
        #     address_obj = SysAddress.objects.get(id=cc_data['address'])
        #     cc_data['address'] = SysAddressSerializer(address_obj).data

        if cc_data['facility_type']:
            cc_data['facility_type'] = FacilityType.objects.get(id=cc_data['facility_type']).facilitytype_name

        return cc_data

    def update(self, instance, validated_data):
        # logging.info(f'FacilitySerializer: update()')
        d_address = validated_data.get('address', False)
        if d_address:
            address_obj = super().update(instance.address, d_address)
            validated_data['address'] = address_obj
        else:
            error = f"update Error: This should never EVER happend"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        instance = super().update(instance, validated_data)
        return instance

    def create(self, validated_data):
        # logging.info(f'FacilitySerializer: create()')
        d_address = validated_data.get('address', False)
        if d_address:
            address_obj = SysAddress.objects.create(**d_address)
            validated_data['address'] = address_obj
        else:
            error = f"update Error: This should never EVER happend"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})

        instance = super().create(validated_data)
        return instance

    def validate_short_name(self, value):
        if value == None:
            return None
        if len(value) == 0:
            #logging.error("Short_name: is_empty")
            return None
        else:
            return value


class CMisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mis
        fields = [
            'id',
            'mis_user',
            'mis_name',
            'mis_type',
            'mis_facility',
            'mis_comment',
        ]


class MisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mis
        fields = [
            'id',
            'mis_user',
            'mis_name',
            'mis_type',
            'mis_facility',
            'mis_comment',
            'mis_heartbeat',
            'date_modified',
            'timestamp',
        ]
        read_only_fields = ['id', 'mis_user', 'mis_name', 'mis_comment', 'mis_type']

    def validate_mis_name(self, value):  # Make Mis name uiquie
        logging.info("Validating MIS name: {}".format(value))
        qs = Mis.objects.filter(mis_name__iexact=value)
        if self.instance:
            qs = qs.exclude(id=self.instance.id)
        if qs.exists():
            error = f"MisSerializer: MIS name must be unique"
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        return value

    def validate_mis_heartbeat(self, value):
        if value:
            timedif = abs(timezone.now() - value)
            if timedif.seconds > 5:
                logging.info(f'Time difference: {timedif.seconds}, but accepting')
            if timedif.seconds > 10:
                error = f"MisSerializer: validate_mis_heartbeat: Diff:{timedif.seconds}sec. Limit 10 sec."
                logging.error(error)
                raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        else:
            error = f'MisSerializer: validate_mis_heartbeat: mis_heartbeat MUST be provided'
            logging.error(error)
            raise ValidationError({api_settings.NON_FIELD_ERRORS_KEY: [error]})
        return value
