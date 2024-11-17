from rest_framework import serializers
from family.models import FamilyEmptyTime
from .models import Place


class DateSerializer(serializers.ModelSerializer):
    family_empty_date = serializers.DateField(format='%m월 %d일')
    day_of_week = serializers.SerializerMethodField()
    
    def get_day_of_week(self, obj):
        weekdays = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
        day_num = obj.weekday()
        return weekdays[day_num]

    class Meta:
        model = FamilyEmptyTime
        fields = ['family_empty_date', 'day_of_week']


class PlaceSerializer(serializers.ModelSerializer):
    place_img = serializers.ImageField(use_url=True)

    class Meta:
        model = Place
        fields = ['place_name', 'place_link', 'place_img']