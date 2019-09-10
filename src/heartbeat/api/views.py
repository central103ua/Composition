import logging
import json
import time
from django.http import HttpResponse, JsonResponse, HttpRequest
from rest_framework import generics
from rest_framework import status

from mis.models import Mis
from mis.api.serializers import MisSerializer
from accounts.permissions import IsMisUser, IsOwnerOrReadOnly
from heartbeat.models import HeartBeat, Intercall, IntercallSatus
from .serializers import HeartbeatSerializer, IntercallSerializer


class HeartbeatView(generics.CreateAPIView):
    serializer_class = HeartbeatSerializer
    permission_classes = [IsMisUser]

    def post(self, request, *args, **kwargs):
        error_msg = {}
        user = self.request.user
        mis_obj = Mis.objects.get(mis_user=user)

        mis_ip = request.META.get("HTTP_X_FORWARDED_FOR", None)
        if mis_ip == None:
            mis_ip = request.META.get('REMOTE_ADDR', "0.0.0.0")
        logging.info(f'Heartbeat POST; user: {user.username}, mis: {mis_obj.id}, IP: {mis_ip}')
        if not 'application/json' in request.META.get("CONTENT_TYPE"):
            error_msg["Heartbeat"] = 'Conntent-Type: application/json required'
            logging.error(f'Heartbeat POST; user: {user.username}, mis: {mis_obj.id}')
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        try:
            j_request = json.loads(request.body)
            logging.info(json.dumps(j_request, ensure_ascii=False))
        except:
            logging.error(request.body)
            logging.error(f'Heartbeat POST; user: {user.username}, mis: {mis_obj.id}')
            error_msg["Heartbeat"] = 'Bad JSON in Request'
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

        j_resp_data = json.loads('{"Heartbeat":[],"Intercall":[]}')
        hb_serializer = None
        ic_serializer = None
        if 'Heartbeat' in j_request:
            j_request['Heartbeat'][0]['mis_id'] = mis_obj.id
            hb_serializer = HeartbeatSerializer(data=j_request['Heartbeat'][0])
            if hb_serializer.is_valid():
                hb_serializer.save()
                j_resp_data['Heartbeat'].append(hb_serializer.data)
            else:
                logging.error(f'HeartbeatSerializer is not VALID. user: {user.username}, mis: {mis_obj.id}')
                return JsonResponse(hb_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            hb_data = hb_serializer.data
            mis_serializer = MisSerializer(mis_obj, data=hb_data)
            if mis_serializer.is_valid():
                mis_serializer.save()
        else:
            error_msg["Heartbeat Error"] = "No Heartbeat in request"
            logging.error(f'Heartbeat POST; user: {user.username}, mis: {mis_obj.id}')
            logging.error(error_msg)
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

        # # Proceed Intercall:
        ic_qs = Intercall.objects.filter(mis_to=mis_obj, status__name='Ready')
        for ic_obj in ic_qs:
            ic_s = IntercallSerializer(ic_obj)
            j_resp_data['Intercall'].append(ic_s.data)
            ic_obj.status = IntercallSatus.objects.get(name="Sent")
            ic_obj.save()

        if len(j_resp_data['Intercall']) == 0:
            del j_resp_data['Intercall']
        logging.info(f'Heartbeat Response: {status.HTTP_201_CREATED}; user: {user.username}, mis: {mis_obj.id}')
        logging.info(json.dumps(j_resp_data, ensure_ascii=False))
        return HttpResponse(json.dumps(j_resp_data, ensure_ascii=False),
                            content_type="application/json",
                            status=status.HTTP_201_CREATED)
