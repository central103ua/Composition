from __future__ import absolute_import, unicode_literals
import json
import time
import logging
import requests
from django.core.mail import send_mail
from datetime import date, time, tzinfo, timedelta, datetime
#import datetime
from django.conf import settings
from django.utils import timezone
from django.db import connection
from django.db.models import Count
from django.db.models import Q
from callcard.models import CallCard, CallRecord
from crew.models import Crew
from celery.decorators import task
from .models import DailyTest


@task(name="KhersonShiftReport")
def khersonShiftReport():
    if settings.DEBUG:
        mis_id = 30
    else:
        mis_id = 6
    today = date.today()
    yesterday = today - timedelta(days=1)
    t_08 = time(8, 0)
    start_datetime = datetime.combine(yesterday, t_08)
    end_datetime = datetime.combine(today, t_08)
    msgHeader = f"Хенсонській ЦЕМД та МК\n"
    msgHeader += f"Пеіод звіту: {start_datetime.strftime('%d/%m/%Y %H:%M')} - {end_datetime.strftime('%d/%m/%Y %H:%M')}\n"
    msgHeader += dayShiftReport(mis_id=mis_id, start_datetime=start_datetime, end_datetime=end_datetime)
    print(msgHeader)
    send_mail(
        subject=f'Kherson 24H shift report',
        message=msgHeader,
        from_email='central103@central103.org',
        recipient_list=['khersonshift@central103.org', ],
        fail_silently=False,
    )
    return True


def dayShiftReport(mis_id, start_datetime, end_datetime):
    er_call_qs = CallCard.objects.filter(Q(mis_id=mis_id) &
                                         Q(start_datetime__gte=start_datetime) &
                                         Q(start_datetime__lt=end_datetime) &
                                         Q(call_result__result_name__exact='Виклик бригади')
                                         ).order_by('start_datetime')

    city_call_qs = CallCard.objects.filter(Q(mis_id=mis_id) &
                                           Q(start_datetime__gte=start_datetime) &
                                           Q(start_datetime__lt=end_datetime) &
                                           Q(call_result__result_name__exact='Виклик бригади') &
                                           Q(call_address__location_type__locationtype_name__exact='місто')
                                           ).order_by('start_datetime')
    country_call_qs = CallCard.objects.filter(Q(mis_id=mis_id) &
                                              Q(start_datetime__gte=start_datetime) &
                                              Q(start_datetime__lt=end_datetime) &
                                              Q(call_result__result_name__exact='Виклик бригади') &
                                              Q(call_address__location_type__locationtype_name__exact='село')
                                              ).order_by('start_datetime')

    call_total = er_call_qs.count()
    logging.info(f'dayShiftReport:: MIS# {mis_id}. Виїздів бригад: {call_total}')
    msg = f'Всього виїздів: {call_total}\n'
    msg += f'З них у місті: {city_call_qs.count()}\n'
    msg += f'З них у селі: {country_call_qs.count()}\n\n'
    msg += "Виклики у місті:\n"

    num = 1
    msg += '№\tStartDatetime\tМісто\tВулиця\tБудівля\tТелефон\t\tcall_card_id\n'
    for er_call in city_call_qs:
        msg += f"{num}\t{er_call.start_datetime.strftime('%H:%M:%S')}\t{er_call.call_address.city}\t{er_call.call_address.street}\t{er_call.call_address.building}\t\t{er_call.caller_number}\t{er_call.call_card_id}\n"
        num += 1

    msg += "\nВиклики у селі:\n"
    num = 1
    msg += '№\tStartDatetime\tМісто\tВулиця\tБудівля\tТелефон\t\tcall_card_id\n'
    for er_call in country_call_qs:
        msg += f"{num}\t{er_call.start_datetime.strftime('%H:%M:%S')}\t{er_call.call_address.city}\t{er_call.call_address.street}\t{er_call.call_address.building}\t\t{er_call.caller_number}\t{er_call.call_card_id}\n"
        num += 1

    return msg


@task(name="TernopilNightShiftReport")
def ternopilNightShiftReport():
    if settings.DEBUG:
        mis_id = 30
    else:
        mis_id = 8
    today = date.today()
    yesterday = today - timedelta(days=1)
    t_08 = time(8, 0)
    t_20 = time(20, 0)
    start_datetime = datetime.combine(yesterday, t_20)
    end_datetime = datetime.combine(today, t_08)
    logging.info(f'ternopilNightShiftReport: {start_datetime.isoformat()}')
    logging.info(f'ternopilNightShiftReport: {end_datetime.isoformat()}')
    msgHeader = f"Зміна: {start_datetime.strftime('%d/%m/%Y %H:%M:%S')} - {end_datetime.strftime('%d/%m/%Y %H:%M:%S')}\n"
    msgHeader += shiftReport(mis_id=mis_id, start_datetime=start_datetime, end_datetime=end_datetime)
    print(msgHeader)
    send_mail(
        subject=f'Ternopil NIGHT shift report',
        message=msgHeader,
        from_email='central103@central103.org',
        recipient_list=['ternopilshift@central103.org', ],
        fail_silently=False,
    )
    return True


@task(name="TernopilDayShiftReport")
def ternopilDayShiftReport():
    if settings.DEBUG:
        mis_id = 30
    else:
        mis_id = 8
    today = date.today()
    yesterday = today - timedelta(days=1)
    t_08 = time(8, 0)
    t_20 = time(20, 0)
    start_datetime = datetime.combine(today, t_08)
    end_datetime = datetime.combine(today, t_20)
    logging.info(f'ternopilDayShiftReport: {start_datetime.isoformat()}')
    logging.info(f'ternopilDayShiftReport: {end_datetime.isoformat()}')
    msgHeader = f"Зміна: {start_datetime.strftime('%d/%m/%Y %H:%M:%S')} - {end_datetime.strftime('%d/%m/%Y %H:%M:%S')}\n"
    msgHeader += shiftReport(mis_id=mis_id, start_datetime=start_datetime, end_datetime=end_datetime)
    print(msgHeader)
    send_mail(
        subject=f'Ternopil DAY shift report',
        message=msgHeader,
        from_email='central103@central103.org',
        recipient_list=['ternopilshift@central103.org', ],
        fail_silently=False,
    )
    return True


def shiftReport(mis_id, start_datetime, end_datetime):
    er_call_qs = CallCard.objects.filter(Q(mis_id=mis_id) &
                                         Q(start_datetime__gte=start_datetime) &
                                         Q(start_datetime__lt=end_datetime) &
                                         Q(call_result__result_name__exact='Виклик бригади')
                                         ).order_by('start_datetime')

    q_cancel_str = "select callcard_callcard.start_datetime, callcard_callcard.call_card_id, \
                    callcard_callcard.operator_id_id, callcard_callcard.caller_number from callcard_callcard \
                    inner join callcard_callrecord on (callcard_callrecord.card_id_id=callcard_callcard.id) \
                    where callcard_callrecord.call_station_id=16 \
                    and callcard_callcard.mis_id_id = %s \
                    and callcard_callcard.start_datetime >= %s \
                    and callcard_callcard.start_datetime < %s \
                    order by date(callcard_callcard.start_datetime) desc"

    cursor = connection.cursor()
    start_datetime_s = start_datetime.strftime('%Y-%m-%d %H:%M:%S')
    end_datetime_s = end_datetime.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(q_cancel_str, [mis_id, start_datetime_s, end_datetime_s])
    qs_cancel = cursor.fetchall()
    cancel_num = len(qs_cancel)
    call_total = cancel_num + er_call_qs.count()

    logging.info(f'shiftReport:: MIS# {mis_id}. Виїздів бригад: {er_call_qs.count()}')
    msg = f'Всього викликів: {call_total}; Відмінені: {cancel_num}; Виконані: {er_call_qs.count()}\n\n'
    num = 1
    msg += '№\tStartDatetime\tОператор103\tТелефон\t\tcall_card_id\n'
    for er_call in er_call_qs:
        msg += f"{num}\t{er_call.start_datetime.strftime('%H:%M:%S')}\t{er_call.operator_id.family_name}\t\t{er_call.caller_number}\t{er_call.call_card_id}\n"
        num += 1

    num = 1
    msg += '\n\nВідмінені:\n'
    for q_cancel in qs_cancel:
        msg += f"{num}\t{q_cancel[0].strftime('%H:%M:%S')}\t{q_cancel[2]}\t{q_cancel[3]}\t{q_cancel[1]}\n"
        num += 1

    return msg


@task(name="DailyTest")
def dailyTest():
    qa_date = (datetime.now() - timedelta(days=1)).date()
    misTest_qs = DailyTest.objects.filter(is_active=True).order_by('mis')
    for misTest in misTest_qs:
        report = "Daily Report\n"
        mis_msg = f'\nMIS #{misTest.mis.id} ({misTest.mis.mis_name}): \n'
        if misTest.mis.id == 3 and misTest.steel_city == True:
            mis_msg += 'Для м.Запоріжжя \n'

        if misTest.call_count:
            mis_msg += (" -" + callCount(mis=misTest.mis, qa_date=qa_date))
        if misTest.call_complete:
            mis_msg += (" -" + call_complete(mis=misTest.mis, qa_date=qa_date))
        if misTest.er_no_crew:
            mis_msg += (" -" + er_no_crew(mis=misTest.mis, qa_date=qa_date, steel_city=misTest.steel_city))
        if misTest.active_crew:
            mis_msg += (" -" + active_crew(mis=misTest.mis, qa_date=qa_date))
        report += mis_msg
        sendReport(qa_date, report, misTest)

    return True


def active_crew(mis, qa_date):
    crew_qs = Crew.objects.filter(Q(mis_id=mis) &
                                  Q(shift_end__contains=qa_date) &
                                  Q(is_active=True)
                                  ).order_by('timestamp')
    er_msg = f'Бригади що досі вільні: {crew_qs.count()}\n'
    for crew in crew_qs:
        er_msg += f' -- https://central103.org/sys/crew/{crew.crew_id}/\n'

    return er_msg


def er_no_crew(mis, qa_date, steel_city):
    if mis.id == 3:
        if steel_city:
            er_call_qs = CallCard.objects.filter(Q(mis_id=mis) &
                                                 Q(start_datetime__contains=qa_date) &
                                                 Q(call_result__result_name__exact='Виклик бригади') &
                                                 Q(call_address__district__exact='Запорізький')
                                                 ).order_by('start_datetime')
        else:
            er_call_qs = CallCard.objects.filter(Q(mis_id=mis) &
                                                 Q(start_datetime__contains=qa_date) &
                                                 Q(call_result__result_name__exact='Виклик бригади')
                                                 ).exclude(call_address__district__exact='Запорізький').order_by('start_datetime')
    else:
        er_call_qs = CallCard.objects.filter(Q(mis_id=mis) &
                                             Q(start_datetime__contains=qa_date) &
                                             Q(call_result__result_name__exact='Виклик бригади')
                                             ).order_by('start_datetime')
    er_msg = f'Всього виїздів бригад: {er_call_qs.count()}\n'
    no_crew_list = []
    no_crew_confirm_list = []
    no_crew_arrive_list = []
    for er_call in er_call_qs:
        crew_confirm = False
        crew_arrive = False
        if er_call.crew_id is None:
            no_crew_list.append(er_call)
        else:
            er_call_record_qs = CallRecord.objects.filter(Q(card_id=er_call.id)
                                                          ).order_by('start_datetime')
            for er_call_record in er_call_record_qs:
                if er_call_record.call_station.station_name == 'Бригада':
                    crew_confirm = True
                if er_call_record.call_station.station_name == 'На виїзді':
                    crew_arrive = True
            if crew_confirm == False:
                no_crew_confirm_list.append(er_call)
            elif crew_arrive == False:
                no_crew_arrive_list.append(er_call)

    er_msg += f' --Викликів бригади без бригади: {len(no_crew_list)}\n'
    for no_crew in no_crew_list:
        er_msg += f' --- https://central103.org/sys/callcard/{no_crew.call_card_id}/  start_datetime: {no_crew.start_datetime}\n'
    er_msg += f' --Викликів бригади без підтвердження бригади: {len(no_crew_confirm_list)}\n'
    for no_crew_confirm in no_crew_confirm_list:
        er_msg += f' --- https://central103.org/sys/callcard/{no_crew_confirm.call_card_id}/  start_datetime: {no_crew_confirm.start_datetime}\n'
    er_msg += f' --Викликів бригади без виїзду бригади: {len(no_crew_arrive_list)}\n'
    for no_crew_arrive in no_crew_arrive_list:
        er_msg += f' --- https://central103.org/sys/callcard/{no_crew_arrive.call_card_id}/  start_datetime: {no_crew_arrive.start_datetime}\n'

    return er_msg


def call_complete(mis, qa_date):
    noArchive_qs = CallCard.objects.filter(Q(mis_id=mis) &
                                           Q(start_datetime__contains=qa_date)).exclude(
        call_station__station_name__exact='Архів')

    noArchive_list = ""
    if noArchive_qs.count() != 0:
        for noArchive in noArchive_qs:
            noArchive_list += f' -- https://central103.org/sys/callcard/{noArchive.call_card_id}/  start_datetime: {noArchive.start_datetime}\n'
    noArchive_msg = f'Не зданих в Архів: {noArchive_qs.count()}\n{noArchive_list}'
    return noArchive_msg


def callCount(mis, qa_date):
    callCard_qs = CallCard.objects.filter(Q(mis_id=mis) &
                                          Q(start_datetime__contains=qa_date))
    call_count_msg = f'Кількість звернень: {callCard_qs.count()}\n'
    return call_count_msg


def sendReport(qa_date, report, misTest):
    header_msg = f'Date: {qa_date}\n'
    footer_msg = '\n\nSensirely yours,\n QA Robot'
    mail_msg = header_msg + report + footer_msg
    logging.info("Sending email report")
    # logging.info(mail_msg)
    send_mail(
        subject=f'Central103 Daily Report: {misTest.mis.mis_name}',
        message=mail_msg,
        from_email='central103@central103.org',
        recipient_list=[misTest.email, ],
        fail_silently=False,
    )
    return True


# def archive_qa():
#     qa_date = (datetime.now() - timedelta(days=1)).date()
#     callCard_qs = CallCard.objects.all().filter(Q(mis_id=3) &
#                                                 Q(start_datetime__contains=qa_date))
#     noArchive_qs = CallCard.objects.all().filter(Q(mis_id=3) &
#                                                  Q(start_datetime__contains=qa_date)).exclude(
#         call_station__station_name__exact='Архів')

#     header_msg = f'Date: {qa_date}\n'
#     mis_msg = f'MIS #3:\n'
#     numCalls_msg = f'Number of calls: {callCard_qs.count()}\n'
#     noArchive_list = ""
#     if noArchive_qs.count() != 0:
#         for noArchive in noArchive_qs:
#             noArchive_list += f' -CallCard: {noArchive.call_card_id}: start_datetime: {noArchive.start_datetime}\n'
#     noArchive_msg = f'Calls NoArchive: {noArchive_qs.count()}\n{noArchive_list}'
#     mail_msg = header_msg + mis_msg + numCalls_msg + noArchive_msg
#     send_mail(
#         subject='Central103: QA robot',
#         message=mail_msg,
#         from_email='central103@central103.org',
#         recipient_list=['vlad@central103.org'],
#         fail_silently=False,
#     )
#     logging.info("QA_ROBOT: Done")
#     return True
