import json
import time
import logging
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from rest_framework import generics, mixins
from rest_framework import status
from mis.models import Mis
from crew.models import Crew
from accounts.permissions import IsMisUser
from medrecord.models import MedRecord, MRDiagnosis, MRHospital
from .serializers import MedRecordSerializer, DiagnosisSerializer, HospitalSerializer


class MedRecordRudView(generics.RetrieveUpdateDestroyAPIView):
    #serializer_class = MedRecordSerializer
    permission_classes = [IsMisUser]

    def put(self, request, *args, **kwargs):
        slug = self.kwargs.get("slug")
        user = self.request.user
        error_msg = {}
        mis_obj = Mis.objects.get(mis_user=user)
        mis_id = mis_obj.id
        logging.info(f'MedRecord PUT: user: {user.username}, mis: {mis_id}, medrecord_id: {slug}')
        logging.info(f'MedRecord PUT: Content-Type: {request.META.get("CONTENT_TYPE")}')
        j_response = json.loads('{"MedRecord":[]}')
        try:
            j_request = json.loads(request.body)
            logging.info(json.dumps(j_request, indent=1, ensure_ascii=False))
        except:
            logging.error(request.body)
            error_msg["MedRecord PUT"] = 'Bad JSON in Request'
            logging.error(f'{error_msg}; mis: {mis_id}')
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        if not 'MedRecord' in j_request:
            error_msg["MedRecord PUT"] = "No MedRecord in request"
            logging.error(f'{error_msg}; mis: {mis_id}')
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

        mr_qs = MedRecord.objects.filter(med_record_id=slug)
        if mr_qs.exists():
            mr_obj = mr_qs.first()
        else:
            error_msg["MedRecord PUT"] = "Bad MedRecord ID (slug)"
            logging.error(f'{error_msg}; mis: {mis_id}')
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

        medrecord_data = j_request['MedRecord']
        medrecord_data['mis_id'] = mr_obj.mis_id.id
        medrecord_data['med_record_id'] = slug
        mr_s = MedRecordSerializer(mr_obj, data=medrecord_data)
        if mr_s.is_valid():
            mr_obj = mr_s.save()
        else:
            logging.error(f'CallCard PUT. IsValid exception. user: {user.username}, mis: {mis_id}')
            logging.error(mr_s.errors)
            return JsonResponse(mr_s.errors, status=status.HTTP_400_BAD_REQUEST)

        mr_resp = mr_s.data.copy()
        diag_qs = MRDiagnosis.objects.filter(medrecord=mr_obj.id)
        if diag_qs.exists():
            diag_qs.delete()
        diagnosis = medrecord_data.get('diagnosis', None)
        if diagnosis:
            diagnosis_s = DiagnosisSerializer(data=diagnosis,
                                              mr_id=mr_obj.id,
                                              mr_slug=mr_obj.med_record_id,
                                              cc_id=mr_obj.callcard.id,
                                              many=True)
            if diagnosis_s.is_valid():
                logging.info("MedRecord POST: Diagnosis Validated")
                diagnosis_s.save()
                mr_obj.is_diagnosis_record = True
                mr_obj.save()
                mr_resp['is_diagnosis_record'] = True
                mr_resp['diagnosis'] = diagnosis_s.data
            else:
                logging.error("MedRecord POST: Diagnosis IsValid exception")
                logging.error(json.dumps(diagnosis_s.errors))
                mr_obj.delete()
                return JsonResponse(diagnosis_s.errors, safe=False, status=status.HTTP_400_BAD_REQUEST)
        else:
            mr_obj.is_diagnosis_record = False
        #     if mr_obj.noresult.id == 1:
        #         error_msg["MedRecord POST"] = 'No diagnosis in request'
        #         logging.error(json.dumps(error_msg))
        #         return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

        hosp_qs = MRHospital.objects.filter(medrecord=mr_obj.id)
        if hosp_qs.exists():
            hosp_qs.delete()
        hospital = medrecord_data.get('hospital', None)
        if hospital:
            hospital_s = HospitalSerializer(data=hospital,
                                            mr_id=mr_obj.id,
                                            mr_slug=mr_obj.med_record_id,
                                            cc_id=mr_obj.callcard.id,
                                            many=True)
            if hospital_s.is_valid():
                logging.info("MedRecord POST: Hospital Validated")
                hospital_s.save()
                mr_obj.is_hospital_record = True
                mr_obj.save()
                mr_resp['is_hospital_record'] = True
                mr_resp['hospital'] = hospital_s.data
            else:
                logging.error("MedRecord POST: Hospital IsValid exception")
                logging.error(json.dumps(hospital_s.errors))
                mr_obj.delete()
                return JsonResponse(hospital_s.errors, safe=False, status=status.HTTP_400_BAD_REQUEST)
        else:
            mr_obj.is_hospital_record = False

        j_response["MedRecord"] = mr_resp

        mis_obj.save()
        logging.info(json.dumps(j_response, indent=1, ensure_ascii=False))
        return HttpResponse(json.dumps(j_response, ensure_ascii=False),
                            content_type="application/json",
                            status=status.HTTP_200_OK)


class MedRecordView(generics.CreateAPIView):
    #serializer_class = MedRecordSerializer
    permission_classes = [IsMisUser]

    def post(self, request, *args, **kwargs):
        error_msg = {}
        user = self.request.user
        mis_obj = Mis.objects.get(mis_user=user)
        mis_id = mis_obj.id
        logging.info(f'MedRecord POST: user: {user.username}, mis: {mis_id}')
        logging.info(f'MedRecord POST: Content-Type: {request.META.get("CONTENT_TYPE")}')
        try:
            j_request = json.loads(request.body)
            logging.info(json.dumps(j_request, indent=1, ensure_ascii=False))
        except:
            logging.error(request.body)
            error_msg["MedRecord POST"] = 'Bad JSON in Request'
            logging.error(json.dumps(error_msg))
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        if not 'MedRecord' in j_request:
            error_msg["MedRecord POST"] = 'No MedRecord in reques'
            logging.error(json.dumps(error_msg))
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

        j_response = {}
        medrecord_data = j_request['MedRecord']
        if 'id' in medrecord_data:
            error_msg["MedRecord POST"] = 'Use PUT method to update MedRecord'
            logging.error(json.dumps(error_msg))
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)
        if 'medrecord_id' in medrecord_data:
            error_msg["MedRecord POST"] = 'Use PUT method to update MedRecord'
            logging.error(json.dumps(error_msg))
            return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

        medrecord_data['mis_id'] = mis_id
        medrecord_data['medrecord_id'] = 5  # It will be updated by create() call

        mr_s = MedRecordSerializer(data=medrecord_data)
        if mr_s.is_valid():
            logging.info("MedRecord POST. Validated!!!")
            mr_obj = mr_s.save()
        else:
            logging.error(f'MedRecord POST. IsValid exception. user: {user.username}, mis: {mis_obj.id}')
            logging.error(mr_s.errors)
            return JsonResponse(mr_s.errors, status=status.HTTP_400_BAD_REQUEST)

        mr_resp = mr_s.data.copy()
        diagnosis = medrecord_data.get('diagnosis', None)
        if diagnosis:
            diagnosis_s = DiagnosisSerializer(data=diagnosis,
                                              mr_id=mr_obj.id,
                                              mr_slug=mr_obj.med_record_id,
                                              cc_id=mr_obj.callcard.id,
                                              many=True)
            if diagnosis_s.is_valid():
                logging.info("MedRecord POST: Diagnosis Validated")
                diagnosis_s.save()
                mr_obj.is_diagnosis_record = True
                mr_obj.save()
                mr_resp['is_diagnosis_record'] = True
                mr_resp['diagnosis'] = diagnosis_s.data
            else:
                logging.error("MedRecord POST: Diagnosis IsValid exception")
                logging.error(json.dumps(diagnosis_s.errors))
                mr_obj.delete()
                return JsonResponse(diagnosis_s.errors, safe=False, status=status.HTTP_400_BAD_REQUEST)
        else:
            mr_obj.is_diagnosis_record = False
            # if mr_obj.noresult.id == 1:
            #     error_msg["MedRecord POST"] = 'No diagnosis in request'
            #     logging.error(json.dumps(error_msg))
            #     return JsonResponse(error_msg, status=status.HTTP_400_BAD_REQUEST)

        hospital = medrecord_data.get('hospital', None)
        if hospital:
            hospital_s = HospitalSerializer(data=hospital,
                                            mr_id=mr_obj.id,
                                            mr_slug=mr_obj.med_record_id,
                                            cc_id=mr_obj.callcard.id,
                                            many=True)
            if hospital_s.is_valid():
                logging.info("MedRecord POST: Hospital Validated")
                hospital_s.save()
                mr_obj.is_hospital_record = True
                mr_obj.save()
                mr_resp['is_hospital_record'] = True
                mr_resp['hospital'] = hospital_s.data
            else:
                logging.error("MedRecord POST: Hospital IsValid exception")
                logging.error(json.dumps(hospital_s.errors))
                mr_obj.delete()
                return JsonResponse(hospital_s.errors, safe=False, status=status.HTTP_400_BAD_REQUEST)
        else:
            mr_obj.is_hospital_record = False

        j_response["MedRecord"] = mr_resp

        logging.info(json.dumps(j_response, indent=1, ensure_ascii=False))
        return HttpResponse(json.dumps(j_response, ensure_ascii=False),
                            content_type="application/json",
                            status=status.HTTP_201_CREATED)
