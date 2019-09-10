from __future__ import absolute_import, unicode_literals
import json
import time
import logging
import requests
import telebot
from datetime import date, tzinfo, timedelta, datetime
from django.utils import timezone
from django.conf import settings
from celery.decorators import task
from .models import PushFilter, PushQueue, PushStatus


@task(name="pushAPI-process-Q")
def process_queue():
    headers = {
        "Content-type": "application/json",
        "Connection": "keep-alive",
    }
    q_msg_qs = PushQueue.objects.filter(status__name='New')
    result = 'Failed'
    for q_msg in q_msg_qs:
        if q_msg.push_url:
            try:
                logging.info(f'PushAPIHook: msg_id: {q_msg.id}; url: {q_msg.push_url}')
                logging.info(f'Message: {q_msg.message}')
                r = requests.post(q_msg.push_url, headers=headers, data=q_msg.message.encode('utf-8'))
                logging.info(f'POST Response: {r.status_code}; Content-type: {r.headers["content-type"]}')
                if int(r.status_code) >= 500:
                    result = 'Failed'
                    logging.error(r.text)
                elif int(r.status_code) == 401:
                    result = 'Failed'
                    logging.warning(r.text)
                elif int(r.status_code) == 400:
                    result = 'Failed'
                    logging.error(r.text)
                elif int(r.status_code) == 201 or int(r.status_code) == 200:
                    result = 'Sent'
                    q_msg.date_sent = datetime.now()
                    logging.info(r.text)
                else:
                    result = 'Failed'
                    logging.critical(f'Что-то прошло не так')
                    logging.error(r.text)

            except requests.exceptions.RequestException as ex:
                result = 'Failed'
                logging.error(f"PushAPIHook: Exception!: {ex}")
        elif q_msg.telegram_bot:
            token = q_msg.telegram_bot.token
            chanel = q_msg.telegram_bot.chanel
            bot = telebot.TeleBot(token)
            bot.config['api_key'] = token
            bot.send_message(chanel, q_msg.message)
            result = 'Sent'
        else:
            logging.error(f"PushAPIHook: This should never ever happened")

        q_msg.status = PushStatus.objects.get(name=result)
        logging.info(f'Result: {q_msg.status}')
        q_msg.save()
    return True


#####
# Example from Bogdan
#####

# import telebot
# token='820872191:AAEWrDwMy8cnyzq91E-EInIZYiV8sL5FaB4'
# bot = telebot.TeleBot(token)
# bot.config['api_key'] = token

# def make_post (text):
#     bot.send_message('-1001176352486',text) # '-1001176352486' это id канала


# make_post('Test \nHello world')
