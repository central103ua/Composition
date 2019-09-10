from django.contrib import admin

# Register your models here.

from .models import CallCard
from .models import CallRecord
from .models import CallPriority
from .models import CallStations
from .models import CallResult

# admin.site.register(CallCard)
# admin.site.register(CallRecord)
admin.site.register(CallPriority)
admin.site.register(CallStations)
admin.site.register(CallResult)


class CallRecordAdmin(admin.ModelAdmin):
    list_select_related = (
        'card_id',
    )

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == "card_id":
            kwargs["queryset"] = CallCard.objects.all()[:25]
            # print(kwargs)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(CallRecord, CallRecordAdmin)
