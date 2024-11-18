from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

from .models import FamilySchedule, Request
from .serializers import ProfileSerializer
from family.serializers import RequestSerializer
from accounts.models import User
from fet_calculator import calc_personal_empty_time

# Create your views here.


class AvailableUserView(APIView):
    def post(self, request):
        data = request.data
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        is_repeated = int(data.get('is_repeated'))

        users = calc_personal_empty_time(start_time, end_time, is_repeated, request.user.user_id)
        if not users:
            return Response({'message': '가능한 사용자가 존재하지 않습니다'}, status=status.HTTP_200_OK)
        
        available_users = ProfileSerializer(users, many=True, context={'request': request}).data
        return Response(available_users, status=status.HTTP_200_OK)


class FamScheduleRegisterView(APIView):
    def post(self, request):
        data = request.data
        title = data.get('title')
        category_id = int(data.get('category_id'))
        start_time = datetime.strptime(data.get('start_time'), '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(data.get('end_time'), '%Y-%m-%d %H:%M:%S')
        is_daily = bool(int(data.get('is_daily')))
        is_weekly = bool(int(data.get('is_weekly')))
        is_monthly = bool(int(data.get('is_monthly')))
        is_yearly = bool(int(data.get('is_yearly')))
        memo = data.get('memo')
        sent_user = request.user
        target_users = data.get('target_users')

        repeat_cnt = 1
        add_time = timedelta(0)
        if is_daily == True:
            repeat_cnt = 7
            add_time = timedelta(days=1)
        elif is_weekly == True:
            repeat_cnt = 4
            add_time = timedelta(days=7)
        elif is_monthly == True:
            repeat_cnt = 12
            add_time = relativedelta(months=1)
        elif is_yearly == True:
            repeat_cnt = 5
            add_time = relativedelta(years=1)
        
        schedules = []
        # 가족스케줄 생성 
        for i in range(repeat_cnt):
            schedule = FamilySchedule.objects.create(
                schedule_title = title,
                category_id = category_id,
                schedule_start_time = start_time, 
                schedule_end_time = end_time,
                is_daily = is_daily,
                is_weekly = is_weekly,
                is_monthly = is_monthly,
                is_yearly = is_yearly,
                schedule_memo = memo
            )
            if repeat_cnt > 0:
                start_time += add_time
                end_time += add_time
            schedules.append(schedule)
    
        requests = []
        # 요청 생성
        for target_user_id in target_users:
            target_user_id = int(target_user_id)
            target_user = User.objects.get(user_id=target_user_id)
            for sched in schedules:
                if (sent_user == target_user): # 본인이 보낸 요청은 자동수락
                        req = Request.objects.create(
                        sent_user=sent_user,
                        target_user=target_user,
                        fam_schedule=sched,
                        is_accepted=True,
                        is_checked=True
                    )
                else:
                    req = Request.objects.create(
                        sent_user=sent_user,
                        target_user=target_user,
                        fam_schedule=sched,
                        is_accepted=False,
                        is_checked=False
                    )
                requests.append(req)

        return Response({'message': '스케줄과 요청이 성공적으로 생성되었습니다.'}, status=status.HTTP_201_CREATED)