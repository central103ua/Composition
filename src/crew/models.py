from django.db import models
from django.conf import settings


class CrewSlug(models.Model):
    id = models.BigAutoField(primary_key=True)
    date_modified = models.DateTimeField(auto_now=True)


class Crew(models.Model):
    id = models.BigAutoField(primary_key=True)
    mis_id = models.ForeignKey('mis.Mis', on_delete=models.CASCADE)
    crew_id = models.SlugField(max_length=32, null=False, unique=True)
    mis_crew_id = models.CharField(max_length=32, null=False, blank=False)
    facility_id = models.ForeignKey('mis.Facility', on_delete=models.CASCADE)
    mis_facility_id = models.CharField(max_length=16, null=True, blank=False)
    car_id = models.ForeignKey('mis.Cars', on_delete=models.CASCADE, null=True)
    mis_car_id = models.CharField(max_length=16, null=True)
    shift_start = models.DateTimeField(null=False)
    shift_end = models.DateTimeField(null=False)
    crew_status = models.ForeignKey('CrewStatus', on_delete=models.CASCADE)
    crew_comment = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=False)
    date_modified = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        #unique_together = ('mis_id', 'mis_crew_id',)
        verbose_name = "Crew"
        verbose_name_plural = "Crews"

    def __str__(self):
        return self.crew_id


class CrewTeam(models.Model):
    id = models.BigAutoField(primary_key=True)
    crew_id = models.ForeignKey('Crew', on_delete=models.CASCADE)
    crew_slug = models.CharField(max_length=32, null=False)
    crew_team_seq = models.IntegerField(null=False, default=1)
    crew_staff = models.ForeignKey('mis.Staff', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)


class CrewDairy(models.Model):
    id = models.BigAutoField(primary_key=True)
    crew_id = models.ForeignKey('Crew', on_delete=models.CASCADE)
    mis_id = models.ForeignKey('mis.Mis', on_delete=models.CASCADE)
    crew_slug = models.CharField(max_length=32, null=False)
    call_card_id = models.CharField(max_length=32, null=True)
    call_station = models.ForeignKey('callcard.CallStations', on_delete=models.CASCADE)
    crew_dairy_seq = models.IntegerField(null=False, default=1)
    crew_status = models.ForeignKey('CrewStatus', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True, null=False)
    timestamp = models.DateTimeField(auto_now_add=True)


class CrewRoute(models.Model):
    id = models.BigAutoField(primary_key=True)
    crew_id = models.ForeignKey('Crew', on_delete=models.CASCADE)
    mis_id = models.ForeignKey('mis.Mis', on_delete=models.CASCADE)
    crew_slug = models.CharField(max_length=32, null=False)
    route_seq = models.IntegerField(null=False, default=1)
    crew_status = models.ForeignKey('CrewStatus', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)


class CrewStatus(models.Model):
    id = models.BigAutoField(primary_key=True)
    crewstatus_name = models.CharField(max_length=64, null=False)

    def __str__(self):
        return self.crewstatus_name
