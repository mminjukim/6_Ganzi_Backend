from django.shortcuts import redirect
from django.http import JsonResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
import requests

BASE_URL = 'https://flan.klr.kr/'
KAKAO_CALLBACK_URI = BASE_URL + 'accounts/kakao/callback/'

# JWT 토큰 생성 함수
def create_jwt_token(user):
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    return access_token, refresh_token

# 카카오 로그인 URL 반환
def kakao_login(request):
    rest_api_key = settings.KAKAO_REST_API_KEY
    scopes = "account_email friends talk_message"
    kakao_login_url = (
        f"https://kauth.kakao.com/oauth/authorize?"
        f"client_id={rest_api_key}&redirect_uri={KAKAO_CALLBACK_URI}&response_type=code&scope={scopes}"
    )
    return JsonResponse({"kakaoURL": kakao_login_url})

# 카카오 콜백 처리
def kakao_callback(request):
    rest_api_key = settings.KAKAO_REST_API_KEY
    client_secret = settings.KAKAO_CLIENT_SECRET_KEY
    code = request.GET.get('code')

    # Access Token 요청
    token_req = requests.post(
        "https://kauth.kakao.com/oauth/token",
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

    # 사용자 정보 요청
    profile_req = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    profile_json = profile_req.json()

    kakao_account = profile_json.get('kakao_account', {})
    email = kakao_account.get('email')
    kakao_uid = profile_json.get('id')

    if not email:
        return JsonResponse({'err_msg': 'Email not available'}, status=400)

    # 사용자 생성 및 JWT 발급
    user, created = User.objects.get_or_create(email=email)
    if created:
        user.username = f"kakao_{kakao_uid}"
        user.save()

    access_token, refresh_token = create_jwt_token(user)

    return JsonResponse({
        "access_token": access_token,
        "refresh_token": refresh_token,
    })
