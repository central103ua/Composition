from __future__ import absolute_import, unicode_literals
import json
import time
import logging
import requests
from datetime import date, tzinfo, timedelta, datetime
from django.utils import timezone
from django.conf import settings
from celery.decorators import task


@task(name="ChatBotCall")
def send_chatbot(j_botCall):
    headers = {
        "Content-type": "application/json",
        "Connection": "keep-alive",
    }
    try:
        #logging.info(f'ChatBotHookX: {json.dumps(j_botCall, indent=1, ensure_ascii=False)}')
        r = requests.post(settings.CHATBOT_URL, headers=headers, data=json.dumps(j_botCall, indent=1, ensure_ascii=False).encode('utf-8'))
    except requests.exceptions.RequestException as ex:
        logging.error(f"PushAPIHook: Exception!: {ex}")

    return True
