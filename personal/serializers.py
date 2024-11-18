from datetime import datetime, timedelta
from django.utils import timezone
import calendar
from dateutil.relativedelta import relativedelta
from rest_framework import serializers
from .models import FamilyMemo, PersonalSchedule
from sch_requests.models import FamilySchedule
from ads.models import Place
from django.utils.timezone import make_aware

class FamilyScheduleSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(source='category.category_id')  # ForeignKey 필드 직접 참조
    schedule_date = serializers.SerializerMethodField()

    class Meta:
        model = FamilySchedule
        fields = ['fam_schedule_id', 'category_id', 'schedule_date', 'schedule_title']
    
    def get_schedule_date(self, obj):
        return obj.schedule_start_time.date()

class FamilyMemoSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.user_id')
    profile_img = serializers.SerializerMethodField()
    content = serializers.CharField()

    class Meta:
        model = FamilyMemo
        fields = ['user_id', 'profile_img', 'content']

    def get_profile_img(self, obj):
        request = self.context.get('request')
        if obj.user.profile_img:
            return request.build_absolute_uri(obj.user.profile_img.url)
        return None

class FamilyMessageSerializer(serializers.Serializer):
    family_id = serializers.IntegerField()
    members = FamilyMemoSerializer(many=True)

class AdSerializer(serializers.ModelSerializer):
    place_img = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = ['place_img']
        
    def get_place_img(self, obj):
        request = self.context.get('request')
        if obj.place_img:
            return request.build_absolute_uri(obj.place_img.url)
        return None

class OneWordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMemo
        fields = ['content']
    
class PersonalScheduleSerializer(serializers.ModelSerializer):
    schedule_date = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()

    input_schedule_date = serializers.DateField(write_only=True)
    input_start_time = serializers.TimeField(write_only=True)
    input_end_time = serializers.TimeField(write_only=True)

    class Meta:
        model = PersonalSchedule
        fields = ['personal_schedule_id', 'schedule_date', 'schedule_title', 'start_time', 'end_time', 'input_schedule_date', 'input_start_time', 'input_end_time', 'is_daily', 'is_weekly', 'is_monthly', 'is_yearly']

    def get_schedule_date(self, obj):
        return obj.schedule_start_time.date() if obj.schedule_start_time else None

    def get_start_time(self, obj):
        return obj.schedule_start_time.time() if obj.schedule_start_time else None

    def get_end_time(self, obj):
        return obj.schedule_end_time.time() if obj.schedule_end_time else None

    @staticmethod
    def adjust_to_last_day_of_month(input_date):
        last_day = calendar.monthrange(input_date.year, input_date.month)[1]
        if input_date.day == 31:
            return input_date.replace(day=last_day)
        return input_date

    def create(self, validated_data):
        user = self.context['request'].user
        schedule_date = validated_data.pop('input_schedule_date')
        start_time = validated_data.pop('input_start_time')
        end_time = validated_data.pop('input_end_time')

        schedule_start_time = datetime.combine(schedule_date, start_time)
        schedule_end_time = datetime.combine(schedule_date, end_time)

        schedule_start_time = timezone.make_aware(schedule_start_time, timezone.get_current_timezone())
        schedule_end_time = timezone.make_aware(schedule_end_time, timezone.get_current_timezone())

        schedules = []

        if validated_data.get('is_daily', False):
            for i in range(7):
                start = schedule_start_time + timedelta(days=i)
                end = schedule_end_time + timedelta(days=i)
                # 날짜 조정
                start = self.adjust_to_last_day_of_month(start)
                end = self.adjust_to_last_day_of_month(end)
                schedules.append(PersonalSchedule(
                    user=user,
                    schedule_start_time=start,
                    schedule_end_time=end,
                    **validated_data
                ))

        elif validated_data.get('is_weekly', False):
            for i in range(4):
                start = schedule_start_time + timedelta(weeks=i)
                end = schedule_end_time + timedelta(weeks=i)
                # 날짜 조정
                start = self.adjust_to_last_day_of_month(start)
                end = self.adjust_to_last_day_of_month(end)
                schedules.append(PersonalSchedule(
                    user=user,
                    schedule_start_time=start,
                    schedule_end_time=end,
                    **validated_data
                ))

        elif validated_data.get('is_monthly', False):
            for i in range(12):
                start = schedule_start_time + relativedelta(months=i)
                end = schedule_end_time + relativedelta(months=i)
                # 날짜 조정
                start = self.adjust_to_last_day_of_month(start)
                end = self.adjust_to_last_day_of_month(end)
                schedules.append(PersonalSchedule(
                    user=user,
                    schedule_start_time=start,
                    schedule_end_time=end,
                    **validated_data
                ))

        elif validated_data.get('is_yearly', False):
            for i in range(5):
                start = schedule_start_time + relativedelta(years=i)
                end = schedule_end_time + relativedelta(years=i)
                # 날짜 조정
                start = self.adjust_to_last_day_of_month(start)
                end = self.adjust_to_last_day_of_month(end)
                schedules.append(PersonalSchedule(
                    user=user,
                    schedule_start_time=start,
                    schedule_end_time=end,
                    **validated_data
                ))

        schedule = PersonalSchedule.objects.bulk_create(schedules)
        return schedule


    def update(self, instance, validated_data):
        schedule_date = validated_data.pop('input_schedule_date', None)
        start_time = validated_data.pop('input_start_time', None)
        end_time = validated_data.pop('input_end_time', None)

        if schedule_date and start_time and end_time:
            # 입력 받은 날짜 및 시간을 datetime으로 변환
            schedule_start_time = datetime.combine(schedule_date, start_time)
            schedule_end_time = datetime.combine(schedule_date, end_time)

            # timezone-aware로 변환
            schedule_start_time = make_aware(schedule_start_time, timezone.get_current_timezone())
            schedule_end_time = make_aware(schedule_end_time, timezone.get_current_timezone())

            # datetime 객체를 저장
            instance.schedule_start_time = schedule_start_time
            instance.schedule_end_time = schedule_end_time

        # 다른 필드들 업데이트
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # 변경된 데이터를 저장하고 객체 반환
        instance.save()
        return instance