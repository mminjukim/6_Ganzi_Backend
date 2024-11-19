from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Badge, AcquiredBadge

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def create(self, validated_data):
        user = User.objects.create_user(
            email = validated_data['email'],
            password = validated_data['password']
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def create(self, validated_data):
        user = User.objects.create_user(
            email = validated_data['email'],
            password = validated_data['password']
        )
        return user
    
class SimpleUserSerializer(serializers.ModelSerializer):
    profile_img = serializers.ImageField(use_url=True, required=False)
    class Meta:
        model = User
        fields = ['user_id', 'nickname', 'profile_img']

    
class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['badge_name']

class AcquiredBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer()

    class Meta:
        model = AcquiredBadge
        fields = ['badge']

class FamilySerializer(serializers.ModelSerializer):
    profile_img = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['profile_img', 'nickname']

    def get_profile_img(self, obj):
        request = self.context.get('request')
        if obj.profile_img:
            return request.build_absolute_uri(obj.profile_img.url)
        return None

class ProfileSerializer(serializers.ModelSerializer):
    profile_img = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()
    family = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['nickname', 'email', 'profile_img', 'badges', 'family']

    def get_profile_img(self, obj):
        request = self.context.get('request')
        if obj.profile_img:
            return request.build_absolute_uri(obj.profile_img.url)
        return None

    def get_badges(self, obj):
        acquired_badges = AcquiredBadge.objects.filter(user=obj)
        # AcquiredBadge의 badge_name만 추출하여 평평한 리스트 반환
        return [{"badge_name": badge.badge.badge_name} for badge in acquired_badges]


    def get_family(self, obj):
        family_members = User.objects.filter(family=obj.family).exclude(user_id=obj.user_id)
        return FamilySerializer(family_members, many=True, context=self.context).data