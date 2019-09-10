import json
import logging
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from django.shortcuts import render
from rest_framework import generics, mixins
from rest_framework.settings import api_settings

from ekstrenka.mixins import HttpResponseMixin
from heartbeat.utils import is_json

from accounts.models import Permission
from mis.models import Facility, Mis, SysAddress, Staff, Cars
from mis.models import StaffTitle, StaffQualification, FacilityType
from .serializers import MisSerializer, CMisSerializer, CarSerializer
from .serializers import StaffSerializer, FacilitySerializer, SysAddressSerializer
from accounts.permissions import IsMisUser
from rest_framework.fields import get_error_detail, set_value

from django.contrib.auth import get_user_model
User = get_user_model()


class MisCreateView(generics.CreateAPIView):
    serializer_class = CMisSerializer
    #permission_classes = [IsSuperuserOrMis]

    def post(self, request, *args, **kwargs):
        logging.info("MisCreateView: POST")
        logging.info(f'Content-Type: {request.META.get("CONTENT_TYPE")}')
        user = self.request.user
        logging.info(f'user: {user.username}')
        try:
            j_request = json.loads(request.body)
            logging.info(json.dumps(j_request, indent=1, ensure_ascii=False))
        except:
            logging.error(request.body)
            return HttpResponse("Bad JSON in Request", status=status.HTTP_400_BAD_REQUEST)

        j_facility = j_request.get('mis_facility')
        j_request['mis_facility'] = "0"
        mis_s = CMisSerializer(data=j_request)
        logging.info("MisCreateView POST. MIS Validating")
        if mis_s.is_valid():
            logging.info("MisCreateView POST. MIS Validated")
            mis_obj = mis_s.save()
        else:
            logging.error("MisCreateView POST. MIS IsValid exception")
            logging.error(mis_s.errors)
            return HttpResponse(mis_s.errors, status=status.HTTP_400_BAD_REQUEST)
        j_facility['mis_id'] = mis_obj.id

        facility_s = FacilitySerializer(data=j_facility)
        logging.info("MisCreateView POST. Facility Validating")
        if facility_s.is_valid():
            logging.info("MisCreateView POST. Facility Validated")
            facility_obj = facility_s.save()
        else:
            logging.error("MisCreateView POST. Facility isValid exception")
            logging.error(facility_s.errors)
            return HttpResponse(facility_s.errors, status=status.HTTP_400_BAD_REQUEST)

        mis_obj.mis_facility = facility_obj.id
        mis_obj.save()
        mis_s = CMisSerializer(mis_obj)
        logging.info(json.dumps(mis_s.data, indent=1, ensure_ascii=False))
        return HttpResponse(json.dumps(mis_s.data, ensure_ascii=False),
                            status=status.HTTP_201_CREATED)


class UserCreateView(generics.CreateAPIView):
    #permission_classes = [IsSuperuserOrMis]

    def post(self, request, *args, **kwargs):
        logging.info("UserCreateView: POST")
        logging.info(f'Content-Type: {request.META.get("CONTENT_TYPE")}')
        j_user = json.loads(request.body)
        is_staff = bool(j_user.get("is_staff", False))
        logging.info(f"is_staff: {is_staff}")
        qs = User.objects.filter(username=j_user['username'])
        if qs.exists():
            user_obj = qs.first()
            logging.info(f'User: {user_obj.username} exists. ID: {user_obj.id}')
        else:
            user_obj = User(username=j_user['username'], is_staff=is_staff)
            user_obj.set_password(j_user['password'])
            user_obj.save()
            perms = j_user.get("permission", False)
            if perms:
                for perm in perms:
                    logging.info(f"Looking PERMISSION: user: {user_obj.username}, permission: {perm}")
                    # permission = Permission.objects.get(codename=perm)
                    # print(f"Found PERMISSION: user: {user_obj.username}, permission: {permission}")
                    # user_obj.user_permissions.add(permission)
                    permission_qs = Permission.objects.filter(codename=perm)
                    if permission_qs.exists():
                        permission = permission_qs.first()
                        logging.info(f"Found PERMISSION: user: {user_obj.username}, permission: {permission}")
                        user_obj.user_permissions.add(permission)
                    else:
                        logging.info(f"NOT Found PERMISSION: user: {user_obj.username}, permission: {perm}")

            user_obj.save()

        s_response = f'{{"userID":"{user_obj.id}", "username":"{user_obj.username}"}}'
        logging.info(s_response)
        response = HttpResponse(s_response, status=status.HTTP_201_CREATED)
        return response


class FacilityCreateView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FacilitySerializer
    permission_classes = [IsMisUser]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        # if user.is_staff | user.is_superuser:
        #     return HttpResponse(f'Operation not permited for user: {user.username}',
        #                         status=status.HTTP_403_FORBIDDEN)
        mis_obj = Mis.objects.get(mis_user=user)
        logging.info(f'Facility: GET, Content-Type: {request.META.get("CONTENT_TYPE")}, user: {user.username}, mis: {mis_obj.id}')
        j_response = json.loads('{"Facility":[]}')
        qs = Facility.objects.filter(mis_id=mis_obj.id).order_by('id')
        for facility_obj in qs:
            facility_s = FacilitySerializer(facility_obj)
            j_response["Facility"].append(facility_s.data)

        logging.info(json.dumps(j_response, indent=1, ensure_ascii=False))
        # return JsonResponse(j_response, status=status.HTTP_200_OK)
        return HttpResponse(json.dumps(j_response, ensure_ascii=False),
                            content_type="application/json",
                            status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        #logging.info(f'Content-Type: {request.META.get("CONTENT_TYPE")}')
        user = self.request.user
        error_msg = {}
        # if user.is_staff | user.is_superuser:
        #     return HttpResponse(f'Operation not permited for user: {user.username}',
        #                         status=status.HTTP_403_FORBIDDEN)
        mis_obj = Mis.objects.get(mis_user=user)
        logging.info(f'FacilityCreateView: POST. user: {user.username}, mis: {mis_obj.id}')
        try:
            j_request = json.loads(request.body)
            logging.info(json.dumps(j_request, indent=1, ensure_ascii=False))
        except:
            error_msg["Facility POST"] = 'Bad JSON in Request'
            logging.error(request.body)
            logging.error(f'Facility POST. user: {user.username}, mis: {mis_obj.id}')
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        if not 'Facility' in j_request:
            logging.error('No Facility in request')
            return HttpResponse("No Facility in request", status=status.HTTP_400_BAD_REQUEST)

        j_response = json.loads('{"Facility":[]}')
        new_facility = 0
        update_facility = 0
        total_facility = 0
        for j_facility in j_request['Facility']:
            facility_obj = None
            if j_facility.get('id', False):
                del j_facility['id']
            if not j_facility.get('mis_facility_id', False):
                error_msg["Facility POST"] = "mis_facility_id is missing"
                logging.error(f'user: {user.username}, mis: {mis_obj.id}')
                logging.error(error_msg)
                return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

            j_facility['mis_id'] = mis_obj.id
            facility_q = Facility.objects.filter(mis_id=mis_obj.id,
                                                 mis_facility_id=j_facility['mis_facility_id'])
            if facility_q.exists():
                facility_obj = facility_q.first()
                facility_s = FacilitySerializer(facility_obj, data=j_facility)
                update_facility += 1
            else:
                facility_s = FacilitySerializer(data=j_facility)
                new_facility += 1

            #logging.info("FacilityCreateView POST. Facility Validating")
            if facility_s.is_valid():
                #logging.info("FacilityCreateView POST. Facility Validated")
                facility_obj = facility_s.save()
            else:
                error_msg["Facility POST"] = "Facility isValid exception"
                logging.error(f'user: {user.username}, mis: {mis_obj.id}')
                logging.error(error_msg)
                logging.error(facility_s.errors)
                return JsonResponse(facility_s.errors, status=status.HTTP_400_BAD_REQUEST)

            j_response["Facility"].append(facility_s.data)
            total_facility += 1

        #logging.info(json.dumps(j_response, indent=1, ensure_ascii=False))
        logging.info(f'FacilityCreateView: POST. user: {user.username}, mis: {mis_obj.id}')
        logging.info(f'FacilityCreateView: loaded {total_facility}; {new_facility} new, {update_facility} updated.')
        return HttpResponse(json.dumps(j_response, ensure_ascii=False),
                            content_type="application/json",
                            status=status.HTTP_201_CREATED)


class StaffCreateView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StaffSerializer
    permission_classes = [IsMisUser]

    def get(self, request, *args, **kwargs):
        logging.info("StaffCreateView: GET")
        logging.info(f'Content-Type: {request.META.get("CONTENT_TYPE")}')
        user = self.request.user
        mis_obj = Mis.objects.get(mis_user=user)
        logging.info(f'user: {user.username}, mis: {mis_obj.id}')

        j_response = json.loads('{"Staff":[]}')
        qs = Staff.objects.filter(mis_id=mis_obj.id).order_by('id')
        for staff_obj in qs:
            staff_s = StaffSerializer(staff_obj)
            j_response["Staff"].append(staff_s.data)

        logging.info(json.dumps(j_response, indent=1, ensure_ascii=False))
        return HttpResponse(json.dumps(j_response, ensure_ascii=False),
                            content_type="application/json",
                            status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        logging.info(f'StaffCreateView: POST. Content-Type: {request.META.get("CONTENT_TYPE")}')
        error_msg = {}
        #logging.info(f'Content-Type: {request.META.get("CONTENT_TYPE")}')
        user = self.request.user
        # if user.is_staff | user.is_superuser:
        #     return HttpResponse(f'Operation not permited for user: {user.username}',
        #                         status=status.HTTP_403_FORBIDDEN)
        mis_obj = Mis.objects.get(mis_user=user)
        logging.info(f'user: {user.username}, mis: {mis_obj.id}')
        try:
            j_request = json.loads(request.body)
            logging.info(json.dumps(j_request, indent=1, ensure_ascii=False))
        except:
            error_msg["Staff POST"] = 'Bad JSON in Request'
            logging.error(request.body)
            logging.error(f'Staff POST. user: {user.username}, mis: {mis_obj.id}')
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        if not 'Staff' in j_request:
            error_msg["Staff POST"] = f'No Staff in request'
            logging.error(f'Staff POST; user: {user.username}, mis: {mis_obj.id}')
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        j_response = json.loads('{"Staff":[]}')
        new_staff = 0
        updated_staff = 0
        total_staff = 0
        for j_staff in j_request['Staff']:
            staff_obj = None
            if j_staff.get('id', False):
                del j_staff['id']
            if j_staff.get('facility_id', False):
                del j_staff['facility_id']
            j_staff['mis_id'] = mis_obj.id
            mis_staff_id = j_staff.get('mis_staff_id', False)
            # If Staff object exists
            if mis_staff_id:
                staff_q = Staff.objects.filter(mis_id=mis_obj.id,
                                               mis_staff_id=mis_staff_id)
                if staff_q.exists():
                    staff_obj = staff_q.first()
                    staff_s = StaffSerializer(staff_obj, data=j_staff)
                    updated_staff += 1
                else:
                    staff_s = StaffSerializer(data=j_staff)
                    new_staff += 1
            else:
                error_msg["Staff POST"] = "Staff mis_staff_id required"
                logging.error(f'user: {user.username}, mis: {mis_obj.id}')
                logging.error(error_msg)
                return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

            if staff_s.is_valid():
                #logging.info("StaffCreateView POST. Staff Validated")
                staff_obj = staff_s.save()
            else:
                error_msg["Staff POST"] = "Staff isValid exception"
                logging.error(f'user: {user.username}, mis: {mis_obj.id}')
                logging.error(error_msg)
                logging.error(staff_s.errors)
                return JsonResponse(staff_s.errors, status=status.HTTP_400_BAD_REQUEST)

            j_response["Staff"].append(staff_s.data)
            total_staff += 1

        #logging.info(json.dumps(j_response, indent=1, ensure_ascii=False))
        logging.info(f'user: {user.username}, mis: {mis_obj.id}')
        logging.info(f'StaffCreateView: loaded {total_staff}; {new_staff} new, {updated_staff} updated')
        return HttpResponse(json.dumps(j_response, ensure_ascii=False),
                            content_type="application/json",
                            status=status.HTTP_201_CREATED)


class CarCreateView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CarSerializer
    permission_classes = [IsMisUser]

    def get(self, request, *args, **kwargs):
        logging.info("CarCreateView: GET")
        logging.info(f'Content-Type: {request.META.get("CONTENT_TYPE")}')
        user = self.request.user
        mis_obj = Mis.objects.get(mis_user=user)
        logging.info(f'user: {user.username}, mis: {mis_obj.id}')

        j_response = json.loads('{"Cars":[]}')
        qs = Cars.objects.filter(mis_id=mis_obj.id).order_by('id')
        for car_obj in qs:
            car_s = CarSerializer(car_obj)
            j_response["Cars"].append(car_s.data)

        logging.info(json.dumps(j_response, indent=1, ensure_ascii=False))
        return HttpResponse(json.dumps(j_response, ensure_ascii=False),
                            content_type="application/json",
                            status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        logging.info("CarCreateView: POST")
        error_msg = {}
        user = self.request.user
        mis_obj = Mis.objects.get(mis_user=user)
        logging.info(f'user: {user.username}, mis: {mis_obj.id}')
        try:
            j_request = json.loads(request.body)
            logging.info(json.dumps(j_request, indent=1, ensure_ascii=False))
        except:
            error_msg["Cars POST"] = 'Bad JSON in Request'
            logging.error(request.body)
            logging.error(f'Cars POST. user: {user.username}, mis: {mis_obj.id}')
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        if not 'Cars' in j_request:
            error_msg["Cars POST"] = f'No Cars in request'
            logging.error(f'Cars POST; user: {user.username}, mis: {mis_obj.id}')
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

        j_response = json.loads('{"Cars":[]}')
        new_car = 0
        updated_car = 0
        total_car = 0
        for j_car in j_request['Cars']:
            car_obj = None
            if j_car.get('id', False):
                del j_car['id']
            if j_car.get('facility_id', False):
                del j_car['facility_id']
            j_car['mis_id'] = mis_obj.id
            mis_car_id = j_car.get('mis_car_id', False)
            # If Car object exists
            if mis_car_id:
                car_q = Cars.objects.filter(mis_id=mis_obj.id,
                                            mis_car_id=mis_car_id)
                if car_q.exists():
                    car_obj = car_q.first()
                    car_s = CarSerializer(car_obj, data=j_car)
                    updated_car += 1
                else:
                    car_s = CarSerializer(data=j_car)
                    new_car += 1
            else:
                error_msg["Cars POST"] = "Cars mis_car_id required"
                logging.error(f'user: {user.username}, mis: {mis_obj.id}')
                logging.error(error_msg)
                return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
            if car_s.is_valid():
                #logging.info("CarCreateView POST. Car Validated")
                car_obj = car_s.save()
            else:
                error_msg["Cars POST"] = "Cars isValid exception"
                logging.error(f'user: {user.username}, mis: {mis_obj.id}')
                logging.error(error_msg)
                logging.error(car_s.errors)
                return JsonResponse(car_s.errors, status=status.HTTP_400_BAD_REQUEST)
            j_response["Cars"].append(car_s.data)
            total_car += 1

        logging.info(f'user: {user.username}, mis: {mis_obj.id}')
        logging.info(f'CarCreateView: loaded {total_car}; {new_car} new, {updated_car} updated')
        return HttpResponse(json.dumps(j_response, ensure_ascii=False),
                            content_type="application/json",
                            status=status.HTTP_201_CREATED)
