import datetime
import locale
from datetime import datetime, date, time, timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.views.defaults import page_not_found
from django.contrib.auth import logout as sys_logout
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.db import connection
from django.db.models import Q
from django.conf import settings
from mis.models import Mis
from callcard.api.serializers import CallCardSerializer
#from callcard.models import CallCard, CallRecord
from mis.models import Facility, SysAddress
from .sysutils import *
RED = "#FF0000"
GREEN = "#C4FFD4"
GRAY = "#C0C0C0"


@login_required(login_url='/login/')
@user_passes_test(is_sys, login_url='/', redirect_field_name=None)
def facility_sys_view(request, fsslug):
    facility_qs = Facility.objects.filter(id=fsslug)
    if facility_qs.exists():
        facility = facility_qs.first()
    else:
        return page_not_found(request, f'Not found Facility: [{fsslug}]')
    mis_obj = facility.mis_id
    mis_id = mis_obj.id
    if not is_mis_admin(request.user, mis_id):
        return page_not_found(request, "Not authoruzed")
    context = get_crew_context(request, mis_obj)
    context["facility"] = facility
    context["is_mis_admin"] = "True"
    context["refresh"] = False
    return render(request, "facility_sys.html", context)


def get_crew_context(request, mis_obj):
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
