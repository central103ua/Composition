import json
import time
import logging
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from rest_framework import generics, mixins
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from ekstrenka.mixins import HttpResponseMixin
from heartbeat.utils import is_json
from callcard.models import CallCard, CallStations, CallPriority, CallResult, CallRecord
from mis.models import Mis, Staff
from crew.models import Crew, CrewStatus
from accounts.permissions import IsMisUser
from pushapi.hooks import pushapi_hook
from chatbot.hooks import chatbot_hook

from .serializers import CallCardSerializer, CallRecordSerializer
from crew.api.serializers import CrewDairySerializer
from heartbeat.api.serializers import IntercallSerializer


class CallCardRudView(generics.RetrieveUpdateDestroyAPIView):
    #serializer_class = CallCardSerializer
    permission_classes = [IsMisUser]

    def put(self, request, *args, **kwargs):
        # logging.info(f'CallCard PUT; Content-Type: {request.META.get("CONTENT_TYPE")}')
        error_msg = {}
        slug = self.kwargs.get("slug")
        user = self.request.user
        mis_obj = Mis.objects.get(mis_user=user)
        mis_id = mis_obj.id
        logging.info(f'CallCard PUT; call_card_id: {slug}, user: {user.username}, mis: {mis_id}')
        if not 'application/json' in request.META.get("CONTENT_TYPE"):
            error_msg["CallCard"] = 'Conntent-Type: application/jason required'
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        j_response = json.loads('{"CallCard":[]}')
        try:
            j_request = json.loads(request.body)
            logging.info(json.dumps(j_request, indent=1, ensure_ascii=False))
        except:
            error_msg["CallCard"] = f'Bad JSON in Request. user: {user.username}, mis: {mis_id}'
            logging.error(request.body)
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

        call_card_l = j_request.get('CallCard', False)
        if call_card_l == False or type(call_card_l) != list or len(call_card_l) != 1:
            error_msg["CallCard"] = f'No CallCard in request. user: {user.username}, mis: {mis_id}'
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        cc_qs = CallCard.objects.filter(call_card_id=slug)
        if cc_qs.exists():
            cc_obj = cc_qs.first()
        else:
            error_msg["CallCard"] = f'Bad CallCard in URL. user: {user.username}, mis: {mis_id}'
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

        # Поїхали!
        cc_data = call_card_l[0]
        # for cc_data in j_request['CallCard']:
        #cc_obj = CallCard.objects.get(call_card_id=slug)
        cc_data['mis_id'] = cc_obj.mis_id.id
        cc_data['mis_user'] = cc_obj.mis_user.id
        cc_data['call_card_id'] = slug
        # backup call_comment & operator_id
        call_comment = cc_data.get("call_comment", None)
        if call_comment and call_comment.strip():
            call_comment = call_comment.strip()
            cc_data["call_comment"] = call_comment
        else:
            call_comment = None
            cc_data["call_comment"] = None

        cc_s = CallCardSerializer(cc_obj, data=cc_data)
        if cc_s.is_valid():
            cc_obj = cc_s.save()
        else:
            logging.error(f'CallCard PUT. IsValid exception. user: {user.username}, mis: {mis_id}')
            logging.error(cc_s.errors)
            return JsonResponse(cc_s.errors, status=status.HTTP_400_BAD_REQUEST)

        # print(f'#############   {cc_obj.crew_id} ###########')
        if cc_obj.crew_id:
            crewdairy_data = {}
            if cc_obj.call_station.id in [4, 5, 6, 7, 8, 9, 10, 11, 12, 13]:  # Бригада на ділі
                crew_status = CrewStatus.objects.get(crewstatus_name="На виїзді")
                crewdairy_data['crew_status'] = crew_status.id
                cc_obj.crew_id.crew_status = crew_status
            if cc_obj.call_station.id in [0, 1, 2, 3, 14, 15, 16]:
                crew_status = CrewStatus.objects.get(crewstatus_name="Вільна")
                crewdairy_data['crew_status'] = crew_status.id
                cc_obj.crew_id.crew_status = crew_status
            cc_obj.crew_id.save()
            crewdairy_data['crew_id'] = cc_obj.crew_id.id
            crewdairy_data['crew_slug'] = cc_obj.crew_id.crew_id
            crewdairy_data['call_card_id'] = cc_obj.call_card_id
            crewdairy_data['call_station'] = cc_obj.call_station.id
            crewdairy_data['mis_id'] = mis_id
            with transaction.atomic():
                crew_last_record = (cc_obj.crew_id.
                                    crewdairy_set.
                                    select_for_update().
                                    order_by("crew_dairy_seq").last())
                if crew_last_record:
                    crewdairy_data['crew_dairy_seq'] = crew_last_record.crew_dairy_seq + 1
                else:
                    crewdairy_data['crew_dairy_seq'] = 1
                crewdairy_s = CrewDairySerializer(data=crewdairy_data)
                if crewdairy_s.is_valid():
                    crewdairy_obj = crewdairy_s.save()
                else:
                    logging.error(f'CrewDairy. IsValid exception. user: {user.username}, mis: {mis_id}')
                    logging.error(crewdairy_s.errors)
                    return JsonResponse(crewdairy_s.errors, status=status.HTTP_400_BAD_REQUEST)

        cr_data = {}
        cr_data['mis_id'] = mis_id
        cr_data['call_station'] = cc_data['call_station']
        cr_data['card_id'] = cc_obj.id
        cr_data['start_datetime'] = cc_data.get('start_datetime', timezone.now())
        cr_data['end_datetime'] = cc_data.get('end_datetime', None)
        cr_data['operator_id'] = cc_data.get('operator_id', None)
        cr_data['mis_call_card_id'] = cc_data.get('mis_call_card_id', None)
        # restore CallComment
        if call_comment:
            cr_data['call_record_comment'] = call_comment
        cr_data['crew_id'] = cc_data.get('crew_id', None)
        with transaction.atomic():
            cr_last_record = (cc_obj.callrecord_set.
                              order_by("call_record_seq").
                              select_for_update().
                              last())
            cr_data['call_record_seq'] = cr_last_record.call_record_seq + 1
            cr_s = CallRecordSerializer(data=cr_data)
            if cr_s.is_valid():
                cr_obj = cr_s.save()
            else:
                logging.error(f'CallRecord PUT. IsValid exception. user: {user.username}, mis: {mis_id}')
                logging.error(cr_s.errors)
                return JsonResponse(cr_s.errors, status=status.HTTP_400_BAD_REQUEST)
        j_response["CallCard"].append(cc_s.data)

        # Proceed with API hooks
        pushapi_hook(cc_obj)
        chatbot_hook(cc_obj)

        # Proceed with related_cc
        if cc_obj.intercall:
            logging.info(f"CallCard PUT: Creating CallRecord for related_cc: {cc_obj.intercall.related_cc}")
            related_cc_qs = CallCard.objects.filter(call_card_id=cc_obj.intercall.related_cc)
            if related_cc_qs.exists():
                related_cc = related_cc_qs.first()
            else:
                logging.error(f'CallCard PUT: invalid related_cc slug:{cc_obj.intercall.related_cc}')

            # Processing related_cc
            related_cc_data = {}
            related_cc_data['mis_id'] = related_cc.mis_id.id
            related_cc_data['mis_user'] = related_cc.mis_user.id
            related_cc_data['call_card_id'] = related_cc.call_card_id
            related_cc_data['call_station'] = cc_data['call_station']
            related_cc_data['call_result'] = cc_data['call_result']
            related_cc_data['start_datetime'] = cc_data.get('start_datetime', timezone.now())
            related_cc_data['end_datetime'] = cc_data.get('end_datetime', None)
            # related_cc_data['call_priority'] = cc_data['call_priority']
            related_cc_data['operator_id'] = "SYSTEM"
            related_cc_s = CallCardSerializer(related_cc, data=related_cc_data)
            if related_cc_s.is_valid():
                related_cc = related_cc_s.save()
            else:
                logging.error(f'CallCard PUT. IsValid exception. user: {user.username}, mis: {mis_id}')
                logging.error(related_cc_s.errors)
                # return JsonResponse(related_cc_s.errors, status=status.HTTP_400_BAD_REQUEST)

            # Processing related_callecord
            related_cr_data = {}
            related_cr_data['mis_id'] = related_cc.mis_id.id
            related_cr_data['call_station'] = related_cc_data['call_station']
            related_cr_data['card_id'] = related_cc.id
            related_cr_data['start_datetime'] = related_cc_data.get('start_datetime', timezone.now())
            related_cr_data['end_datetime'] = related_cc_data.get('end_datetime', None)
            related_cr_data['operator_id'] = related_cc_data['operator_id']  # Staff.objects.filter(mis_id=related_cc.mis_id.id).filter(mis_staff_id="SYSTEM").first().id
            #related_cr_data['mis_call_card_id'] = cc_data.get('mis_call_card_id', None)
            # restore CallComment
            if call_comment:
                related_cr_data['call_record_comment'] = call_comment
            related_cr_data['crew_id'] = cc_data.get('crew_id', None)
            with transaction.atomic():
                related_cr_last_record = (related_cc.callrecord_set.
                                          order_by("call_record_seq").
                                          select_for_update().
                                          last())
                related_cr_data['call_record_seq'] = related_cr_last_record.call_record_seq + 1
                related_cr_s = CallRecordSerializer(data=related_cr_data)
                if related_cr_s.is_valid():
                    related_cr_obj = related_cr_s.save()
                else:
                    logging.error(f'CallRecord PUT. Intercall; IsValid exception. user: {user.username}, mis: {mis_id}')
                    logging.error(related_cr_s.errors)
                    # return JsonResponse(related_cr_s.errors, status=status.HTTP_400_BAD_REQUEST)

            # Create Intercall messge here!!!
            ic_data_j = {}
            ic_data_j['mis_to'] = related_cc.mis_id
            ic_data_j['mis_from'] = cc_obj.mis_id
            ic_data_j['related_cc'] = related_cc.call_card_id
            ic_data_j['callcard'] = cc_obj
            ic_data_j['status'] = 'Ready'
            ic_s = IntercallSerializer(data=ic_data_j)
            if ic_s.is_valid():
                ic_obj = ic_s.save()
                logging.info(f'Intercall created: {json.dumps(ic_s.data, indent=1, ensure_ascii=False)}')
            else:
                logging.error(f'CallRecord POST: IntercallSerializer. {ic_s.errors}')

        # Update MIS.date_modified
        mis_obj.save()
        logging.info(json.dumps(j_response, indent=1, ensure_ascii=False))
        logging.info(f'CallCard PUT; response: {status.HTTP_200_OK}, call_card_id: {slug}, user: {user.username}, mis: {mis_id}')
        return HttpResponse(json.dumps(j_response, ensure_ascii=False),
                            content_type="application/json",
                            status=status.HTTP_200_OK)


class CallCardView(generics.CreateAPIView):
    #serializer_class = CallCardSerializer
    permission_classes = [IsMisUser]

    def post(self, request, *args, **kwargs):
        error_msg = {}
        user = self.request.user
        mis_obj = Mis.objects.get(mis_user=user)
        logging.info(f'CallCard POST; user: {user.username}, mis: {mis_obj.id}')
        if not 'application/json' in request.META.get("CONTENT_TYPE"):
            error_msg["CallCard"] = 'Conntent-Type: application/jason required'
            logging.error(f'CallCard POST; user: {user.username}, mis: {mis_obj.id}')
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        try:
            j_request = json.loads(request.body)
            logging.info(json.dumps(j_request, indent=1, ensure_ascii=False))
        except:
            error_msg["CallCard"] = 'Bad JSON in Request'
            logging.error(request.body)
            logging.error(f'CallCard POST; user: {user.username}, mis: {mis_obj.id}')
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        call_card_l = j_request.get('CallCard', False)
        if call_card_l == False or type(call_card_l) != list or len(call_card_l) != 1:
            error_msg["CallCard"] = f'No CallCard list in request'
            logging.error(f'CallCard POST; user: {user.username}, mis: {mis_obj.id}')
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        j_response = json.loads('{"CallCard":[]}')

        # Поїхали!
        cc_data = call_card_l[0]
        cc_data_id = cc_data.get('id', False)
        if cc_data_id:
            error_msg["CallCard"] = 'Use PUT method to update CallCard'
            logging.error(f'CallCard POST; user: {user.username}, mis: {mis_obj.id}')
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        cc_data['mis_user'] = user.id
        # backup call_comment
        call_comment = cc_data.get("call_comment", None)
        if call_comment and call_comment.strip():
            call_comment = call_comment.strip()
            cc_data["call_comment"] = call_comment
        else:
            call_comment = None
            cc_data["call_comment"] = None

        cc_s = CallCardSerializer(data=cc_data)
        if cc_s.is_valid():
            cc_obj = cc_s.save()
        else:
            logging.error(f'CallCard POST. IsValid exception. user: {user.username}, mis: {mis_obj.id}')
            logging.error(cc_s.errors)
            return JsonResponse(cc_s.errors, status=status.HTTP_400_BAD_REQUEST)

        cr_data = {}
        cr_data['call_record_seq'] = 1
        cr_data['mis_id'] = cc_obj.mis_id.id
        cr_data['call_station'] = cc_data['call_station']
        cr_data['card_id'] = cc_obj.id
        cr_data['start_datetime'] = cc_data['start_datetime']
        cr_data['end_datetime'] = cc_data.get('end_datetime', None)
        cr_data['operator_id'] = cc_data.get('operator_id', None)
        # restore CallComment
        if call_comment:
            cr_data['call_record_comment'] = call_comment

        cr_data['crew_id'] = cc_data.get('crew_id', None)
        # logging.info(f"call_record: {cr_data['card_id']}")
        cr_s = CallRecordSerializer(data=cr_data)
        if cr_s.is_valid():
            #logging.info("CallRecord POST. Validated!!!")
            cr_obj = cr_s.save()
        else:
            logging.error("CallRecord POST. IsValid exception. This shoud have NEVER EVER happened")
            logging.error(f'user: {user.username}, mis: {mis_obj.id}')
            logging.error(cr_s.errors)
            return JsonResponse(cr_s.errors, status=status.HTTP_400_BAD_REQUEST)
        #
        # Process for Intercall message if any
        #
        if cc_obj.intercall:
            logging.info(f"CallCard POST: Creating Intercall CallCard for mis: {cc_obj.intercall.mis_to}")
            icc_data = (dict(cc_s.data)).copy()
            icc_data['mis_id'] = icc_data['intercall']['mis_to']
            mis_qs = Mis.objects.filter(id=icc_data['mis_id'])
            if mis_qs.exists():
                mis_obj = mis_qs.first()
                icc_data['mis_user'] = mis_obj.mis_user.id
            else:
                err = "CallCard POST. Interconect process. This shoud have NEVER EVER happened"
                logging.error(err)
                return JsonResponse(err, status=status.HTTP_400_BAD_REQUEST)

            icc_data['operator_id'] = 'SYSTEM'
            icc_data['intercall']['related_cc'] = icc_data['call_card_id']
            del icc_data['call_card_id']
            #icc_data['mis_call_card_id'] = "-1"
            # backup ICC icall_comment
            icall_comment = icc_data.get("call_comment", None)
            if icall_comment and icall_comment.strip():
                icall_comment = icall_comment.strip()
                icc_data["call_comment"] = icall_comment
            else:
                icall_comment = None
                icc_data["call_comment"] = None

            logging.info(json.dumps(icc_data, indent=1, ensure_ascii=False))
            icc_s = CallCardSerializer(data=icc_data)
            if icc_s.is_valid():
                icc_obj = icc_s.save()
            else:
                logging.error(f'CallCard POST. IsValid exception for InterCC. user: {user.username}, mis: {mis_obj.id}')
                logging.error(icc_s.errors)
                return JsonResponse(icc_s.errors, status=status.HTTP_400_BAD_REQUEST)

            # Proceed CallRecord for intercal CallCard
            icr_data = {}
            icr_data['call_record_seq'] = 1
            icr_data['mis_id'] = icc_obj.mis_id.id
            icr_data['call_station'] = icc_data['call_station']
            icr_data['card_id'] = icc_obj.id
            icr_data['start_datetime'] = icc_data['start_datetime']
            icr_data['end_datetime'] = icc_data.get('end_datetime', None)
            icr_data['operator_id'] = icc_data.get('operator_id', None)
            # restore ICC CallComment
            if icall_comment:
                icr_data['call_record_comment'] = icall_comment
            icr_data['crew_id'] = icc_data.get('crew_id', None)
            icr_s = CallRecordSerializer(data=icr_data)
            if icr_s.is_valid():
                #logging.info("CallRecord POST. Validated!!!")
                icr_obj = icr_s.save()
            else:
                logging.error("CallRecord POST. IsValid exception. This shoud have NEVER EVER happened")
                logging.error(f'user: {user.username}, mis: {mis_obj.id}')
                logging.error(cr_s.errors)
                return JsonResponse(cr_s.errors, status=status.HTTP_400_BAD_REQUEST)

            # Save related_cc to origin CallCard
            cc_obj.intercall.related_cc = icc_obj.call_card_id
            cc_obj.intercall.save()

            # Create Intercall messge here!!!
            ic_data_j = {}
            ic_data_j['mis_to'] = icc_obj.mis_id
            ic_data_j['mis_from'] = cc_obj.mis_id
            ic_data_j['related_cc'] = cc_obj.call_card_id
            ic_data_j['callcard'] = icc_obj
            ic_data_j['status'] = 'Ready'
            ic_s = IntercallSerializer(data=ic_data_j)
            if ic_s.is_valid():
                ic_obj = ic_s.save()
                logging.info(f'Intercall created: {json.dumps(ic_s.data, indent=1, ensure_ascii=False)}')
            else:
                logging.error(f'CallRecord POST: IntercallSerializer. {ic_s.errors}')

        # Proceed with API hooks
        pushapi_hook(cc_obj)

        out_cc_s = CallCardSerializer(cc_obj)
        j_response["CallCard"].append(out_cc_s.data)

        # Update MIS.date_modified
        mis_obj = Mis.objects.get(mis_user=user)
        mis_obj.save()
        logging.info(json.dumps(j_response, indent=1, ensure_ascii=False))
        logging.info(f'CallCard POST; response: {status.HTTP_201_CREATED}, user: {user.username}, mis: {mis_obj.id}')
        return HttpResponse(json.dumps(j_response, ensure_ascii=False),
                            content_type="application/json",
                            status=status.HTTP_201_CREATED)
