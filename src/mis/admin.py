from django.contrib import admin

# Register your models here.

from .models import Mis
from .models import MisType
from .models import Facility
from .models import Staff
from .models import Cars
from .models import SysAddress


admin.site.register(Mis)
admin.site.register(MisType)
admin.site.register(Facility)
admin.site.register(SysAddress)
admin.site.register(Staff)
admin.site.register(Cars)
