from datetime import datetime
from rest_framework import serializers
from .models import FamilyMemo, PersonalSchedule
from sch_requests.models import FamilySchedule
from accounts.models import User
from ads.models import Place

class FamilyScheduleSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(source='category.category_id')  # ForeignKey 필드 직접 참조
    schedule_date = serializers.SerializerMethodField()

    class Meta:
        model = FamilySchedule
        fields = ['fam_schedule_id', 'category_id', 'schedule_date', 'schedule_title']
    
    def get_schedule_date(self, obj):
        return obj.schedule_start_time.date()

class FamilyMemoSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id')
    profile_img = serializers.SerializerMethodField()
    content = serializers.CharField()

    class Meta:
        model = FamilyMemo
        fields = ['user_id', 'profile_img', 'content']

    def get_profile_img(self, obj):
        return obj.user.profile_img.url if obj.user.profile_img else None

class FamilyMessageSerializer(serializers.Serializer):
    family_id = serializers.IntegerField()
    members = FamilyMemoSerializer(many=True)

class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ['place_img']

class OneWordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMemo
        fields = ['content']
    
class PersonalScheduleSerializer(serializers.ModelSerializer):
    date =serializers.SerializerMethodField()
    schedule_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

    class Meta:
        model = PersonalSchedule
        fields = ['personal_schedule_id', 'date','schedule_date', 'schedule_title', 'start_time', 'end_time', 'is_daily', 'is_weekly', 'is_monthly', 'is_yearly', 'schedule_start_time', 'schedule_end_time']

    def get_date(self, obj):
        return obj.schedule_start_time.date()
    
    def create(self, validated_data):
        schedule_date = validated_data.get('schedule_date')
        start_time = validated_data.get('start_time')
        end_time = validated_data.get('end_time')

        schedule_start_time = datetime.combine(schedule_date, start_time)
        schedule_end_time = datetime.combine(schedule_date, end_time)

        schedule = PersonalSchedule.objects.create(
            schedule_title=validated_data.get('schedule_title'),
            user=self.context['request'].user,
            schedule_start_time=schedule_start_time,
            schedule_end_time=schedule_end_time,
            is_daily=validated_data.get('is_daily', False),
            is_weekly=validated_data.get('is_weekly', False),
            is_monthly=validated_data.get('is_monthly', False),
            is_yearly=validated_data.get('is_yearly', False),
        )
        return schedule