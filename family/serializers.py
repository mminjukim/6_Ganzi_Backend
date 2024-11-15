from rest_framework import serializers
from sch_requests.models import Request


# 스케줄 목록용 
class RequestListSerializer(serializers.ModelSerializer):
    sent_user_img = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='fam_schedule.category.category_name')
    schedule_title = serializers.CharField(source='fam_schedule.schedule_title')
    schedule_memo = serializers.CharField(source='fam_schedule.schedule_memo')

    def get_sent_user_img(self, obj):
        if (obj.sent_user.profile_img is not None):
            return obj.sent_user.profile_img.url
        return None
    
    class Meta:
        model = Request
        fields = ['id', 'sent_user_img', 'category_name', 'schedule_title', 'schedule_memo']


# 스케줄 상세보기용 
class RequestSerializer(serializers.ModelSerializer):
    sent_user_name = serializers.CharField(source='sent_user.nickname')
    target_user_name = serializers.CharField(source='target_user.nickname')
    category_name = serializers.CharField(source='fam_schedule.category.category_name')
    schedule_title = serializers.CharField(source='fam_schedule.schedule_title')
    schedule_time = serializers.DateTimeField(source='fam_schedule.schedule_start_time')
    schedule_memo = serializers.CharField(source='fam_schedule.schedule_memo')

    class Meta:
        model = Request
        fields = ['id', 'sent_user_name', 'target_user_name', 'category_name', 'schedule_title', 'schedule_time', 'schedule_memo']