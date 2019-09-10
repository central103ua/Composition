import json
import time
import logging
from collections import Mapping, OrderedDict
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from rest_framework import generics, mixins
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ErrorDetail, ValidationError
from django.db import transaction
from mis.models import Mis
from crew.models import Crew
from .serializers import CrewSerializer, CrewTeamSerializer, CrewDairySerializer
from accounts.permissions import IsMisUser


class CrewRudView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CrewSerializer
    permission_classes = [IsMisUser]

    def get_object(self):
        pk = self.kwargs.get("slug")
        return Crew.objects.get(crew_id=pk)

    def put(self, request, *args, **kwargs):
        slug = self.kwargs.get("slug")
        user = self.request.user
        error_msg = {}
        mis_obj = Mis.objects.get(mis_user=user)
        mis_id = mis_obj.id
        logging.info(f'Crew PUT: user: {user.username}, mis: {mis_id}, crew_id: {slug}')
        logging.info(f'Crew PUT: Content-Type: {request.META.get("CONTENT_TYPE")}')
        j_response = json.loads('{"Crew":[]}')
        try:
            j_request = json.loads(request.body)
            logging.info(json.dumps(j_request, indent=1, ensure_ascii=False))
        except:
            logging.error(request.body)
            error_msg["Crew PUT"] = 'Bad JSON in Request'
            logging.error(f'{error_msg}; mis: {mis_id}')
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        if not 'Crew' in j_request:
            error_msg["Crew PUT"] = "No Crew in request"
            logging.error(f'{error_msg}; mis: {mis_id}')
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        cr_qs = Crew.objects.filter(crew_id=slug)
        if cr_qs.exists():
            cr_obj = cr_qs.first()
        else:
            error_msg["Crew PUT"] = "Bad Crew ID (slug)"
            logging.error(f'{error_msg}; mis: {mis_id}')
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

        for cr_data in j_request['Crew']:
            #status_data = {}
            # status_data['is_active'] = "True"
            # status_data['crew_status'] = ""
            if mis_id != cr_obj.mis_id.id:
                error_msg["Crew PUT"] = f'mis_id[slug] != mis_id[user] [{cr_obj.mis_id.id} != {mis_id}]'
                logging.error(f'{error_msg}; mis: {mis_id}')
                return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
            # check if Crew is_active
            active_b = "True"
            if cr_obj.is_active == False:
                active_b = cr_data.get("is_active", "myNone")
                # if no is_active statement -> BAD
                if active_b == "myNone":
                    error_msg["Crew PUT"] = f'Crew {slug} is not Active'
                    logging.error(f'{error_msg}; mis: {mis_id}')
                    return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
                # accept repeat is_active = False
                if active_b == "False":
                    logging.warning("Crew PUT: Set is_active=False AGAIN")
                    cr_data = {}
                    cr_data['is_active'] = "False"

            #cr_data['mis_id'] = mis_id
            cr_data['crew_id'] = slug
            # print(cr_data)
            cr_s = CrewSerializer(cr_obj, data=cr_data)
            if cr_s.is_valid():
                logging.info("Crew PUT. Validated!!!")
                cr_obj = cr_s.save()
            else:
                logging.error(f'Crew PUT. IsValid exception: {cr_s.errors}')
                return JsonResponse(cr_s.errors, status=status.HTTP_400_BAD_REQUEST)
            j_response["Crew"].append(cr_s.data)

            crewdairy_data = {}
            crewdairy_data['crew_id'] = cr_obj.id
            crewdairy_data['crew_slug'] = cr_obj.crew_id
            crewdairy_data['is_active'] = cr_obj.is_active
            crewdairy_data['mis_id'] = mis_id
            crewdairy_data['crew_status'] = cr_obj.crew_status.id
            crewdairy_data['call_station'] = 4
            with transaction.atomic():
                crew_last_record = (cr_obj.crewdairy_set.
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
                    return JsonResponse(cr_s.errors, status=status.HTTP_400_BAD_REQUEST)

        mis_obj.save()
        logging.info(json.dumps(j_response, indent=1, ensure_ascii=False))
        return HttpResponse(json.dumps(j_response, ensure_ascii=False),
                            content_type="application/json",
                            status=status.HTTP_200_OK)


class CrewView(generics.CreateAPIView):
    serializer_class = CrewSerializer
    permission_classes = [IsMisUser]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        error_msg = {}
        mis_obj = Mis.objects.get(mis_user=user)
        mis_id = mis_obj.id
        logging.info(f'Crew GET: user: {user.username}, mis: {mis_id}')
        logging.info(f'Crew GET: Content-Type: {request.META.get("CONTENT_TYPE")}')
        j_response = json.loads('{"Crew":[]}')

        qs = Crew.objects.filter(mis_id=mis_obj.id, is_active="True").order_by('id')
        for crew_obj in qs:
            crew_s = CrewSerializer(crew_obj)
            j_response["Crew"].append(crew_s.data)

        logging.info(json.dumps(j_response, indent=1, ensure_ascii=False))
        return HttpResponse(json.dumps(j_response, ensure_ascii=False),
                            content_type="application/json",
                            status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        logging.info("Crew: POST")
        error_msg = {}
        user = self.request.user
        mis_obj = Mis.objects.get(mis_user=user)
        logging.info(f'Crew POST: user: {user.username}, mis: {mis_obj.id}')
        logging.info(f'Crew POST: Content-Type: {request.META.get("CONTENT_TYPE")}')
        try:
            j_request = json.loads(request.body)
            logging.info(json.dumps(j_request, indent=1, ensure_ascii=False))
        except:
            logging.error(request.body)
            error_msg["Crew POST"] = 'Bad JSON in Request'
            logging.error(json.dumps(error_msg))
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        if not 'Crew' in j_request:
            error_msg["Crew POST"] = 'No Crew in reques'
            logging.error(json.dumps(error_msg))
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

        mis_id = mis_obj.id
        j_response = json.loads('{"Crew":[]}')
        for crew_data in j_request['Crew']:
            crew_data['mis_id'] = mis_id
            if 'id' in crew_data:
                error_msg["Crew POST"] = 'Use PUT method to update Crew record'
                logging.error(json.dumps(error_msg))
                return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
            if 'crew_id' in crew_data:
                error_msg["Crew POST"] = 'Use PUT method to update Crew record'
                logging.error(json.dumps(error_msg))
                return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

            cr_s = CrewSerializer(data=crew_data)
            if cr_s.is_valid():
                logging.info("Crew POST. Crew Validated!!!")
            else:
                logging.error("Crew POST. IsValid exception")
                logging.error(json.dumps(cr_s.errors))
                return JsonResponse(cr_s.errors, status=status.HTTP_400_BAD_REQUEST)

            crew_team = crew_data.get('crew_team', False)
            if crew_team:
                cr_obj = cr_s.save()
                crew_team_s = CrewTeamSerializer(data=crew_team,
                                                 crew_id=cr_obj.id,
                                                 mis_id=mis_id, many=True)
                if crew_team_s.is_valid():
                    logging.info("Crew POST. CrewTeam Validated")
                    crew_team_s.save()
                else:
                    logging.error("Crew POST. CrewTeam IsValid exception")
                    logging.error(json.dumps(crew_team_s.errors))
                    cr_obj.is_active = False
                    cr_obj.save()
                    cr_obj.delete()
                    return JsonResponse(crew_team_s.errors, safe=False, status=status.HTTP_400_BAD_REQUEST)
            else:
                error_msg["Crew POST"] = 'No crew_team in request'
                logging.error(json.dumps(error_msg))
                return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
            crew_d = cr_s.data.copy()
            crew_d['crew_team'] = crew_team_s.data
            j_response["Crew"].append(crew_d)

            crewdairy_data = {}
            crewdairy_data['crew_id'] = cr_obj.id
            crewdairy_data['crew_slug'] = cr_obj.crew_id
            crewdairy_data['is_active'] = cr_obj.is_active
            crewdairy_data['mis_id'] = mis_id
            crewdairy_data['crew_dairy_seq'] = 1
            crewdairy_data['crew_status'] = cr_obj.crew_status.id
            crewdairy_data['call_station'] = 4
            crewdairy_s = CrewDairySerializer(data=crewdairy_data)
            if crewdairy_s.is_valid():
                crewdairy_obj = crewdairy_s.save()
            else:
                logging.error(f'CrewDairy. IsValid exception. user: {user.username}, mis: {mis_obj.id}')
                logging.error(crewdairy_s.errors)
                return JsonResponse(cr_s.errors, status=status.HTTP_400_BAD_REQUEST)

        logging.info(json.dumps(j_response, indent=1, ensure_ascii=False))
        return HttpResponse(json.dumps(j_response, ensure_ascii=False),
                            content_type="application/json",
                            status=status.HTTP_201_CREATED)


# def myerror(exc):
#     detail = exc
#     if isinstance(detail, Mapping):
#         # If errors may be a dict we use the standard {key: list of values}.
#         # Here we ensure that all the values are *lists* of errors.
#         ret = {
#             key: value if isinstance(value, (list, Mapping)) else [value]
#             for key, value in detail.items()
#         }
#         print(f'3: {ret}')
#         return ret
#     elif isinstance(detail, list):
#         # Errors raised as a list are non-field errors.
#         ret = {
#             api_settings.NON_FIELD_ERRORS_KEY: detail
#         }
#         print(f'4: {ret}')
#         return ret
#     # Errors raised as a string are non-field errors.
#     ret = {
#         api_settings.NON_FIELD_ERRORS_KEY: [detail]
#     }
#     print(f'5: {ret}')
#     return ret
