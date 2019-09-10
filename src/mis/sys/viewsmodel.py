import time
import datetime
import locale
from datetime import timedelta, date
from django.utils import timezone
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth import logout as sys_logout
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.db import connection
from django.conf import settings
from mis.models import Mis, Facility, Staff, Cars
from .sysutils import *


@login_required(login_url='/login/')
@user_passes_test(is_sys, login_url='/', redirect_field_name=None)
def mis_syscars_view(request, mid):
    # print(f'Facility: MIS {mid}')
    if not is_mis_admin(request.user, mid):
        return redirect('/login/')
    context = get_syscars_context(request, mid)
    return render(request, "mis_cars_sys.html", context)


def get_syscars_context(request, mid):
    car_list = []
    context = {}
    mis = get_object_or_404(Mis, id=mid)
    #facility_list = getFacilities(mis.id)
    car_obj_list = list(Cars.objects.filter(mis_id=mid, is_active=True).order_by("id"))
    for car_obj in car_obj_list:
        car_item = {}
        car_item['id'] = car_obj.id
        car_item['mis_car_id'] = car_obj.mis_car_id
        car_item['mis_facility_id'] = car_obj.mis_facility_id
        car_item['car_model'] = car_obj.car_model
        if car_obj.car_type:
            car_item['car_type'] = car_obj.car_type.cartype_name
        else:
            car_item['car_type'] = None
        if car_obj.car_status:
            car_item['car_status'] = car_obj.car_status.carstatus_name
        else:
            car_item['car_status'] = None
        if car_obj.car_owner:
            car_item['car_owner'] = car_obj.car_owner.carowner_name
        else:
            car_item['car_owner'] = None
        car_item['is_active'] = car_obj.is_active
        car_item['date_modified'] = car_obj.date_modified.strftime('%d/%m/%Y %H:%M:%S')
        car_item['timestamp'] = car_obj.timestamp.strftime('%d/%m/%Y %H:%M:%S')
        car_list.append(car_item)

    context = {
        "car_list_num": len(car_list),
        "car_list": car_list,
        "mis": mis,
        "user": request.user.username,
        "timezone_now": timezone.now(),
        "hostname": settings.HOSTNAME,
        "info_link": f'/sys/mis/{mid}/',
        "is_mis_admin": "True",
    }
    return context


@login_required(login_url='/login/')
@user_passes_test(is_sys, login_url='/', redirect_field_name=None)
def mis_sysstaff_view(request, mid):
    # print(f'Facility: MIS {mid}')
    if not is_mis_admin(request.user, mid):
        return redirect('/login/')
    context = get_sysstaff_context(request, mid)
    return render(request, "mis_staff_sys.html", context)


def get_sysstaff_context(request, mid):
    staff_list = []
    context = {}
    mis = get_object_or_404(Mis, id=mid)
    #facility_list = getFacilities(mis.id)
    staff_obj_list = list(Staff.objects.filter(mis_id=mid, is_active=True).order_by("id"))
    for staff_obj in staff_obj_list:
        staff_item = {}
        staff_item['id'] = staff_obj.id
        staff_item['mis_staff_id'] = staff_obj.mis_staff_id
        staff_item['mis_facility_id'] = staff_obj.mis_facility_id
        staff_item['first_name'] = staff_obj.first_name
        staff_item['family_name'] = staff_obj.family_name
        if staff_obj.title:
            staff_item['title'] = staff_obj.title.title_name
        else:
            staff_item['title'] = ""
        if staff_obj.qualification:
            staff_item['qualification'] = staff_obj.qualification.qualification_name
        else:
            staff_item['qualification'] = ""
        staff_item['is_active'] = staff_obj.is_active
        staff_item['date_modified'] = staff_obj.date_modified.strftime('%d/%m/%Y %H:%M:%S')
        staff_item['timestamp'] = staff_obj.timestamp.strftime('%d/%m/%Y %H:%M:%S')
        staff_list.append(staff_item)

    context = {
        "staff_list_num": len(staff_list),
        "staff_list": staff_list,
        "mis": mis,
        "user": request.user.username,
        "timezone_now": timezone.now(),
        "hostname": settings.HOSTNAME,
        "info_link": f'/sys/mis/{mid}/',
        "is_mis_admin": "True",
    }
    return context


@login_required(login_url='/login/')
@user_passes_test(is_sys, login_url='/', redirect_field_name=None)
def mis_sysfacility_view(request, mid):
    # print(f'Facility: MIS {mid}')
    if not is_mis_admin(request.user, mid):
        return redirect('/login/')
    context = get_sysfacility_context(request, mid)
    return render(request, "mis_facility_sys.html", context)


def get_sysfacility_context(request, mid):
    facility_list = []
    context = {}
    mis = get_object_or_404(Mis, id=mid)
    facility_qs = Facility.objects.filter(mis_id=mid, is_active=True).order_by("id")
    for facility_obj in facility_qs:
        facility_item = {}
        facility_item['id'] = facility_obj.id
        facility_item['mis_facility_id'] = facility_obj.mis_facility_id
        facility_item['name'] = facility_obj.name
        facility_item['short_name'] = facility_obj.short_name
        addr_street = ""
        addr_location = ""
        facility_item['addr_street'] = None
        facility_item['addr_city'] = None
        facility_item['addr_location'] = None
        if facility_obj.address:
            if facility_obj.address.city:
                facility_item['addr_city'] = facility_obj.address.city
            if facility_obj.address.street:
                addr_street = facility_obj.address.street
            if facility_obj.address.building:
                addr_building = facility_obj.address.building
            facility_item['addr_street'] = f'{addr_street} {addr_building}'
            if facility_obj.address.location_type:
                facility_item['addr_location'] = facility_obj.address.location_type.locationtype_name
        #facility_item['street'] = addr_street
        #facility_item['address'] = facility_obj.address.id
        facility_item['facility_contact'] = facility_obj.facility_contact
        if facility_obj.facility_type:
            facility_item['facility_type'] = facility_obj.facility_type.facilitytype_name
        else:
            facility_item['facility_type'] = None
        facility_item['is_active'] = facility_obj.is_active
        facility_item['date_modified'] = facility_obj.date_modified.strftime('%d/%m/%Y %H:%M:%S')
        facility_item['timestamp'] = facility_obj.timestamp.strftime('%d/%m/%Y %H:%M:%S')
        facility_list.append(facility_item)

    context = {
        "facility_num": len(facility_list),
        "facility_list": facility_list,
        "mis": mis,
        "user": request.user.username,
        "timezone_now": timezone.now(),
        "hostname": settings.HOSTNAME,
        "info_link": f'/sys/mis/{mid}/',
        "is_mis_admin": "True",
    }
    return context
