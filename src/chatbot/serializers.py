import json
import time
import logging
import random
from datetime import date, datetime
from collections import Mapping, OrderedDict
from django.utils import timezone
from django.conf import settings
from rest_framework import serializers
from callcard.models import CallCard, CallStations, CallResult, CallPriority
from patients.serializers import PatientSerializer, AddressSerializer, ComplainSerializer


class ChatbotCallSerializer(serializers.ModelSerializer):
    complain = ComplainSerializer(allow_null=True)
    patient = PatientSerializer(allow_null=True)
    call_address = AddressSerializer(allow_null=True)

    class Meta:
        model = CallCard
        fields = [
            'call_card_id',
            'mis_id',
            'caller_number',
            'start_datetime',
            'end_datetime',
            'call_priority',
            'call_result',
            'call_station',
            'complain',
            'patient',
            'call_address',
            'call_comment',
        ]

    def to_representation(self, instance):
        cc_data = super().to_representation(instance)

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

        return cc_data
