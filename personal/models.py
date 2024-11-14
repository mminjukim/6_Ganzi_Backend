from django.db import models
from django.conf import settings

class UserEmptyTime(models.Model):
    user_empty_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='user_empty_times')
    user_empty_day = models.DateField(verbose_name="빈 날짜")
    user_empty_start_time = models.TimeField(verbose_name="빈 시간 시작")
    user_empty_end_time = models.TimeField(verbose_name="빈 시간 종료")


class FamilyMemo(models.Model):
    memo_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='family_memos')
    content = models.CharField(max_length=50, blank=True, null=True, verbose_name="가족 한마니 내용")  
    created_at = models.DateField(auto_now_add=True, blank=True, null=True, verbose_name="작성일시")
    
class PersonalSchedule(models.Model):
    personal_schedule_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='personal_schedules')
    schedule_title = models.CharField(max_length=200, blank=True, null=True, verbose_name="개인 스케줄 내용")
    schedule_start_time = models.TimeField(verbose_name="개인 스케줄 시작 시간")
    schedule_end_time = models.TimeField(verbose_name="개인 스케줄 종료 시간")
    is_daily = models.BooleanField(default=False, verbose_name = "데일리")
    is_weekly = models.BooleanField(default=False, verbose_name = "위클리")
    is_monthly = models.BooleanField(default=False, verbose_name = "먼슬리")
    is_yearly = models.BooleanField(default=False, verbose_name = "이얼리")