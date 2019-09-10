# ekshome URL Configuration
#from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path, path, include
from django.contrib import admin
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token
from django.contrib.auth.views import LoginView, LogoutView
from heartbeat.api.views import HeartbeatView
#from intercall.api.views import IntercallView
from mis.views import home, mis_logout, mis_details_view
from mis.views import home_en, mis_details_view_en
from callcard.api.views import CallCardView, CallCardRudView
from callcard.views import ajax_callcard_list
from crew.api.views import CrewView, CrewRudView
from medrecord.api.views import MedRecordView, MedRecordRudView
from medrecord.views import medrecord_sys_view
from callcard.viewscallcard import callcard_sys_view

# home.html - for sys users
# home_page.html - for aemuser, misuser

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^login/$', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    re_path(r'^logout/$', LogoutView.as_view(next_page='/login/'), name='logout'),
    re_path(r'^api/auth/login/$', obtain_jwt_token, name='api-login'),
    re_path(r'^api/heartbeat/', HeartbeatView.as_view(), name='api-heartbeat'),
    #re_path(r'^api/intercall/', IntercallView.as_view(), name='api-intercall'),
    re_path(r'^api/mis/', include('mis.api.urls')),
    re_path(r'^api/callcard/$', CallCardView.as_view(), name='api-callcard'),
    re_path(r'^api/callcard/(?P<slug>[\w-]+)', CallCardRudView.as_view()),
    re_path(r'^api/crew/$', CrewView.as_view(), name='api-crew'),
    re_path(r'^api/crew/(?P<slug>[\w-]+)', CrewRudView.as_view()),
    re_path(r'^api/medrecord/$', MedRecordView.as_view(), name='api-crew'),
    re_path(r'^api/medrecord/(?P<slug>[\w-]+)', MedRecordRudView.as_view()),
    re_path(r'^sys/medrecord/(?P<medrecordslug>[\w-]+)/$', medrecord_sys_view),
    re_path(r'^sys/callcard/(?P<cardslug>[\w-]+)/$', callcard_sys_view),
    path('en/', home_en),
    re_path(r'^$', home),
    re_path(r'^mis/(?P<mid>[\w-]+)/$', mis_details_view),
    re_path(r'^en/mis/(?P<mid>[\w-]+)/$', mis_details_view_en),
    re_path(r'^sys/', include('mis.sys.urls', namespace='sys')),
    re_path(r'^ajax/api/callcardlist/$', ajax_callcard_list),

]

if settings.DEBUG:
    urlpatterns = urlpatterns + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
