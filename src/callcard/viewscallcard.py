import datetime
import locale
from datetime import datetime, date, time, timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.defaults import page_not_found
from django.contrib.auth import logout as sys_logout
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.db import connection
#from django.db.models import Q
from django.conf import settings
from mis.models import Mis
from callcard.api.serializers import CallCardSerializer
from callcard.models import CallCard, CallRecord
from mis.sys.sysutils import is_sys, is_mis_admin, is_true_admin
RED = "#FF0000"
GREEN = "#C4FFD4"
GRAY = "#C0C0C0"


@login_required(login_url='/login/')
@user_passes_test(is_sys, login_url='/', redirect_field_name=None)
def callcard_sys_view(request, cardslug):
    callCard_qs = CallCard.objects.filter(call_card_id=cardslug)
    if callCard_qs.exists():
        callCard = callCard_qs.first()
    else:
        return page_not_found(request, f'Not found Callcard: {cardslug}')
    mis_obj = callCard.mis_id
    mis_id = mis_obj.id
    # print(f'MIS: {mis_id}, CallCard: {cardslug}')
    if not is_mis_admin(request.user, mis_id):
        return page_not_found(request, "Not authoruzed")
    callCard_s = CallCardSerializer(callCard)
    ref_date = callCard.start_datetime.strftime('%Y%m%d')
    ref_hour = callCard.start_datetime.strftime('%H')
    date_s = callCard.start_datetime.strftime('%d/%m/%Y')
    duration = callCard.end_datetime - callCard.start_datetime
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    duration_s = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
    context = get_callcard_context(request, mis_obj)
    call_record_l = getCallRecord(callCard)
    med_record_l = getMedRecord(callCard)
    #med_record_l = []
    callStat = getCallStat(callCard, call_record_l)
    if is_true_admin(request.user, mis_id):
        kszi = "True"
    else:
        kszi = "False"
    context["callcard_s"] = callCard_s
    context["callcard"] = callCard
    context["call_record"] = call_record_l
    context["call_stat"] = callStat
    context["med_record"] = med_record_l
    context["ref_date"] = ref_date
    context["ref_hour"] = ref_hour
    context["duration"] = duration_s
    context["is_mis_admin"] = "True"
    context["is_kszi"] = kszi
    context["refresh"] = False
    context["date_s"] = date_s  # "08/02/2019"
    context["mtime"] = callCard.start_datetime
    return render(request, "callcard_sys.html", context)


def get_callcard_context(request, mis_obj):
    mis_id = mis_obj.id
    context = {
        "mis": mis_obj,
        "user": request.user.username,
        "timezone_now": timezone.now(),
        "hostname": settings.HOSTNAME,
        "info_link": f'/sys/mis/{mis_id}/',
        "is_mis_admin": "False",
    }
    return context


def duration_str(duration):
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    duration_s = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
    return duration_s


def getCallStat(callCard, call_record_l):
    callStat = {}
    call_start = callCard.start_datetime
    call_ttp = None
    call_tth = None
    for record in call_record_l:
        if record["call_station"].station_name == 'Оператор103':
            call_start = record["start_datetime"]
        elif record["call_station"].station_name == 'У пацієнта':
            call_ttp = record["start_datetime"]
        elif record["call_station"].station_name == 'У лікарні':
            call_tth = record["start_datetime"]
    #duration_s = duration_str(callCard.end_datetime - callCard.start_datetime)
    callStat['call_duration'] = duration_str(callCard.end_datetime - callCard.start_datetime)
    if call_ttp:
        callStat['ttp'] = duration_str(call_ttp - call_start)
    if call_tth:
        callStat['tth'] = duration_str(call_tth - call_start)
    return callStat


def getMedRecord(callcard_obj):
    med_record = []
    med_record_qs = callcard_obj.medrecord_set.order_by('timestamp')
    if med_record_qs.exists():
        for mrecord_obj in med_record_qs:
            record = {}
            record['med_record_id'] = mrecord_obj.med_record_id

            med_record.append(record)
    else:
        record = {}
        record['med_record_id'] = None
        med_record.append(record)

    return med_record


def getCallRecord(callcard_obj):
    call_record = []
    callrecord_qs = callcard_obj.callrecord_set.order_by('start_datetime')
    call_start_datetime = None
    for record_obj in callrecord_qs:
        record = {}
        if not call_start_datetime:
            call_start_datetime = record_obj.start_datetime
        duration = record_obj.end_datetime - record_obj.start_datetime
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_s = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))

        duration_start = record_obj.end_datetime - call_start_datetime
        hours_st, remainder_st = divmod(duration_start.seconds, 3600)
        minutes_st, seconds_st = divmod(remainder_st, 60)
        duration_start_s = '{:02}:{:02}:{:02}'.format(int(hours_st), int(minutes_st), int(seconds_st))

        record['duration'] = duration_s
        record['duration_start'] = duration_start_s
        record['call_record_seq'] = record_obj.call_record_seq
        record['operator_id'] = record_obj.operator_id
        record['sys_operator_id'] = record_obj.operator_id.id
        record['call_station'] = record_obj.call_station
        record['crew_id'] = record_obj.crew_id
        record['start_datetime'] = record_obj.start_datetime
        record['end_datetime'] = record_obj.end_datetime
        record['timestamp'] = record_obj.timestamp
        record['call_record_comment'] = record_obj.call_record_comment

        call_record.append(record)
    return call_record
