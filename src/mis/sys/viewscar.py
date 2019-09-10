import datetime
import locale
from datetime import datetime, date, time, timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.views.defaults import page_not_found
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from mis.models import Mis
from callcard.api.serializers import CallCardSerializer
from mis.models import Cars
from .sysutils import *
RED = "#FF0000"
GREEN = "#C4FFD4"
GRAY = "#C0C0C0"


@login_required(login_url='/login/')
@user_passes_test(is_sys, login_url='/', redirect_field_name=None)
def car_sys_view(request, carid):
    cars_qs = Cars.objects.filter(id=carid)
    if cars_qs.exists():
        car_obj = cars_qs.first()
    else:
        return page_not_found(request, f'Not found Car: [{carid}]')

    mis_obj = car_obj.mis_id
    mis_id = mis_obj.id

    context = get_car_context(request, mis_obj)
    context["car"] = car_obj
    context["is_mis_admin"] = "True"
    context["refresh"] = False
    return render(request, "car_sys.html", context)


def get_car_context(request, mis_obj):
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
