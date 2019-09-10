#from django.conf.urls import url, include
from django.urls import re_path, path, include
from django.contrib.auth.views import LoginView
from .views import MisAPIView
from .cviews import MisCreateView, UserCreateView, FacilityCreateView, StaffCreateView, CarCreateView

app_name = 'api-mis'
urlpatterns = [
    # re_path(r'^$', MisAPIView.as_view(), name='mis-list'),
    # re_path(r'^createmis/', MisCreateView.as_view(), name='mis-create'),
    # re_path(r'^createuser/', UserCreateView.as_view(), name='user-create'),
    re_path(r'^facility/', FacilityCreateView.as_view(), name='facility-create'),
    re_path(r'^staff/', StaffCreateView.as_view(), name='staff-create'),
    re_path(r'^cars/', CarCreateView.as_view(), name='car-create'),
]
