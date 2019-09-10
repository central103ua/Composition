import datetime
import locale
import logging
from datetime import datetime, date, time, timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth import logout as sys_logout
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.db import connection
from django.conf import settings
from mis.models import Mis
from .sysutils import is_mis_admin, is_sys

RED = "#EBCCDC"
YELLOW = "#FCE6AD"
# GREEN = "#C4FFD4" # More bright
GREEN = "#C4E5D4"
GRAY = "#B0B0B0"
# SUN = "#DBBCCC"
SAT = "#FF0000"
SUN = "#EE0000"


@login_required(login_url='/login/')
@user_passes_test(is_sys, login_url='/', redirect_field_name=None)
def syshome(request):
    context = get_syshome_context(request)
    context["refresh"] = True
    return render(request, "home.html", context)


def get_syshome_context(request):
    mis_list = []
    context = {}
    today_list = getCallToday()
    #yesterday_list = getCallYesterday()
    call_av_list = getCallAv()
    er_av_list = getErAv()
    ed_av_list = getEdAv()
    cars_list = getCars()
    facility_list = getFacility()
    staff_list = getStaff()
    # qs = Mis.objects.all().order_by('id')
    for today_item, call_av_item, er_av_item, ed_av_item, facility_item, staff_item, car_item in zip(
            today_list, call_av_list, er_av_list, ed_av_list, facility_list, staff_list, cars_list
    ):
        mis_item = {}
        mis_item['id'] = today_item["id"]
        mis_item['mis_name'] = today_item["mis_name"]
        if today_item["call_num"] is not None:
            mis_item['today'] = today_item["call_num"]
        else:
            mis_item['today'] = ""

        if call_av_item["call_num"] is not None:
            mis_item['call_av'] = call_av_item["call_num"]
        else:
            mis_item['call_av'] = ""

        ###########
        if er_av_item["call_num"] is not None:
            mis_item['er_av'] = er_av_item["call_num"]  # "{:.1f}%".format(ytd_pp)
            if call_av_item["call_num"] is not None and call_av_item["call_num"] != 0:
                mis_item['er_avp'] = "{:.1f}%".format(er_av_item["call_num"] / call_av_item["call_num"] * 100)
            else:
                mis_item['er_avp'] = ""
        else:
            mis_item['er_av'] = ""
            mis_item['er_avp'] = ""

        ###########
        if ed_av_item["call_num"] is not None:
            mis_item['ed_av'] = ed_av_item["call_num"]  # "{:.1f}%".format(ytd_pp)
            mis_item['ed_avp'] = ""
            if ed_av_item["call_num"] is not None and er_av_item["call_num"] != 0:
                # logging.error(f'ed_av_item["call_num"]: {ed_av_item["call_num"]}')
                # logging.error(f'er_av_item["call_num"]: {er_av_item["call_num"]}')
                mis_item['ed_avp'] = "{:.1f}%".format(ed_av_item["call_num"] / er_av_item["call_num"] * 100)
        else:
            mis_item['ed_av'] = ""
            mis_item['ed_avp'] = ""

        if facility_item["facility_num"] is not None:
            mis_item['facility'] = facility_item["facility_num"]
        else:
            mis_item['facility'] = ""
        if staff_item["staff_num"] is not None:
            mis_item['staff'] = staff_item["staff_num"]
        else:
            mis_item['staff'] = ""

        if car_item["car_num"] is not None:
            mis_item['car'] = car_item["car_num"]
        else:
            mis_item['car'] = ""

        # mis_item['status'] = "00ff00"
        mis_item['status'] = GREEN
        if ((today_item["date_modified"] - today_item["timestamp"]) / timedelta(seconds=1)) > 1:
            # if ((qs_today_item.date_modified - qs_today_item.timestamp) / timedelta(seconds=1)) > 1:
            mis_item['mis_heartbeat'] = today_item["date_modified"]  # date_modified
        else:
            mis_item['mis_heartbeat'] = today_item["mis_heartbeat"]  # mis_heartbeat
        # mis_item['mis_heartbeat'] = qs_item.mis_heartbeat
        if mis_item['mis_heartbeat'] is None:
            mis_item['status'] = GRAY
            # mis_item['mis_heartbeat'] = 'Не підєднана'
        else:
            timedif = (timezone.now() - today_item["date_modified"]).seconds
            # timedif = (timezone.now() - qs_today_item.date_modified).seconds
            if timedif > 60:
                mis_item['status'] = "FCE6AD"
                # mis_item['status'] = "F0F000"
            if timedif > 240:
                mis_item['status'] = RED
                # mis_item['status'] = "ff00000"

        mis_list.append(mis_item)
    context = {
        "user": request.user.username,
        "mis_list": mis_list,
        "timezone_now": timezone.now(),
    }
    return context


def getCallToday():
    cursor = connection.cursor()
    cursor.execute('select id, mis_name, timestamp, mis_heartbeat, date_modified, t2.call_c \
        from mis_mis left join \
        (select callcard_callcard.mis_id_id as call_id, Count(callcard_callcard.id) as call_c \
        from callcard_callcard \
        where date(callcard_callcard.start_datetime)=date(now()) \
        group by callcard_callcard.mis_id_id) t2 on mis_mis.id = t2.call_id where mis_mis.is_active=True \
        order by mis_mis.id;')
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


def getCars():
    cursor = connection.cursor()
    cursor.execute("select id, t2.car_c from mis_mis left join \
        (select mis_cars.mis_id_id as car_id , Count(mis_cars.mis_id_id) as car_c \
        from mis_cars where is_active=true \
        group by mis_cars.mis_id_id) t2 on mis_mis.id = t2.car_id where mis_mis.is_active=True \
        order by mis_mis.id;")
    qs_staff = cursor.fetchall()
    staff_list = []
    for qs_staff_item in qs_staff:
        staff_item = {}
        staff_item["id"] = qs_staff_item[0]
        staff_item["car_num"] = qs_staff_item[1]
        staff_list.append(staff_item)
    return staff_list


def getStaff():
    cursor = connection.cursor()
    cursor.execute("select id, t2.call_c from mis_mis left join \
        (select mis_staff.mis_id_id as call_id , Count(mis_staff.mis_id_id) as call_c \
        from mis_staff where is_active=true \
        group by mis_staff.mis_id_id) t2 on mis_mis.id = t2.call_id where mis_mis.is_active=True \
        order by mis_mis.id;")
    qs_staff = cursor.fetchall()
    staff_list = []
    for qs_staff_item in qs_staff:
        staff_item = {}
        staff_item["id"] = qs_staff_item[0]
        staff_item["staff_num"] = qs_staff_item[1]
        staff_list.append(staff_item)
    return staff_list


def getFacility():
    cursor = connection.cursor()
    cursor.execute("select id, t2.call_c from mis_mis left join \
        (select mis_facility.mis_id_id as call_id , Count(mis_facility.mis_id_id) as call_c \
        from mis_facility where is_active=true \
        group by mis_facility.mis_id_id) t2 on mis_mis.id = t2.call_id where mis_mis.is_active=True \
        order by mis_mis.id;")
    qs_facility = cursor.fetchall()
    facility_list = []
    for qs_facility_item in qs_facility:
        facility_item = {}
        facility_item["id"] = qs_facility_item[0]
        facility_item["facility_num"] = qs_facility_item[1]
        facility_list.append(facility_item)
    return facility_list


def getCallAv():
    cursor = connection.cursor()
    cursor.execute("select id, t2.call_c from mis_mis left join \
        (select callcard_callcard.mis_id_id as call_id , Count(callcard_callcard.id) as call_c \
        from callcard_callcard \
        where date(callcard_callcard.start_datetime) <= date(TIMESTAMP 'yesterday') \
        and date(callcard_callcard.start_datetime) >= date(now() - interval '7 day') \
        group by callcard_callcard.mis_id_id) t2 on mis_mis.id = t2.call_id where mis_mis.is_active=True \
        order by mis_mis.id;")
    qs_call_av = cursor.fetchall()
    call_av_list = []
    for qs_av_item in qs_call_av:
        call_av_item = {}
        call_av_item["id"] = qs_av_item[0]
        if qs_av_item[1]:
            call_av_item["call_num"] = round(qs_av_item[1] / 7)
        else:
            call_av_item["call_num"] = qs_av_item[1]
        call_av_list.append(call_av_item)
    return call_av_list


def getErAv():
    cursor = connection.cursor()
    cursor.execute("select id, t2.call_c from mis_mis left join \
        (select callcard_callcard.mis_id_id as call_id , count(callcard_callcard.id) as call_c \
        from callcard_callcard \
        where date(callcard_callcard.start_datetime) <= date(TIMESTAMP 'yesterday') \
        and date(callcard_callcard.start_datetime) >= date(now() - interval '7 day') \
        and call_result_id = 3 \
        group by callcard_callcard.mis_id_id) t2 on mis_mis.id = t2.call_id where mis_mis.is_active=True \
        order by mis_mis.id")
    qs_call_av = cursor.fetchall()
    call_av_list = []
    for qs_av_item in qs_call_av:
        call_av_item = {}
        call_av_item["id"] = qs_av_item[0]
        if qs_av_item[1]:
            call_av_item["call_num"] = round(qs_av_item[1] / 7)
        else:
            call_av_item["call_num"] = qs_av_item[1]
        call_av_list.append(call_av_item)
    return call_av_list


def getEdAv():
    cursor = connection.cursor()
    cursor.execute("select id, t2.call_c from mis_mis left join \
        (select callcard_callcard.mis_id_id as call_id , count(distinct callcard_callcard.id) as call_c \
        from callcard_callcard \
        inner join callcard_callrecord on callcard_callcard.id=callcard_callrecord.card_id_id \
        where callcard_callrecord.call_station_id = 11 \
        and date(callcard_callcard.start_datetime) <= date(TIMESTAMP 'yesterday') \
        and date(callcard_callcard.start_datetime) >= date(now() - interval '7 day') \
        group by callcard_callcard.mis_id_id) t2 on mis_mis.id = t2.call_id where mis_mis.is_active=True \
        order by mis_mis.id")
    qs_call_av = cursor.fetchall()
    call_av_list = []
    for qs_av_item in qs_call_av:
        call_av_item = {}
        call_av_item["id"] = qs_av_item[0]
        if qs_av_item[1]:
            call_av_item["call_num"] = round(qs_av_item[1] / 7)
        else:
            call_av_item["call_num"] = qs_av_item[1]
        call_av_list.append(call_av_item)
    return call_av_list


def mis_logout(request):
    logging.info('mis_logout: ', request.user.id)
    sys_logout(request)
    return HttpResponseRedirect('/login/')
