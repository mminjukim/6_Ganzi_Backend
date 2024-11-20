from django.db import models
from accounts.models import *
from django.conf import settings

# Create your models here.
class Category(models.Model):
    category_id = models.BigAutoField(primary_key=True)
    category_name = models.CharField(max_length=15)

class DetailWork(models.Model):
    work_id = models.BigAutoField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="detail_works")
    work_name = models.CharField(max_length=15)

class FamilySchedule(models.Model):
    fam_schedule_id = models.BigAutoField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="family_schedules")
    schedule_start_time = models.DateTimeField()
    schedule_end_time = models.DateTimeField()
    schedule_title = models.CharField(max_length=30)
    schedule_memo = models.CharField(max_length=50, blank=True, null=True)
    is_daily = models.BooleanField(default=False)
    is_weekly = models.BooleanField(default=False)
    is_monthly = models.BooleanField(default=False)
    is_yearly = models.BooleanField(default=False)

class Request(models.Model):
    sent_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='snt_requests')
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trg_requests')
    fam_schedule = models.ForeignKey(FamilySchedule, on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False, verbose_name="요청 수락 여부")
    is_checked = models.BooleanField(default=False, verbose_name="요청 확인 여부")