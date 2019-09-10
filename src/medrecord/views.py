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
# from callcard.api.serializers import CallCardSerializer
# from callcard.models import CallCard, CallRecord
from medrecord.models import MedRecord
from medrecord.api.serializers import MedRecordSerializer
from mis.sys.sysutils import is_sys, is_mis_admin, is_true_admin
RED = "#FF0000"
GREEN = "#C4FFD4"
GRAY = "#C0C0C0"


@login_required(login_url='/login/')
@user_passes_test(is_sys, login_url='/', redirect_field_name=None)
def medrecord_sys_view(request, medrecordslug):
    medRecord_qs = MedRecord.objects.filter(med_record_id=medrecordslug)
    if medRecord_qs.exists():
        medRecord_obj = medRecord_qs.first()
    else:
        return page_not_found(request, f'Not found Callcard: {medrecordslug}')
    mis_obj = medRecord_obj.mis_id
    mis_id = mis_obj.id
    if not is_mis_admin(request.user, mis_id):
        return page_not_found(request, "Not authoruzed")
    medRecord_s = MedRecordSerializer(medRecord_obj)
    ref_date = medRecord_obj.start_datetime.strftime('%Y%m%d')
    ref_hour = medRecord_obj.start_datetime.strftime('%H')
    date_s = medRecord_obj.start_datetime.strftime('%d/%m/%Y')
    noresult_msg = "Виїзд рзультативний"
    is_result = True
    if medRecord_obj.noresult:
        if medRecord_obj.noresult.name != "результативний":
            noresult_msg = f"Виїзд безрезультатний: {medRecord_obj.noresult.name}"
            is_result = False
    hospital_list = list(medRecord_obj.mrhospital_set.order_by('hospital_seq'))
    diagnosis_list = list(medRecord_obj.mrdiagnosis_set.order_by('diagnosis_seq'))
    context = get_medrecord_context(request, mis_obj)
    if is_true_admin(request.user, mis_id):
        kszi = "True"
    else:
        kszi = "False"
    context["medrecord_s"] = medRecord_s
    context["medrecord"] = medRecord_obj
    context["ref_date"] = ref_date
    context["ref_hour"] = ref_hour
    context["date_s"] = date_s
    context["noresult_msg"] = noresult_msg
    context["is_result"] = is_result
    context["hospital_list"] = hospital_list
    context["diagnosis_list"] = diagnosis_list
    context["is_mis_admin"] = "True"
    context["is_kszi"] = kszi
    context["refresh"] = False
    context["mtime"] = medRecord_obj.start_datetime
    return render(request, "medrecord_sys.html", context)


def get_medrecord_context(request, mis_obj):
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


# def getMedRecord(callcard_obj):
#     med_record = []
#     medrecord_qs = callcard_obj.medrecord_set.order_by('timestamp')
#     if medrecord_qs.exists():
#         for mrecord_obj in medrecord_qs:
#             record = {}
#             record['medrecord_id'] = mrecord_obj.medrecord_id

#             med_record.append(record)
#     else:
#         record = {}
#         record['medrecord_id'] = None
#         med_record.append(record)

#     return med_record


# def getCallRecord(callcard_obj):
#     call_record = []
#     callrecord_qs = callcard_obj.callrecord_set.order_by('start_datetime')

#     for record_obj in callrecord_qs:
#         record = {}
#         duration = record_obj.end_datetime - record_obj.start_datetime
#         hours, remainder = divmod(duration.seconds, 3600)
#         minutes, seconds = divmod(remainder, 60)
#         duration_s = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))
#         record['duration'] = duration_s
#         record['call_record_seq'] = record_obj.call_record_seq
#         record['operator_id'] = record_obj.operator_id
#         record['sys_operator_id'] = record_obj.operator_id.id
#         record['call_station'] = record_obj.call_station
#         record['crew_id'] = record_obj.crew_id
#         record['start_datetime'] = record_obj.start_datetime
#         record['end_datetime'] = record_obj.end_datetime
#         record['timestamp'] = record_obj.timestamp
#         record['call_record_comment'] = record_obj.call_record_comment

#         call_record.append(record)
#     return call_record
