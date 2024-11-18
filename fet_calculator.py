import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flan.settings")
import django
django.setup()

from datetime import timedelta, datetime
from django.utils import timezone
from family.models import FamilyInfo, FamilyEmptyTime
from accounts.models import User
from personal.models import PersonalSchedule
from sch_requests.models import FamilySchedule, Request


def calc_family_empty_time():
    all_families = FamilyInfo.objects.all()
    today = datetime.now()
    calc_start_date = datetime(today.year, today.month, today.day) + timedelta(days=1)
    calc_end_date = datetime(today.year, today.month, today.day) + timedelta(days=7)

    print(today, calc_start_date, calc_end_date)
    
    for family in all_families:
        fam_members = User.objects.filter(family=family)
        print(family.family_id, fam_members)

        user_schedules = PersonalSchedule.objects.filter(
            user__in=fam_members, 
            schedule_start_time__lte=calc_end_date,
            schedule_end_time__gte=calc_start_date).order_by('schedule_start_time')
        
        print(family.family_id, user_schedules)
        
        # 스케줄이 겹치지 않는 빈 시간을 저장할 리스트
        free_time_slots = []
        last_end_time = calc_start_date

        for schedule in user_schedules:
            # 스케줄의 시작 시간이 이전 종료 시간보다 늦은 경우 빈 시간이 발생
            if schedule.schedule_start_time.replace(tzinfo=None) > last_end_time:
                free_time_slots.append((last_end_time, schedule.schedule_start_time.replace(tzinfo=None)))

            # 이전 종료 시간을 현재 스케줄의 종료 시간으로 업데이트
            last_end_time = max(last_end_time, schedule.schedule_end_time.replace(tzinfo=None))

        # calc_end_date 이전의 빈 시간도 추가
        if last_end_time < calc_end_date:
            free_time_slots.append((last_end_time, calc_end_date))

        requests = Request.objects.filter(target_user__in=fam_members, is_accepted=True)
        fam_schedules = FamilySchedule.objects.filter(
            request__in=requests,
            schedule_start_time__lte=calc_end_date,
            schedule_end_time__gte=calc_start_date).distinct().order_by('schedule_start_time')
        
        print(family.family_id, fam_schedules)

        

calc_family_empty_time()