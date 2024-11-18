import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flan.settings")
import django
django.setup()

from datetime import timedelta, datetime, time
from django.utils import timezone
from family.models import FamilyInfo, FamilyEmptyTime
from accounts.models import User
from personal.models import PersonalSchedule
from sch_requests.models import FamilySchedule, Request


'''
place 광고 띄우는 용도의 Family Empty Time 계산
'''
def calc_family_empty_time(family_id):
    DAY_START = time(8, 0) 
    DAY_END = time(22, 0) 
    today = datetime.now()
    family = FamilyInfo.objects.get(family_id=family_id)

    # 내일부터 일주일간의 스케줄이 계산 대상 
    calc_start_date = datetime(today.year, today.month, today.day) + timedelta(days=1)
    calc_end_date = datetime(today.year, today.month, today.day) + timedelta(days=7)
    
    fam_members = User.objects.filter(family=family)

    # 가족 내 개인 구성원들의 개인스케줄 get
    user_schedules = PersonalSchedule.objects.filter(
        user__in=fam_members, 
        schedule_start_time__lte=calc_end_date,
        schedule_end_time__gte=calc_start_date).order_by('schedule_start_time')

    # 가족 내 가족스케줄 get
    requests = Request.objects.filter(target_user__in=fam_members, is_accepted=True)
    fam_schedules = FamilySchedule.objects.filter(
        request__in=requests,
        schedule_start_time__lte=calc_end_date,
        schedule_end_time__gte=calc_start_date).distinct().order_by('schedule_start_time')

    # 모든 스케줄 합쳐 start_time, end_time만 추출하고 정렬 
    all_schedules = []
    all_schedules.extend([
        {'start_time': schedule.schedule_start_time, 'end_time': schedule.schedule_end_time}
        for schedule in user_schedules
    ]) # 개인 스케줄 추출
    all_schedules.extend([
        {'start_time': schedule.schedule_start_time, 'end_time': schedule.schedule_end_time}
        for schedule in fam_schedules
    ]) # 가족 스케줄 추출 
    all_schedules.sort(key=lambda x: x['start_time'])

    # 스케줄이 겹치지 않는 빈 시간을 저장할 리스트
    free_time_slots = []
    last_end_time = calc_start_date

    for schedule in all_schedules:
        # 스케줄의 시작 시간이 이전 종료 시간보다 늦은 경우 빈 시간이 발생
        if schedule['start_time'] > last_end_time:
            free_time_slots.append((last_end_time, schedule['start_time']))
        # 이전 종료 시간을 현재 스케줄의 종료 시간으로 업데이트
        last_end_time = max(last_end_time, schedule['end_time'])

    # calc_end_date 이전의 빈 시간도 추가
    if last_end_time < calc_end_date:
        free_time_slots.append((last_end_time, calc_end_date))

    # 아래부터 매 날짜마다 유효한 분 계산해 리턴
    results = {}
    i_date = calc_start_date.date()
    calc_end_date = calc_end_date.date()

    while i_date < calc_end_date:
        daily_start = datetime.combine(i_date, DAY_START)
        daily_end = datetime.combine(i_date, DAY_END)
        daily_free_minutes = 0

        for start_time, end_time in free_time_slots:
            slot_start = max(start_time, daily_start)
            slot_end = min(end_time, daily_end)
            if slot_start < slot_end:
                free_interval_minutes = int((slot_end - slot_start).total_seconds() // 60)
                daily_free_minutes += free_interval_minutes

        results[i_date.strftime("%Y-%m-%d")] = daily_free_minutes
        i_date += timedelta(days=1)

    print(results)
    return results



'''
가족스케줄 요청시 시간 비는 구성원 띄우는 용도의 Personal Empty Time 계산 
'''
def calc_personal_empty_time(req_start_time, req_end_time, user_id):
    DAY_START = time(8, 0) 
    DAY_END = time(22, 0) 

    req_start_time = datetime.strptime(req_start_time, '%Y-%m-%d %H:%M:%S')
    req_end_time = datetime.strptime(req_end_time, '%Y-%m-%d %H:%M:%S')

    user = User.objects.get(user_id=user_id)
    family = FamilyInfo.objects.get(family_id=user.family.family_id)
    fam_members = User.objects.filter(family=family)

    available_members = []
    for member in fam_members:
        # 이미 해당 시간에 스케줄이 있는 가족구성원은 결과에서 제외 
        user_schedules = PersonalSchedule.objects.filter(user=member, schedule_start_time__lte=req_end_time,
                                                         schedule_end_time__gte=req_start_time).order_by('schedule_start_time')
        if not user_schedules:
            requests = Request.objects.filter(target_user=member, is_accepted=True)
            fam_schedules = FamilySchedule.objects.filter(request__in=requests, schedule_start_time__lte=req_end_time, 
                                                        schedule_end_time__gte=req_start_time).distinct().order_by('schedule_start_time')
            if not fam_schedules:
                available_members.append(member)
    
    print(available_members)
    return available_members