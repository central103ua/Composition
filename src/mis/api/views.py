import json
from django.shortcuts import render
from rest_framework import generics, mixins
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from ekstrenka.mixins import HttpResponseMixin
from mis.models import Mis
from heartbeat.utils import is_json

from .serializers import MisSerializer
from accounts.permissions import IsMisOrSuperuser, IsOwnerOrReadOnly


class MisAPIView(generics.ListAPIView):
    serializer_class = MisSerializer
    #lookup_field = 'id'
    #permission_classes = [AllowAny]
    #permission_classes = [IsAuthenticatedOrReadOnly]
    #permission_classes = [IsAuthenticated]
    permission_classes = [IsMisOrSuperuser]
    #permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = Mis.objects.all().order_by('id')
        query = self.request.GET.get("q")
        if query is not None:
            qs = qs.filter(Q(mis_name__icontains=query) | Q(mis_comment__icontains=query)).distinct()
        return qs

    def get_serializer_context(self, *args, **kwargs):
        return {"request": self.request}

    def get_queryset(self):
        qs = Mis.objects.all().order_by('id')
        print("MisRudView:get_queryset: ", qs)
        return qs

    def get_serializer_context(self, *args, **kwargs):
        return {"request": self.request}
