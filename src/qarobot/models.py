from django.db import models
from django.utils import timezone
from django.conf import settings
from mis.models import Mis


class DailyTest(models.Model):
    id = models.BigAutoField(primary_key=True)
    mis = models.ForeignKey('mis.Mis', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    call_count = models.BooleanField(default=False)         # Викликів на добу
    call_complete = models.BooleanField(default=False)      # Незавершенный вызов. call_station != Архів
    er_no_crew = models.BooleanField(default=False)         # Виїзд бригади без бригади, виїзду
    active_crew = models.BooleanField(default=False)        # Досить активні бригади
    steel_city = models.BooleanField(default=False)         # Для Запоріжжя
    email = models.EmailField(null=False, default='central103@central103.org')

    def __str__(self):
        return self.mis.mis_name
