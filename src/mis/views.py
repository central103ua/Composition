import re
import time
import datetime
import locale
from datetime import timedelta
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout as sys_logout
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.db import connection
from django import template
from django.conf import settings
from .sys.sysutils import is_sys

from .models import Mis
# C4E5D4 GREEN TIFANY
# FCE6AD YELLOW TIFANY
# EBCCDC RED TIFANY


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def mis_details_view_en(request, mid):
    context = get_detailed_context(request, mid)
    context["refresh"] = True
    return render(request, "mis_details_en.html", context)


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def mis_details_view(request, mid):
    context = get_detailed_context(request, mid)
    context["refresh"] = True
    return render(request, "mis_details.html", context)


def get_detailed_context(request, mid):
    t_d = {}
    t_d[0] = timezone.now()
    t_d[1] = (timezone.now() - timedelta(days=1))
    t_d[2] = (timezone.now() - timedelta(days=2))
    t_d[3] = (timezone.now() - timedelta(days=3))
    t_d[4] = (timezone.now() - timedelta(days=4))
    t_d[5] = (timezone.now() - timedelta(days=5))
    t_d[6] = (timezone.now() - timedelta(days=6))
    #locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
    errors = None
    heartbeat = getHeartbeatSum(mis_id=mid, t_d=t_d)
    calls = getCallSum(mis_id=mid, t_d=t_d)
    fake = getCallTypeSum(mis_id=mid, t_d=t_d, call_type=[1])
    crew_call = getCallTypeSum(mis_id=mid, t_d=t_d, call_type=[3])
    advise = getCallTypeSum(mis_id=mid, t_d=t_d, call_type=[2, 5, 7])
    refuse = getCallTypeSum(mis_id=mid, t_d=t_d, call_type=[6])
    noanswer = getCallTypeSum(mis_id=mid, t_d=t_d, call_type=[8])

    # fake = getFakeCallSum(mis_id=mid, t_d=t_d)
    # advise = getAdCallSum(mis_id=mid, t_d=t_d)
    # crew_call = getCrCallSum(mis_id=mid, t_d=t_d)
    ed_call = getEdCallSum(mis_id=mid, t_d=t_d)
    title = ['YTD', 'last', t_d[0].strftime('%b %d'), t_d[1].strftime('%b %d'),
             t_d[2].strftime('%b %d'), t_d[3].strftime('%b %d'), t_d[4].strftime('%b %d'),
             t_d[5].strftime('%b %d'), t_d[6].strftime('%b %d')]
    hospital = ['0', '', '', '', '', '', '', '', '']
    obj = get_object_or_404(Mis, id=mid)
    context = {
        "mis": obj,
        "user": request.user.username,
        "timezone_now": timezone.now(),
        "title": title,
        "heartbeat": heartbeat,
        "calls": calls,
        "noanswer": noanswer,
        "refuse": refuse,
        "fake": fake,
        "advise": advise,
        "crew_call": crew_call,
        "ed_call": ed_call,
        "hospital": hospital,
        "hostname": settings.HOSTNAME
    }
    return context


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def home(request):
    user = request.user
    if is_sys(user):
        return redirect('/sys/')
    context = get_home_context(request)
    context["refresh"] = True
    return render(request, "home_page.html", context)


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def home_en(request):
    context = get_home_context(request)
    context["refresh"] = True
    return render(request, "home_page_en.html", context)


def get_home_context(request):
    mis_list = []
    context = {}
    #locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
    today_list = getCallToday()
    yesterday_list = getCallYesterday()
    # qs = Mis.objects.all().order_by('id')
    for today_item, yesterday_item in zip(today_list, yesterday_list):
        mis_item = {}
        # print(today_item)
        # print(qs_yesterday_item)
        mis_item['id'] = today_item["id"]  # id
        mis_item['mis_name'] = today_item["mis_name"]  # mis_name
        if today_item["call_num"] is not None:
            mis_item['today'] = today_item["call_num"]
        else:
            mis_item['today'] = ""
        if yesterday_item["call_num"] is not None:
            mis_item['yesterday'] = yesterday_item["call_num"]  # call_c
        else:
            mis_item['yesterday'] = ""

        # mis_item['status'] = "00ff00"
        mis_item['status'] = "C4E5D4"
        if ((today_item["date_modified"] - today_item["timestamp"]) / timedelta(seconds=1)) > 1:
            # if ((qs_today_item.date_modified - qs_today_item.timestamp) / timedelta(seconds=1)) > 1:
            mis_item['mis_heartbeat'] = today_item["date_modified"]  # date_modified
        else:
            mis_item['mis_heartbeat'] = today_item["mis_heartbeat"]  # mis_heartbeat
        # mis_item['mis_heartbeat'] = qs_item.mis_heartbeat
        if mis_item['mis_heartbeat'] is None:
            mis_item['status'] = "b0b0b0"
            # mis_item['mis_heartbeat'] = 'Не підєднана'
        else:
            timedif = (timezone.now() - today_item["date_modified"]).seconds
            # timedif = (timezone.now() - qs_today_item.date_modified).seconds
            if timedif > 60:
                mis_item['status'] = "FCE6AD"
                # mis_item['status'] = "F0F000"
            if timedif > 240:
                mis_item['status'] = "EBCCDC"
                # mis_item['status'] = "ff00000"

        mis_list.append(mis_item)
    # print(mis_list)
    context = {
        "user": request.user.username,
        "mis_list": mis_list,
        "timezone_now": timezone.now(),
    }
    return context


def getEdCallSum(mis_id, t_d):
    cursor = connection.cursor()
    cursor1 = connection.cursor()
    qx_str = f"select count(*), date(timestamp) from callcard_callrecord \
        where call_station_id = 11 and mis_id_id = %s and timestamp > now() - interval '7 day' \
        group by date(timestamp) \
        order by date(timestamp) desc"
    q_str = f'select count(id), max(timestamp) from callcard_callrecord \
        where call_station_id = 11 and mis_id_id = %s'
    cursor.execute(q_str, [mis_id])
    cursor1.execute(qx_str, [mis_id])
    qs_edCallSum = cursor.fetchall()
    qs_edxCallSum = cursor1.fetchall()
    edCallSum = {}
    edCallSum["YTD"] = qs_edCallSum[0][0]
    if qs_edCallSum[0][1] is not None:
        edCallSum["last"] = qs_edCallSum[0][1].strftime('%d/%m/%Y %H:%M:%S')
    else:
        edCallSum["last"] = ""
    edCallxSum = {}
    for q_edxCallSum in qs_edxCallSum:
        edCallxSum[q_edxCallSum[1]] = q_edxCallSum[0]
    edCallSum["dates"] = edCallxSum
    edCalls = [edCallSum['YTD'], edCallSum['last'],
               edCallSum['dates'].get(t_d[0].date(), ""),
               edCallSum['dates'].get(t_d[1].date(), ""),
               edCallSum['dates'].get(t_d[2].date(), ""),
               edCallSum['dates'].get(t_d[3].date(), ""),
               edCallSum['dates'].get(t_d[4].date(), ""),
               edCallSum['dates'].get(t_d[5].date(), ""),
               edCallSum['dates'].get(t_d[6].date(), "")]
    return edCalls


def getCallTypeSum(mis_id, t_d, call_type):
    cursor = connection.cursor()
    cursor1 = connection.cursor()
    qx_str = f"select count(*), date(timestamp) from callcard_callcard \
        where call_result_id in %s and mis_id_id = %s and timestamp > now() - interval '7 day' \
        group by date(timestamp) \
        order by date(timestamp) desc"
    q_str = f'select count(id), max(timestamp) from callcard_callcard \
        where call_result_id in %s and mis_id_id=%s'
    cursor.execute(q_str, [tuple(call_type), mis_id])
    cursor1.execute(qx_str, [tuple(call_type), mis_id])
    qs_fakeCallSum = cursor.fetchall()
    qs_fakexCallSum = cursor1.fetchall()
    fakeCallSum = {}
    fakeCallSum["YTD"] = qs_fakeCallSum[0][0]
    if qs_fakeCallSum[0][1] is not None:
        fakeCallSum["last"] = qs_fakeCallSum[0][1].strftime('%d/%m/%Y %H:%M:%S')
    else:
        fakeCallSum["last"] = ""
    fakeCallxSum = {}
    for q_fakexCallSum in qs_fakexCallSum:
        fakeCallxSum[q_fakexCallSum[1]] = q_fakexCallSum[0]
    fakeCallSum["dates"] = fakeCallxSum
    calls = [fakeCallSum['YTD'], fakeCallSum['last'],
             fakeCallSum['dates'].get(t_d[0].date(), ""),
             fakeCallSum['dates'].get(t_d[1].date(), ""),
             fakeCallSum['dates'].get(t_d[2].date(), ""),
             fakeCallSum['dates'].get(t_d[3].date(), ""),
             fakeCallSum['dates'].get(t_d[4].date(), ""),
             fakeCallSum['dates'].get(t_d[5].date(), ""),
             fakeCallSum['dates'].get(t_d[6].date(), "")]
    return calls


def getCallSum(mis_id, t_d):
    cursor = connection.cursor()
    cursor1 = connection.cursor()
    qx_str = f"select count(*), date(timestamp) from callcard_callcard \
        where mis_id_id = %s and timestamp > now() - interval '7 day' \
        group by date(timestamp) \
        order by date(timestamp) desc"
    q_str = f'select count(id), max(timestamp) from callcard_callcard \
        where mis_id_id = %s'
    cursor.execute(q_str, [mis_id])
    cursor1.execute(qx_str, [mis_id])
    qs_callSum = cursor.fetchall()
    qs_callxSum = cursor1.fetchall()
    callSum = {}
    callSum["YTD"] = qs_callSum[0][0]
    if qs_callSum[0][1] is not None:
        callSum["last"] = qs_callSum[0][1].strftime('%d/%m/%Y %H:%M:%S')
    else:
        callSum["last"] = ""
    callxSum = {}
    for q_callxSum in qs_callxSum:
        callxSum[q_callxSum[1]] = q_callxSum[0]
    callSum["dates"] = callxSum
    calls = [callSum['YTD'], callSum['last'],
             callSum['dates'].get(t_d[0].date(), ""),
             callSum['dates'].get(t_d[1].date(), ""),
             callSum['dates'].get(t_d[2].date(), ""),
             callSum['dates'].get(t_d[3].date(), ""),
             callSum['dates'].get(t_d[4].date(), ""),
             callSum['dates'].get(t_d[5].date(), ""),
             callSum['dates'].get(t_d[6].date(), "")]
    return calls


def getHeartbeatSum(mis_id, t_d):
    cursor = connection.cursor()
    cursor1 = connection.cursor()
    qx_str = f"select count(*), date(timestamp) from heartbeat_heartbeat \
        where mis_id_id = %s and timestamp > now() - interval '7 day' \
        group by date(timestamp) \
        order by date(timestamp) desc"
    q_str = f'select count(id), max(timestamp) from heartbeat_heartbeat \
        where mis_id_id = %s'
    cursor.execute(q_str, [mis_id])
    cursor1.execute(qx_str, [mis_id])
    qs_hbSum = cursor.fetchall()
    qs_hbxSum = cursor1.fetchall()
    hbSum = {}
    hbSum["YTD"] = qs_hbSum[0][0]
    # hbSum["last"] = qs_hbSum[0][1]
    if qs_hbSum[0][1] is not None:
        hbSum["last"] = qs_hbSum[0][1].strftime('%d/%m/%Y %H:%M:%S')
    else:
        hbSum["last"] = ""
    hbxSum = {}
    for q_hbxSum in qs_hbxSum:
        hbxSum[q_hbxSum[1]] = q_hbxSum[0]
    hbSum["dates"] = hbxSum
    heartbeat = [hbSum['YTD'], hbSum['last'],
                 hbSum['dates'].get(t_d[0].date(), ""),
                 hbSum['dates'].get(t_d[1].date(), ""),
                 hbSum['dates'].get(t_d[2].date(), ""),
                 hbSum['dates'].get(t_d[3].date(), ""),
                 hbSum['dates'].get(t_d[4].date(), ""),
                 hbSum['dates'].get(t_d[5].date(), ""),
                 hbSum['dates'].get(t_d[6].date(), "")]
    return heartbeat


def getCallToday():
    cursor = connection.cursor()
    cursor.execute('select id, mis_name, timestamp, mis_heartbeat, date_modified, t2.call_c \
        from mis_mis left join \
        (select callcard_callcard.mis_id_id as call_id , Count(callcard_callcard.id) as call_c \
        from callcard_callcard \
        where date(callcard_callcard.timestamp)=date(now()) \
        group by callcard_callcard.mis_id_id) t2 on mis_mis.id = t2.call_id \
        where mis_mis.is_active=True order by mis_mis.id;')
    # cursor.execute('select mis_mis.id, Count(callcard_callcard.id) \
    #     from mis_mis left join callcard_callcard on mis_mis.id = callcard_callcard.mis_id_id \
    #     where date(callcard_callcard.timestamp)=date(now()) \
    #     group by mis_mis.id;')
    qs_today = cursor.fetchall()
    today_list = []
    for qs_today_item in qs_today:
        today_item = {}
        today_item["id"] = qs_today_item[0]
        today_item["mis_name"] = qs_today_item[1]
        today_item["timestamp"] = qs_today_item[2]
        today_item["mis_heartbeat"] = qs_today_item[3]
        today_item["date_modified"] = qs_today_item[4]
        today_item["call_num"] = qs_today_item[5]
        today_list.append(today_item)
    return today_list


def getCallYesterday():
    cursor = connection.cursor()
    cursor.execute("select id, t2.call_c from mis_mis left join \
        (select callcard_callcard.mis_id_id as call_id , Count(callcard_callcard.id) as call_c \
        from callcard_callcard \
        where date(callcard_callcard.timestamp)=date(TIMESTAMP 'yesterday') \
        group by callcard_callcard.mis_id_id) t2 on mis_mis.id = t2.call_id \
        where mis_mis.is_active=True order by mis_mis.id;")
    # cursor.execute("select mis_mis.id, Count(callcard_callcard.id) \
    #     from mis_mis left join callcard_callcard on mis_mis.id = callcard_callcard.mis_id_id \
    #     where date(callcard_callcard.timestamp)=date(TIMESTAMP 'yesterday') \
    #     group by mis_mis.id;")
    qs_yesterday = cursor.fetchall()
    yesterday_list = []
    for qs_yesterday_item in qs_yesterday:
        yesterday_item = {}
        yesterday_item["id"] = qs_yesterday_item[0]
        yesterday_item["call_num"] = qs_yesterday_item[1]
        yesterday_list.append(yesterday_item)
    return yesterday_list


def mis_logout(request):
    #print('mis_logout: ', request.user.id)
    sys_logout(request)
    return HttpResponseRedirect('/login/')
