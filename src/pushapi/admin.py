from django.contrib import admin
from callcard.models import CallCard

# Register your models here.
from .models import PushQueue
from .models import PushFilter
from .models import PushCustomer
from .models import PushStatus
from .models import FilterLogic
from .models import TelegramBot

from .forms import PushQueueForm

# admin.site.register(PushQueue)
# admin.site.register(PushFilter)
admin.site.register(PushCustomer)
admin.site.register(PushStatus)
admin.site.register(FilterLogic)


class TelegramBotAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active',)


admin.site.register(TelegramBot, TelegramBotAdmin)


class PushQueueAdmin(admin.ModelAdmin):
    readonly_fields = ('date_sent', 'date_modified', 'timestamp',)
    form = PushQueueForm
    list_display = ('id', 'push_filter', 'status', 'timestamp', )
    list_select_related = (
        'call_card',
    )

    # def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
    #     if db_field.name == "call_card":
    #         kwargs["queryset"] = CallCard.objects.all()[:15]
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(PushQueue, PushQueueAdmin)


class PushFilterAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Filter',
            {'fields': ('name', 'customer',)}
         ),
        ('Destination',
            {'fields': ('is_push_url', 'push_url', 'is_bot', 'telegram_bot')}
         ),
        ('MIS',
            {'fields': ('mis_id_logic', 'mis_id')}
         ),
        ('Statuses',
            {'fields': ('call_station_logic', 'call_station',
                        'call_result_logic', 'call_result',
                        'call_priority_logic', 'call_priority')}
         ),
        ('Complain',
            {'fields': ('complain_code_logic', 'chief_complain_code',
                        'complain_text_logic', 'chief_complain_text')}
         ),
        ('Address',
            {'fields': ('address_district_logic', 'address_district',
                        'address_city_logic', 'address_city',
                        'address_locationtype_logic', 'address_locationtype')}
         ),
        (None,
            {'fields': ('is_active', 'date_modified')}
         ),
    )
    readonly_fields = ['date_modified']


admin.site.register(PushFilter, PushFilterAdmin)
