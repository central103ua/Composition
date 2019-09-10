from django import forms
from .models import PushQueue
from callcard.models import CallCard


class PushQueueForm(forms.ModelForm):
    class Meta:
        model = PushQueue
        #fields = '__all__'  # 'push_filter, status'

        fields = ('push_filter', 'call_card', 'status', 'message', 'date_sent')
        #readonly_fields = ('date_modified', 'timestamp')

        # fieldsets = (
        # ('Message',
        #     {'fields': ('push_filter', 'call_card', 'status', 'push_url', 'message')}
        #  ),
        # ('Time',
        #     {'fields': ('date_sent', 'date_modified', 'timestamp')}
        #  )
        # )
        #field_classes = {'username': UsernameField}
        #fields = ('username', 'password', 'is_active', 'is_superuser')

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.fields['call_card'].queryset = CallCard.objects.all()[:5]
        if 'instance' in kwargs:
            # print(kwargs['instance'].call_card)
            #cc_l = [].append(kwargs['instance'].call_card)
            #cc_l[1] = kwargs['instance'].call_card
            self.fields['call_card'].queryset = CallCard.objects.all().filter(call_card_id=kwargs['instance'].call_card.call_card_id)
        else:
            self.fields['call_card'].queryset = CallCard.objects.all()[:5]
