from datetime import timezone
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from sch_requests.models import Request, FamilySchedule
from .models import FamilyMemo
from accounts.models import User
from ads.models import Place
from django.db import models
from .serializers import FamilyScheduleSerializer, FamilyMessageSerializer, AdSerializer, OneWordSerializer

# 메인페이지 기능 구현
class HomeAPIView(APIView):
     def get(self, request):
        user = request.user
        accepted_requests = Request.objects.filter(
            (models.Q(sent_user=user) | models.Q(target_user=user)) & models.Q(is_accepted=True)
        )
        schedules = FamilySchedule.objects.filter(fam_schedule_id__in=accepted_requests.values('fam_schedule_id'))
        schedule_data = FamilyScheduleSerializer(schedules, many=True).data
        
        family_id = user.family
        family_members = User.objects.filter(family = family_id)
        family_memos = FamilyMemo.objects.filter(user__in=family_members, created_at__date=timezone.now().date())
        
        fam_message_data = FamilyMessageSerializer({
            "family_id": family_id,
            "members": family_memos
        }).data
        
        ads = Place.objects.order_by("?")[:3]
        ad_data = AdSerializer(ads, many=True).data

        return Response({
            "schedule": schedule_data,
            "fam_message":fam_message_data,
            "ad":ad_data
        })

class OneWordApiView(APIView):
    def post(self, request):
        serializer = OneWordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Memo data saved successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)