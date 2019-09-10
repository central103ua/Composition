import json
import time
import logging
import random
from datetime import date, datetime
from collections import Mapping, OrderedDict
from django.utils import timezone
from django.conf import settings
from callcard.models import CallCard
from .serializers import ChatbotCallSerializer
from .tasks import send_chatbot

chatbotMis = [3, 6, 8, 30]


def chatbot_hook(callCard):
    if not settings.CHATBOT_HOOK:
        return False

    logging.info(f'ChatBotHook: Processing CallCard# {callCard.call_card_id}. MIS: {callCard.mis_id}')
    j_response = {}
    if callCard.mis_id.id in chatbotMis:
        if callCard.call_result is not None:
            if callCard.call_result.result_name == "Виклик бригади":
                cb_s = ChatbotCallSerializer(callCard)
                j_response["ChatBotCall"] = cb_s.data
                # logging.info(f'ChatBotHook: {json.dumps(j_response, indent=1, ensure_ascii=False)}')

                if settings.DEBUG:
                    logging.info("ChatBot_hook: sending in DEBUG")
                    send_chatbot(j_response)
                else:
                    logging.info("ChatBot_hook: sending in DELAY")
                    send_chatbot.delay(j_response)
    return True
