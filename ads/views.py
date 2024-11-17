from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import schedule, datetime

from .models import Place
from .serializers import *
from family.models import FamilyInfo, FamilyEmptyTime
from accounts.models import User

# Create your views here.


class AdPopupView(APIView):
    def get(self, request):
        family = request.user.family
        empty_dates = FamilyEmptyTime.objects.filter(family_empty_date__gte=timezone.now().date(), 
                                                    family=family).order_by('family_empty_date')
        empty_date = empty_dates.first()
        place = Place.objects.filter(place_min_time__lte=empty_date.family_empty_min).order_by('?')[:1]

        empty_date_data = DateSerializer(empty_date, context=self.context).data
        place_data = PlaceSerializer(place, context=self.context).data

        return Response({
            "family_date": empty_date_data,
            "ad_place":place_data,
        }, status=status.HTTP_200_OK)
