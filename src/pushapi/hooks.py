import json
import time
import logging
import requests
from datetime import date, tzinfo, timedelta, datetime
from django.conf import settings
from callcard.models import CallCard
from .models import PushFilter, PushQueue, PushStatus
from .tasks import process_queue


def pushapi_hook(callCard):
    if not settings.PUSH_API_HOOK:
        logging.warning(f'PushAPI: PushAPI is disabled. Skiping for now')
        return True
    logging.info(f'PushAPIHook: Processing CallCard# {callCard.call_card_id}. MIS: {callCard.mis_id}, Station: {callCard.call_station}')
    result_b = False
    filter_qs = PushFilter.objects.filter(is_active=True)
    for filter_obj in filter_qs:
        logging.info(f'PushAPIHook:Filter:: {filter_obj.name}')
        try:
            if not check_mis(filter_obj, callCard):
                logging.info(f'PushAPIHook:MIS:: False')
                continue
            if not check_station(filter_obj, callCard):
                logging.info(f'PushAPIHook:Station:: False')
                continue
            if not check_result(filter_obj, callCard):
                logging.info(f'PushAPIHook:Result:: False')
                continue
            if not check_priority(filter_obj, callCard):
                logging.info(f'PushAPIHook:Priority:: False')
                continue
            if not check_complain_code(filter_obj, callCard):
                logging.info(f'PushAPIHook:Complain Code:: False')
                continue
            if not check_complain_text(filter_obj, callCard):
                logging.info(f'PushAPIHook:Complain Text:: False')
                continue
            if not check_address(filter_obj, callCard):
                logging.info(f'PushAPIHook:Address:: False')
                continue
            logging.info(f'PushAPIHook: Adding to PushQueue')
            if add_to_queue(filter_obj, callCard):
                result_b = True
        except Exception as e:
            logging.critical(f'PushAPIHook: filters failed!!!')
            logging.error(e, exc_info=True)

    if result_b:
        try:
            if settings.DEBUG:
                logging.info("Process_q in DEBUG")
                process_queue()
            else:
                logging.info("Process_q in DELAY")
                process_queue.delay()
        except Exception as e:
            logging.critical(f'PushAPIHook: process_queue.delay() failed!')
            logging.error(e, exc_info=True)

            q_msg_qs = PushQueue.objects.filter(status=1)
            for q_msg in q_msg_qs:
                q_msg.status = PushStatus.objects.get(name='Failed')
                q_msg.date_sent = datetime.now()
                q_msg.save()
            return False
    return True


def check_mis(filter_obj, callCard):
    if filter_obj.mis_id_logic.name == 'Ignore':
        pushlog(f'PushAPI:Filter:{filter_obj}:MIS:: Ignoring')
        return True
    if filter_obj.mis_id_logic.name == 'Equal' or filter_obj.mis_id_logic.name == 'Contain':
        if filter_obj.mis_id.id == callCard.mis_id.id:
            pushlog(f'PushAPI:Filter:{filter_obj}:MIS:: IS equal')
            return True
        pushlog(f'PushAPI:Filter:{filter_obj}:MIS:: NOT equal')
        return False
    logging.error(f'PushAPI:Filter:{filter_obj}:MIS. This should NEVER EVER HAPPEN')
    return False


def check_station(filter_obj, callCard):
    if filter_obj.call_station_logic.name == 'Ignore':
        pushlog(f'PushAPI:Filter:{filter_obj}:Station:: Ignoring')
        return True
    if filter_obj.call_station_logic.name == 'Equal' or filter_obj.call_station_logic.name == 'Contain':
        filter_call_station = filter_obj.call_station
        callcard_call_station = callCard.call_station
        if filter_call_station == None and callcard_call_station == None:
            pushlog(f'PushAPI:Filter:{filter_obj}:Station:: Both None')
            return True
        if filter_call_station is not None and callcard_call_station is not None:
            if filter_call_station.id == callcard_call_station.id:
                pushlog(f'PushAPI:Filter:{filter_obj}:Station:: IS equal')
                return True
            pushlog(f'PushAPI:Filter:{filter_obj}:Station:: NOT equal')
            return False
        else:
            pushlog(f'PushAPI:Filter:{filter_obj}:Station:: NOT equal (None vs. Not None)')
            return False
    logging.error(f'PushAPI:Filter:{filter_obj}:Station. This should NEVER EVER HAPPEN')
    return False


def check_result(filter_obj, callCard):
    if filter_obj.call_result_logic.name == 'Ignore':
        pushlog(f'PushAPI:Filter:{filter_obj}:Result:: Ignoring')
        return True
    if filter_obj.call_result_logic.name == 'Equal' or filter_obj.call_result_logic.name == 'Contain':
        filter_call_result = filter_obj.call_result
        callcard_call_result = callCard.call_result
        if filter_call_result == None and callcard_call_result == None:
            pushlog(f'PushAPI:Filter:{filter_obj}:Result:: Both None')
            return True
        if filter_call_result is not None and callcard_call_result is not None:
            if filter_obj.call_result.id == callCard.call_result.id:
                pushlog(f'PushAPI:Filter:{filter_obj}:Result:: IS equal')
                return True
            pushlog(f'PushAPI:Filter:{filter_obj}:Result:: NOT equal')
            return False
        else:
            pushlog(f'PushAPI:Result filter:: NOT equal (None vs. Not None)')
            return False

    logging.error(f'PushAPI:Filter:{filter_obj}:Result. This should NEVER EVER HAPPEN')
    return False


def check_priority(filter_obj, callCard):
    if filter_obj.call_priority_logic.name == 'Ignore':
        pushlog(f'PushAPI:Filter:{filter_obj}:Priority:: Ignoring')
        return True
    if filter_obj.call_priority_logic.name == 'Equal' or filter_obj.call_priority_logic.name == 'Contain':
        if filter_obj.call_priority == callCard.call_priority:
            return True
        else:
            return False
    else:
        logging.error(f'PushAPI:Filter:{filter_obj}:Priority. This should NEVER EVER HAPPEN')
    # logging.error(f'PushAPI:Priority filter. Is not yet implemented')
    return True


def check_complain_code(filter_obj, callCard):
    if filter_obj.complain_code_logic.name == 'Ignore':
        pushlog(f'PushAPI:Filter:{filter_obj}:Complain Code:: Ignoring')
        return True

    if filter_obj.complain_code_logic.name == 'Equal' or filter_obj.complain_code_logic.name == 'Contain':
        if not callCard.complain:
            pushlog(f'PushAPI:Filter:{filter_obj}:Complain Code:: CallCard complain is None')
            return False
        if filter_obj.chief_complain_code == callCard.complain.chief_complain:
            pushlog(f'PushAPI:Filter:{filter_obj}:Complain Code:: IS equal')
            return True
        else:
            pushlog(f'PushAPI:Filter:{filter_obj}:Complain Code:: NOT equal')
            return False
    else:
        logging.error(f'PushAPI:Filter:{filter_obj}:Complain. This should NEVER EVER HAPPEN')
        return False


def check_complain_text(filter_obj, callCard):
    if filter_obj.complain_text_logic.name == 'Ignore':
        pushlog(f'PushAPI:Filter:{filter_obj}:Complain Text:: Ignoring')
        return True

    if not callCard.complain:
        pushlog(f'PushAPI:Filter:{filter_obj}:Complain Code:: CallCard complain is None')
        return False
    if filter_obj.complain_text_logic.name == 'Equal':
        if callCard.complain.complain1 == filter_obj.chief_complain_text:
            pushlog(f'PushAPI:Filter:{filter_obj}:Complain Text:: IS equal')
            return True
    elif filter_obj.complain_text_logic.name == 'Contain':
        if callCard.complain.complain1.lower().find(filter_obj.chief_complain_text.lower()) >= 0:
            pushlog(f'PushAPI:Filter:{filter_obj}:Complain Text:: IS Contain')
            return True
    else:
        logging.error(f'PushAPI:Complain Text. This should NEVER EVER HAPPEN')
        return False
    pushlog(f'PushAPI:Filter:{filter_obj}:Complain Text:: NOT equal')
    return False


def check_address(filter_obj, callCard):
    # Checking District
    if filter_obj.address_district_logic.name == 'Ignore':
        pushlog(f'PushAPI:Filter:{filter_obj}:Address district:: Ignoring')
        return True

    if not callCard.address:
        pushlog(f'PushAPI:Filter:{filter_obj}:Address:: callCard.address is None')
        return False

    if filter_obj.address_district_logic.name == 'Equal':
        if callCard.address.district == filter_obj.address_district:
            pushlog(f'PushAPI:Filter:{filter_obj}:Address district:: IS equal')
            return True
        else:
            pushlog(f'PushAPI:Filter:{filter_obj}:Address district:: NOT Equal')
            return False
    elif filter_obj.address_district_logic.name == 'Contain':
        # make CONTAIN here
        if callCard.address.district.lower().find(filter_obj.address_district.lower()) >= 0:
            pushlog(f'PushAPI:Filter:{filter_obj}:Address district:: IS Contain')
            return True
        else:
            pushlog(f'PushAPI:Filter:{filter_obj}:Address district:: NOT Contail')
            return False
    else:
        logging.error(f'PushAPI:Address district. This should NEVER EVER HAPPEN')
        return False

    # Check City
    if filter_obj.address_city_logic.name == 'Ignore':
        pushlog(f'PushAPI:Filter:{filter_obj}:Address city:: Ignoring')
        return True
    if filter_obj.address_city_logic.name == 'Equal':
        if callCard.address.city == filter_obj.address_city:
            pushlog(f'PushAPI:Filter:{filter_obj}:Address city:: IS equal')
            return True
        else:
            pushlog(f'PushAPI:Filter:{filter_obj}:Address city:: NOT Equal')
            return False
    elif filter_obj.address_city_logic.name == 'Contain':
        # make CONTAIN here
        if callCard.address.city.lower().find(filter_obj.address_city.lower()) >= 0:
            pushlog(f'PushAPI:Filter:{filter_obj}:Address city:: IS Contain')
            return True
        else:
            pushlog(f'PushAPI:Filter:{filter_obj}:Address city:: NOT Contail')
            return False
    else:
        logging.error(f'PushAPI:Address city. This should NEVER EVER HAPPEN')
        return False

    # Check Location Type
    if filter_obj.address_locationtype_logic.name == 'Ignore':
        pushlog(f'PushAPI:Filter:{filter_obj}:Address locationtype:: Ignoring')
        return True
    if filter_obj.address_locationtype_logic.name == 'Equal' or filter_obj.address_locationtype_logic.name == 'Contain':
        if filter_obj.address_locationtype_logic == filter_obj.address_locationtype:
            pushlog(f'PushAPI:Filter:{filter_obj}:Address Location type:: IS equal')
            return True
        else:
            pushlog(f'PushAPI:Filter:{filter_obj}:Address Location type:: NOT equal')
            return False
    else:
        logging.error(f'PushAPI:Address Location type. This should NEVER EVER HAPPEN')
        return False
    return False


def add_to_queue(filter_obj, callCard):
    pushlog(f'PushAPIHook:add_to_queue:: CallCard# {callCard.call_card_id}, filter# {filter_obj.id}')
    pq_qs = PushQueue.objects.filter(push_filter=filter_obj, call_card=callCard)
    if pq_qs.exists():
        logging.info(f'PushAPIHook: add_to_queue:: CallCard# {callCard.call_card_id}, filter# {filter_obj.id} already in Q')
        return False

    # Each filter can add to queue URL and BOT message
    message = "The Message"
    if filter_obj.is_push_url:
        message = json_message(filter_obj, callCard)
        pq = PushQueue.objects.create(push_filter=filter_obj,
                                      call_card=callCard,
                                      push_url=filter_obj.push_url,
                                      telegram_bot=None,
                                      message=message,
                                      status=PushStatus.objects.get(name='New'))
        logging.info(f'PushAPIHook[URL]: add_to_queue:: CallCard# {callCard.call_card_id}')

    if filter_obj.is_bot:
        message = bot_message(filter_obj, callCard)
        pq = PushQueue.objects.create(push_filter=filter_obj,
                                      call_card=callCard,
                                      push_url=None,
                                      telegram_bot=filter_obj.telegram_bot,
                                      message=message,
                                      status=PushStatus.objects.get(name='New'))
        logging.info(f'PushAPIHook[BOT]: add_to_queue:: CallCard# {callCard.call_card_id}')

    return True


def bot_message(filter_obj, callCard):
    start_time = callCard.start_datetime.strftime('%H:%M')
    address_str = ""
    if callCard.call_address.district:
        address_str += f"{callCard.call_address.district} рн,"
    # address_str += callCard.call_address.location_type.locationtype_short
    if callCard.call_address.city:
        if callCard.call_address.city.find("м.") >= 0:
            address_str += f" {callCard.call_address.city}"
        else:
            address_str += f" м.{callCard.call_address.city}"
    if callCard.call_address.street:
        if callCard.call_address.street.find("вул.") >= 0:
            address_str += f" {callCard.call_address.street}"
        else:
            address_str += f" вул.{callCard.call_address.street}"
    if callCard.call_address.building:
        address_str += f" {callCard.call_address.building}"
    msg_body = f'За інформацією від МІС#{callCard.mis_id.id}: {callCard.mis_id.mis_name} \
о {start_time} надійшло повідомлення про: {callCard.complain.complain1}. Адреса: {address_str}. \
Час до першого медичного контакту: 10хв. \
Виклик# {callCard.call_card_id}'

    msg_text = msg_body
    pushlog(msg_text)
    # logging.warning(f'Bot Message: {msg_text}')
    return msg_text


def json_message(filter_obj, callCard):
    filter_complain = {}
    if callCard.complain:
        filter_complain['ChiefComplain'] = callCard.complain.complain1
        filter_complain['VitalSigns'] = callCard.complain.complain2
        filter_complain['PatientStatus'] = callCard.complain.complain3
        filter_complain['Sircumstance'] = callCard.complain.complain4
    else:
        filter_complain['ChiefComplain'] = 'Невизначено'
        filter_complain['VitalSigns'] = 'Невизначено'
        filter_complain['PatientStatus'] = 'Невизначено'
        filter_complain['Sircumstance'] = 'Невизначено'

    filter_address = {}
    address_str = 'Невизначено'
    if callCard.call_address:
        building_str = ''
        if callCard.call_address.building:
            building_str = f' {callCard.call_address.building}'
        address_str = f'{callCard.call_address.street}{building_str}'
    district_msg = 'Невизначено'
    if callCard.call_address:
        if callCard.call_address.district:
            district_msg = callCard.call_address.district
    filter_address['District'] = district_msg
    filter_address['Address'] = address_str

    if callCard.call_address:
        filter_address['City'] = callCard.call_address.city
        filter_address['LocationType'] = callCard.call_address.location_type.locationtype_name
        filter_address['AddressType'] = callCard.call_address.address_type.addresstype_name
        filter_address['Longitude'] = callCard.call_address.longitude
        filter_address['Latitude'] = callCard.call_address.latitude
    else:
        filter_address['LocationType'] = 'Невизначено'
        filter_address['AddressType'] = 'Невизначено'
        filter_address['Longitude'] = 'Невизначено'
        filter_address['Latitude'] = 'Невизначено'
        filter_address['City'] = 'Невизначено'
    msg = json.loads('{"Central103": {}}')
    msg['Central103']['CallCard'] = callCard.call_card_id
    msg['Central103']['FilterName'] = filter_obj.name
    msg['Central103']['Region'] = callCard.mis_id.mis_name
    if callCard.call_priority:
        msg['Central103']['Priority'] = callCard.call_priority.priority_name
    else:
        msg['Central103']['Priority'] = 'Невизначено'
    if callCard.call_result:
        msg['Central103']['CallResult'] = callCard.call_result.result_name
    else:
        msg['Central103']['CallResult'] = 'Невизначено'
    msg['Central103']['Complain'] = filter_complain
    msg['Central103']['Address'] = filter_address
    msg['Central103']['timestamp'] = datetime.now().isoformat()

    msg_text = json.dumps(msg, indent=1, ensure_ascii=False)
    pushlog(msg_text)
    return msg_text


# def process_queue():
#     headers = {
#         "Content-type": "application/json",
#         "Connection": "keep-alive",
#     }
#     q_msg_qs = PushQueue.objects.filter(status=1)
#     for q_msg in q_msg_qs:
#         try:
#             logging.info(f'PushAPIHook: url: {q_msg.push_url}')
#             logging.info(q_msg.message)
#             r = requests.post(q_msg.push_url, headers=headers, data=q_msg.message.encode('utf-8'))
#             logging.info(f'POST Response: {r.status_code}; Content-type: {r.headers["content-type"]}')
#             if int(r.status_code) >= 500:
#                 logging.error(r.text)
#             elif int(r.status_code) == 401:
#                 logging.warning(r.text)
#             elif int(r.status_code) == 400:
#                 logging.error(r.text)
#             elif int(r.status_code) == 201 or int(r.status_code) == 200:
#                 logging.info(r.text)
#             else:
#                 logging.critical(f'Что-то прошло не так')
#                 logging.error(r.text)
#                 my_r.status = False

#         except requests.exceptions.RequestException as ex:
#             logging.error(f"Exception! {ex}")

#         q_msg.status = PushStatus.objects.get(id=2)
#         q_msg.date_sent = datetime.now()
#         q_msg.save()
#     return True


def pushlog(msg):
    if settings.PUSH_API_HOOK_DEBUG:
        logging.info(f'PushAPIHook: {msg}')
