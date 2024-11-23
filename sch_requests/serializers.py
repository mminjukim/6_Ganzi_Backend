from rest_framework import serializers
from accounts.models import User
from .models import FamilySchedule


class ProfileSerializer(serializers.ModelSerializer):
    profile_img = serializers.ImageField(use_url=True, required=False, allow_empty_file=True)

    class Meta:
        model = User
        fields = ['user_id', 'nickname', 'profile_img']


class FindUserRequestSerializer(serializers.ModelSerializer):
    start_time = serializers.CharField()
    end_time = serializers.CharField()
    is_repeated = serializers.IntegerField()

    def get_is_repeated(self, obj):
        return obj.is_repeated if obj.is_repeated else None
    def get_start_time(self, obj):
        return obj.start_time if obj.start_time else None
    def get_end_time(self, obj):
        return obj.end_time if obj.end_time else None
    
    class Meta:
        model = FamilySchedule
        fields = ['start_time', 'end_time', 'is_repeated']


class RegisterScheduleSerializer(serializers.ModelSerializer):
    title = serializers.CharField()
    category_id = serializers.IntegerField()
    start_time = serializers.CharField()
    end_time = serializers.CharField()
    is_daily = serializers.IntegerField()
    is_weekly = serializers.IntegerField()
    is_monthly = serializers.IntegerField()
    is_yearly = serializers.IntegerField()
    memo = serializers.CharField()
    target_users = serializers.ListField(child=serializers.IntegerField())

    def get_title(self, obj):
        return obj.title if obj.title else None
    def get_category_id(self, obj):
        return obj.category_id if obj.category_id else None
    def get_start_time(self, obj):
        return obj.start_time if obj.start_time else None
    def get_end_time(self, obj):
        return obj.end_time if obj.end_time else None
    def get_is_daily(self, obj):
        return obj.is_daily if obj.is_daily else None
    def get_is_weekly(self, obj):
        return obj.is_weekly if obj.is_weekly else None
    def get_is_monthly(self, obj):
        return obj.is_monthly if obj.is_monthly else None
    def get_is_yearly(self, obj):
        return obj.is_yearly if obj.is_yearly else None
    def get_memo(self, obj):
        return obj.memo if obj.memo else None
    def get_target_users(self, obj):
        return obj.target_users if obj.target_users else None

    class Meta:
        model = FamilySchedule
        fields = ['title', 'category_id', 'start_time', 'end_time', 
                  'is_daily', 'is_weekly', 'is_monthly', 'is_yearly', 
                  'memo', 'target_users']