import logging
from collections import Mapping, OrderedDict
from rest_framework import serializers
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ErrorDetail, ValidationError
from heartbeat.models import HeartBeat, Intercall, IntercallSatus
from callcard.api.serializers import CallCardSerializer


class HeartbeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeartBeat
        fields = [
            'mis_id',
            'mis_heartbeat',
            'timestamp',
        ]
        read_only_fields = ['timestamp']

    def validate(self, object):
        if "mis_heartbeat" in object:
            return object
        else:
            raise serializers.ValidationError("mis_heartbeat MUST be provided")

    def validate_mis_heartbeat(self, value):
        if value:
            timedif = abs(timezone.now() - value)
            if timedif.seconds > 10:
                logging.error(f'HeartbeatSerializer: validate_mis_heartbeat: heartbeat timedif > 10 sec.')
                logging.error(f'Time difference: {timedif.seconds}')
                raise serializers.ValidationError(f'Timestamp provided is too old. {timedif.seconds}s')
        else:
            logging.error(f'HeartbeatSerializer: validate_mis_heartbeat: mis_heartbeat MUST be provided')
            raise serializers.ValidationError("mis_heartbeat MUST be provided")
        return value


class IntercallSerializer(serializers.ModelSerializer):
    callcard = CallCardSerializer()

    class Meta:
        model = Intercall
        fields = [
            'mis_to',
            'mis_from',
            'related_cc',
            'callcard',
            'date_modified',
            'timestamp'
        ]

    def to_internal_value(self, data):
        ret = OrderedDict()
        ret['mis_to'] = data['mis_to']
        ret['mis_from'] = data['mis_from']
        ret['related_cc'] = data['related_cc']
        ret['callcard'] = data['callcard']
        status_str = data.get("status", None)
        ret['status'] = IntercallSatus.objects.get(id=1)
        if status_str:
            status_qs = IntercallSatus.objects.filter(name=status_str)
            if status_qs.exists():
                ret['status'] = status_qs.first()

        return ret

    # def to_representation(self, instance):
