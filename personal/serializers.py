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
    date = serializers.SerializerMethodField()

    class Meta:
        model = PersonalSchedule
        fields = ['personal_schedule_id', 'date', 'schedule_title', 'schedule_start_time', 'schedule_end_time']

    def get_date(self, obj):
        return obj.schedule_start_time.date()