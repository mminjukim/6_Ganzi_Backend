import requests
from django.shortcuts import redirect
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.kakao import views as kakao_view
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from .models import User
from .serializers import UserSerializer

BASE_URL = 'http://127.0.0.1:8000/'
KAKAO_CALLBACK_URI = BASE_URL + 'accounts/kakao/callback/'

# JWT 토큰 생성 함수
def create_jwt_token(user):
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    return access_token, refresh_token

class MypageUserDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = User.objects.get(id=request.user.id)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def patch(self, request):
        user = User.objects.get(id=request.user.id)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InfoUserDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = User.objects.get(id=request.user.id)
        serializer = UserSerializer(user)
        return Response(serializer.data)

# 카카오 로그인 URL로 리다이렉션
def kakao_login(request):
    rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')
    scopes = "account_email"
    return redirect(
        f"https://kauth.kakao.com/oauth/authorize?client_id={rest_api_key}&redirect_uri={KAKAO_CALLBACK_URI}&response_type=code&scope={scopes}"
    )

# 카카오 로그인 콜백
def kakao_callback(request):
    rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')
    client_secret = getattr(settings, 'KAKAO_CLIENT_SECRET_KEY')
    code = request.GET.get('code')

    # 액세스 토큰 요청
    token_req = requests.post(
        f"https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": rest_api_key,
            "redirect_uri": KAKAO_CALLBACK_URI,
            "code": code,
            "client_secret": client_secret,
        }
    )
    token_req_json = token_req.json()
    access_token = token_req_json.get('access_token')
    print(access_token)

    if not access_token:
        return JsonResponse({'err_msg': 'Failed to get access token'}, status=status.HTTP_400_BAD_REQUEST)

    # 사용자 정보 요청
    profile_request = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"},
        params ={
            "property_keys" : '["kakao_account.email"]'
        }
    )
    profile_json = profile_request.json()
    print(profile_json)

    # 이메일 확인
    kakao_account = profile_json.get('kakao_account', {})
    email = kakao_account.get('email', None)
    #if kakao_account.get('is_email_needs_agreement', False):
    #    return JsonResponse({'err_msg': 'Email permission not granted'}, status=status.HTTP_400_BAD_REQUEST)

    #if not email:
    #    email = f"{profile_json.get('id')}@kakao.com"

    kakao_uid = str(profile_json.get('id'))
    try:
        social_user = SocialAccount.objects.get(provider='kakao', uid=kakao_uid)
        user = social_user.user

        # JWT 토큰 발급
        access_token, refresh_token = create_jwt_token(user)
        response = JsonResponse({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
        })
        return response

    except SocialAccount.DoesNotExist:
        # SocialAccount 새로 생성
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # User 새로 생성
            user = User.objects.create(email=email)

        # SocialAccount 생성
        SocialAccount.objects.create(user=user, provider='kakao', uid=kakao_uid, extra_data=profile_json)

        # JWT 토큰 발급
        access_token, refresh_token = create_jwt_token(user)
        response = JsonResponse({
            'message': 'User created and logged in',
            'access_token': access_token,
            'refresh_token': refresh_token,
        })
        return response

class TokenRefreshAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({'message': 'No refresh token'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
        except Exception as e:
            return Response({'message': f'Invalid token: {str(e)}'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'access_token': access_token}, status=status.HTTP_200_OK)

class KakaoLogin(SocialLoginView):
    adapter_class = kakao_view.KakaoOAuth2Adapter
    client_class = OAuth2Client
    callback_url = KAKAO_CALLBACK_URI