from datetime import datetime
from django.utils import timezone
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from sch_requests.models import Request, FamilySchedule
from .models import FamilyMemo, PersonalSchedule
from accounts.models import User
from ads.models import Place
from django.db import models
from .serializers import FamilyScheduleSerializer, FamilyMessageSerializer, AdSerializer, OneWordSerializer, PersonalScheduleSerializer

class HomeAPIView(APIView):
    def get(self, request):
        user = request.user  # request.user는 User 객체
        accepted_requests = Request.objects.filter(
            (models.Q(sent_user=user) | models.Q(target_user=user)) & models.Q(is_accepted=True)
        )
        schedules = FamilySchedule.objects.filter(fam_schedule_id__in=accepted_requests.values('fam_schedule_id'))
        schedule_data = FamilyScheduleSerializer(schedules, many=True).data
        
        current_date = timezone.now().date()  # 현재 날짜를 가져옵니다.
        print(f"Current date: {current_date}")
        
        # user.family는 FamilyInfo 객체
        family_id = user.family_id
        family_members = User.objects.filter(family=family_id)
        family_memos = FamilyMemo.objects.filter(user__in=family_members, created_at__date=timezone.now().date())
        
        fam_message_data = FamilyMessageSerializer(
            {
                "family_id": family_id,
                "members": family_memos
            },
            context={'request': request}
        ).data
        
        ads = Place.objects.order_by("?")[:3]
        ad_data = AdSerializer(ads, many=True).data

        return Response({
            "schedule": schedule_data,
            "fam_message": fam_message_data,
            "ad": ad_data
        })


class OneWordAPIView(APIView):
    def post(self, request):
        serializer = OneWordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"message": "Memo data saved successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ScheduleAPIView(APIView):
    def get(self, request):
        user = request.user
        date = request.GET.get('date')
        
        if date:
            try:
                schedule_date = datetime.strptime(date, '%Y-%m-%d').date()
                schedules = PersonalSchedule.objects.filter(user=user, schedule_start_time__date=schedule_date).order_by('schedule_start_time')
            except ValueError:
                return Response({"message": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # 날짜가 없으면 모든 스케줄 반환
            schedules = PersonalSchedule.objects.filter(user=user).order_by('schedule_start_time')

        if not schedules.exists():
            return Response({"message": "No schedules found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = PersonalScheduleSerializer(schedules, many=True)
        return Response({"schedule": serializer.data}, status=status.HTTP_200_OK)
    
    def post(self, request):
        user = request.user
        serializer = PersonalScheduleSerializer(data=request.data, context = {'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Schedule added successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ScheduleManageAPIView(APIView):
    def get(self, request, personal_schedule_id=None):
        user = request.user.user_id
        print(user)
        print(f"Personal Schedule ID: {personal_schedule_id}")
        if personal_schedule_id:
            # 특정 스케줄 조회
            try:
                schedule = PersonalSchedule.objects.get(
                    user=user, personal_schedule_id=personal_schedule_id)
                serializer = PersonalScheduleSerializer(schedule)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except PersonalSchedule.DoesNotExist:
                return Response({"message": "Schedule not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            # 모든 스케줄 조회
            schedules = PersonalSchedule.objects.filter(user=user).order_by('schedule_start_time')
            serializer = PersonalScheduleSerializer(schedules, many=True)
            return Response({"schedule": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request, personal_schedule_id):
        user = request.user.user_id
        try:
            schedule = PersonalSchedule.objects.get(user=user, personal_schedule_id=personal_schedule_id)
        except PersonalSchedule.DoesNotExist:
            return Response({"message": "Schedule not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # PUT 요청에 대한 데이터 유효성 검사
        serializer = PersonalScheduleSerializer(schedule, data=request.data)
        if serializer.is_valid():
            serializer.save()  # 데이터 저장
            return Response({"schedule": serializer.data}, status=status.HTTP_200_OK)
        return Response({"message": "Invalid data", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, personal_schedule_id):
        user = request.user.user_id
        try:
            schedule = PersonalSchedule.objects.get(
                user=user, personal_schedule_id=personal_schedule_id)
        except PersonalSchedule.DoesNotExist:
            return Response({"message": "Schedule not found."}, status=status.HTTP_404_NOT_FOUND)

        schedule.delete()
        return Response({"message": "Schedule deleted successfully."}, status=status.HTTP_204_NO_CONTENT)