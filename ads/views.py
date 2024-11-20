from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import datetime

from .models import Place
from .serializers import *
from family.models import FamilyInfo, FamilyEmptyTime
from accounts.models import User
from fet_calculator import calc_family_empty_time

# Create your views here.


class AdPopupView(APIView):
    def get(self, request):
        family = request.user.family
        
        empty_dates_dict = calc_family_empty_time(family.family_id)
        if not empty_dates_dict:
            return Response({
            'message': '이번 주는 가족들이 전부 가능한 시간이 없습니다'
        }, status=status.HTTP_200_OK)

        date = next(iter(empty_dates_dict))
        available_min = empty_dates_dict[date]
        place = Place.objects.filter(place_min_time__lte=available_min).order_by('?')[:3]
        place_data = PlaceSerializer(place, many=True, context={'request': request}).data

        datetime_date = datetime.strptime(date, '%Y-%m-%d')
        weekdays = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
        day_num = datetime_date.weekday()

        return Response({
            'available_date': date,
            'day_of_week': weekdays[day_num],
            'ad_place': place_data,
        }, status=status.HTTP_200_OK)
