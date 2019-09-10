import datetime
import locale
from datetime import datetime, date, time, timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth import logout as sys_logout
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.db import connection
from django.db.models import Q
from django.conf import settings
from mis.models import Mis
from callcard.models import CallCard
from callcard.api.serializers import CallCardSerializer
from mis.sys.sysutils import is_sys, is_mis_admin
RED = "#FF0000"
GREEN = "#C4FFD4"
GRAY = "#C0C0C0"


@login_required(login_url='/login/')
@user_passes_test(is_sys, login_url='/', redirect_field_name=None)
def ajax_callcard_list(request):
    mid = request.GET.get("mid")
    if not is_mis_admin(request.user, mid):
        return redirect('/login/')
    call_priority = request.GET.get("priority")
    call_result = request.GET.get("result")
    call_date = request.GET.get("date")

    sdate = str(call_date)
    this_date = date(int(sdate[0:4]), int(sdate[4:6]), int(sdate[6:]))

    day_calls = getDayCalls(mid, this_date, call_priority, call_result)
    callCardCount = day_calls.pop()
    context = {
        "day_calls": day_calls,
        "count": callCardCount,
    }
    return render(request, "call_card_list.html", context)


@login_required(login_url='/login/')
@user_passes_test(is_sys, login_url='/', redirect_field_name=None)
def callcard_day_view(request, mid, mdate):
    mis_obj = get_object_or_404(Mis, id=mid)
    if not is_mis_admin(request.user, mid):
        return redirect('/login/')
    conext = get_calls_context(request)
    try:
        sdate = str(mdate)
        this_date = date(int(sdate[0:4]), int(sdate[4:6]), int(sdate[6:]))
        date_s = this_date.strftime("%d/%m/%Y")
    except Exception as ex:
        raise Http404
    day_calls = getDayCalls(mid, this_date)
    callCardCount = day_calls.pop()
    context = get_calls_context(request)
    context["mis"] = mis_obj
    context["mdate"] = mdate
    context["date_s"] = date_s
    context["day_calls"] = day_calls
    context["count"] = callCardCount
    context["info_link"] = f'/sys/mis/{mid}/'
    context["is_mis_admin"] = "True"
    context["refresh"] = False
    return render(request, "callcard_day.html", context)


def getDayCalls(mis_id, this_date, call_priority=None, call_result=None):
    dayCalls = []
    dayCalls_qs = CallCard.objects.filter(Q(mis_id=mis_id) &
                                          Q(start_datetime__contains=this_date))
    if call_priority and call_priority != '11':
        print(f'getDayCalls::call_priority: {call_priority}')
        dayCalls_qs = dayCalls_qs.filter(Q(call_priority=call_priority))
    if call_result and call_result != '11':
        print(f'getDayCalls::call_result: {call_result}')
        dayCalls_qs = dayCalls_qs.filter(Q(call_result=call_result))

    dayCalls_qs = dayCalls_qs.order_by("id")
    for callItem_obj in dayCalls_qs:
        theCall = {}
        theCall["call_card_id"] = callItem_obj.call_card_id
        theCall["mis_call_card_id"] = callItem_obj.mis_call_card_id
        theCall["call_priority"] = callItem_obj.call_priority
        theCall["call_result"] = callItem_obj.call_result
        theCall["call_station"] = callItem_obj.call_station
        theCall["crew_id"] = callItem_obj.crew_id
        if callItem_obj.complain:
            theCall["complain"] = callItem_obj.complain.complain1
        else:
            theCall["complain"] = ""
        duration = callItem_obj.end_datetime - callItem_obj.start_datetime
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_s = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))

        theCall["duration"] = duration_s
        theCall["start_datetime"] = callItem_obj.start_datetime.strftime('%d/%m/%Y %H:%M:%S')
        dayCalls.append(theCall)

    count = dayCalls_qs.count()
    dayCalls.append(count)
    return dayCalls


@login_required(login_url='/login/')
@user_passes_test(is_sys, login_url='/', redirect_field_name=None)
def callcard_hour_view(request, mid, mdate, mhour):
    mis_obj = get_object_or_404(Mis, id=mid)
    if not is_mis_admin(request.user, mid):
        return redirect('/login/')
    context = get_calls_context(request)
    sdate = str(mdate)
    try:
        this_date = date(int(sdate[0:4]), int(sdate[4:6]), int(sdate[6:]))
        this_time = time(int(mhour), 0)
        this_datetime = datetime.combine(this_date, this_time)
        this_datetime_s = this_datetime.strftime('%d/%m/%Y %H:%M')
    except Exception as ex:
        raise Http404
    date_s = this_date.strftime("%d/%m/%Y")
    day_calls = getHourCalls(mid, this_datetime)
    callCardCount = day_calls.pop()

    context["mis"] = mis_obj
    context["mtime"] = this_time
    context["mdatetime"] = this_datetime
    context["mdatetime_s"] = this_datetime_s
    context["date_s"] = date_s
    context["day_calls"] = day_calls
    context["count"] = callCardCount
    context["mdate"] = sdate
    context["info_link"] = f'/sys/mis/{mid}/'
    context["is_mis_admin"] = "True"
    context["refresh"] = True
    return render(request, "callcard_hour.html", context)


def getHourCalls(mis_id, this_datetime):
    dayCalls = []
    this_datetime_end = this_datetime + timedelta(seconds=3600)
    dayCalls_qs = CallCard.objects.filter(Q(mis_id=mis_id) &
                                          Q(start_datetime__gt=this_datetime) &
                                          Q(start_datetime__lt=this_datetime_end)).order_by("id")

    for callItem_obj in dayCalls_qs:
        theCall = {}
        theCall["call_card_id"] = callItem_obj.call_card_id
        theCall["mis_call_card_id"] = callItem_obj.mis_call_card_id
        theCall["call_priority"] = callItem_obj.call_priority
        theCall["call_result"] = callItem_obj.call_result
        theCall["call_station"] = callItem_obj.call_station
        theCall["crew_id"] = callItem_obj.crew_id
        if callItem_obj.complain:
            theCall["complain"] = callItem_obj.complain.complain1
        else:
            theCall["complain"] = ""
        duration = callItem_obj.end_datetime - callItem_obj.start_datetime
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_s = '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))

        theCall["duration"] = duration_s
        theCall["start_datetime"] = callItem_obj.start_datetime.strftime('%d/%m/%Y %H:%M:%S')
        dayCalls.append(theCall)

    count = dayCalls_qs.count()
    dayCalls.append(count)
    return dayCalls


def get_calls_context(request):
    context = {
        "user": request.user.username,
        "timezone_now": timezone.now(),
        "hostname": settings.HOSTNAME,
    }
    return context
