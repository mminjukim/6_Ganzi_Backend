from rest_framework import serializers
from sch_requests.models import Request
from accounts.models import User


# 스케줄 목록용 
class RequestListSerializer(serializers.ModelSerializer):
    sent_user_img = serializers.ImageField(source='sent_user.profile_img')
    category_name = serializers.CharField(source='fam_schedule.category.category_name')
    schedule_title = serializers.CharField(source='fam_schedule.schedule_title')
    schedule_memo = serializers.CharField(source='fam_schedule.schedule_memo')
    
    class Meta:
        model = Request
        fields = ['id', 'sent_user_img', 'category_name', 'schedule_title', 'schedule_memo']


# 스케줄 상세보기용 
class RequestSerializer(serializers.ModelSerializer):
    sent_user_name = serializers.CharField(source='sent_user.nickname')
    target_user_name = serializers.CharField(source='target_user.nickname')
    category_name = serializers.CharField(source='fam_schedule.category.category_name')
    schedule_title = serializers.CharField(source='fam_schedule.schedule_title')
    schedule_time = serializers.DateTimeField(source='fam_schedule.schedule_start_time',
                                              format='%Y년 %m월 %d일 %H:%M')
    schedule_memo = serializers.CharField(source='fam_schedule.schedule_memo')

    class Meta:
        model = Request
        fields = ['id', 'sent_user_name', 'target_user_name', 'category_name', 
                  'schedule_title', 'schedule_time', 'schedule_memo', 
                  'is_checked', 'is_accepted']


class ProfileImgSerializer(serializers.ModelSerializer):
    profile_img = serializers.ImageField(use_url=True, required=False, allow_empty_file=True)

    class Meta:
        model = User
        fields = ['profile_img']