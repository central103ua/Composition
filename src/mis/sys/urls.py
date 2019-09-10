from django.urls import re_path, path, include
from callcard.views import callcard_hour_view, callcard_day_view
from .views import syshome
from .viewsmodel import mis_sysfacility_view, mis_sysstaff_view, mis_syscars_view
from .viewscrew import crew_sys_view
from .viewsfacility import facility_sys_view
from .viewsstaff import staff_sys_view
from .viewscar import car_sys_view

app_name = 'sys-mis'
urlpatterns = [
    re_path(r'^$', syshome, name='mis-sys'),

    re_path(r'^mis/(?P<mid>[\d-]+)/(?P<mdate>[\d-]+)/calls/$', callcard_day_view),
    re_path(r'^mis/(?P<mid>[\d-]+)/(?P<mdate>[\d-]+)/(?P<mhour>[\d-]+)/$', callcard_hour_view),
    re_path(r'^mis/(?P<mid>[\d-]+)/facility/$', mis_sysfacility_view, name='facility'),
    re_path(r'^mis/(?P<mid>[\d-]+)/staff/$', mis_sysstaff_view, name='staff'),
    re_path(r'^mis/(?P<mid>[\d-]+)/cars/$', mis_syscars_view, name='cars'),
    re_path(r'^crew/(?P<crewslug>[\w-]+)/$', crew_sys_view),
    re_path(r'^facility/(?P<fsslug>[\w-]+)/$', facility_sys_view),
    re_path(r'^staff/(?P<staffslug>[\w-]+)/$', staff_sys_view),
    re_path(r'^car/(?P<carid>[\w-]+)/$', car_sys_view),
]
