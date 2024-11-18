from rest_framework import serializers
from accounts.models import User


class ProfileSerializer(serializers.ModelSerializer):
    profile_img = serializers.ImageField(use_url=True, required=False, allow_empty_file=True)

    class Meta:
        model = User
        fields = ['user_id', 'nickname', 'profile_img']
