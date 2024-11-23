from django.utils import timezone
import requests
from django.shortcuts import redirect
from flan import settings
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.socialaccount.models import SocialAccount,SocialLogin
from allauth.socialaccount.providers.kakao import views as kakao_view
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from .models import *
from sch_requests.models import *
from family.models import FamilyInfo
from .serializers import UserSerializer, ProfileSerializer, SimpleUserSerializer

BASE_URL = 'http://127.0.0.1:8000/'
KAKAO_CALLBACK_URI = BASE_URL + 'accounts/kakao/callback/'

# JWT 토큰 생성 함수

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
    scopes = "account_email friends talk_message"
    return redirect(
        f"https://kauth.kakao.com/oauth/authorize?client_id={rest_api_key}&redirect_uri={KAKAO_CALLBACK_URI}&response_type=code&scope={scopes}"
    )

def kakao_callback(request):
    rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')
    client_secret = getattr(settings, 'KAKAO_CLIENT_SECRET_KEY')
    code = request.GET.get('code')
    redirect_uri = "http://localhost:5173/kakaoLogin"

    if not code:
        return JsonResponse({'err_msg': 'Authorization code is missing'}, status=400)

    # Access Token 요청
    token_req = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": rest_api_key,
            "redirect_uri": redirect_uri,  # 수정된 redirect_uri
            "code": code,
            "client_secret": client_secret,
        }
    )
    token_req_json = token_req.json()

    if token_req.status_code != 200:
        print(f"Kakao Token Request Failed: {token_req.status_code}, {token_req_json}")
        return JsonResponse({'err_msg': 'Failed to get access token', 'details': token_req_json}, status=400)

    access_token = token_req_json.get('access_token')
    if not access_token:
        return JsonResponse({'err_msg': 'Access token is missing'}, status=400)

    # 사용자 정보 요청
    profile_request = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
    )
    profile_json = profile_request.json()

    if profile_request.status_code != 200:
        print(f"Profile Request Failed: {profile_request.status_code}, {profile_json}")
        return JsonResponse({'err_msg': 'Failed to fetch user profile', 'details': profile_json}, status=400)

    kakao_account = profile_json.get('kakao_account', {})
    email = kakao_account.get('email')
    kakao_uid = str(profile_json.get('id'))

    if not email:
        return JsonResponse({'err_msg': 'Email not available'}, status=400)

    # 사용자 생성 및 JWT 발급
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = User.objects.create(email=email)
        SocialAccount.objects.create(
            user=user,
            provider='kakao',
            uid=kakao_uid,
            extra_data=profile_json
        )

    access_token, refresh_token = create_jwt_token(user)
    response = JsonResponse({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token
    })
    response["Authorization"] = f'Bearer {access_token}'
    response["Refresh-Token"] = refresh_token
    return response

    
def merge_social_account(user, social_account):
    try:
        # 기존 계정을 검색
        existing_account = SocialAccount.objects.get(user=user, provider='kakao')
        # 기존 계정 정보 업데이트
        existing_account.uid = social_account.uid
        existing_account.extra_data = social_account.extra_data
        existing_account.save()
    except SocialAccount.DoesNotExist:
        # 계정이 없을 경우 새 계정을 생성
        SocialAccount.objects.create(
            user=user,
            provider='kakao',
            uid=social_account.uid,
            extra_data=social_account.extra_data,
        )


def create_jwt_token(user):
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    return access_token, refresh_token

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

# 카카오 로그아웃
class KakaoLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        access_token = request.user.kakao_access_token
        
        logout_request = requests.post(
            "https://kapi.kakao.com/v1/user/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        logout_json = logout_request.json()
        
        if logout_request.status_code == 200:
            return Response({"message": "Successfully logged out from Kakao"}, status=200)
        else:
            return Response({"error": logout_json.get('msg', 'Logout failed')}, status=logout_request.status_code)

# 회원탈퇴
class KakaoUnlinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 인증된 사용자의 카카오 액세스 토큰 가져오기
        access_token = request.user.kakao_access_token
        
        # 카카오 연결 끊기 요청
        unlink_request = requests.post(
            "https://kapi.kakao.com/v1/user/unlink",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        unlink_json = unlink_request.json()
        
        if unlink_request.status_code == 200:
            # 카카오와 연결이 끊어졌다면, 서버에서 사용자 정보 삭제
            try:
                # 해당 사용자의 SocialAccount를 찾아 삭제
                social_account = SocialAccount.objects.get(user=request.user, provider='kakao')
                social_account.delete()
                # 해당 사용자의 가족 수 -= 1
                user_family = request.user.family
                user_family.fam_num -= 1
                user_family.save(update_fields=['fam_num'])
                if user_family.fam_num == 0:
                    user_family.delete()
                # 서버의 사용자 정보도 삭제
                request.user.delete()

                return Response({"message": "Successfully disconnected from Kakao and deleted user from the server"}, status=200)
            except SocialAccount.DoesNotExist:
                return Response({"error": "Kakao account not linked to this user"}, status=400)
        else:
            return Response({"error": unlink_json.get('msg', 'Failed to unlink from Kakao')}, status=unlink_request.status_code)

# 카카오 친구목록
class KakaoFriendsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        access_token = request.user.kakao_access_token

        if not access_token:
            return Response({"error": "Access token is required"}, status=400)
        
        # 카카오 친구 목록 요청
        url = "https://kapi.kakao.com/v1/api/talk/friends"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return Response(data, status=200)
            else:
                return Response(response.json(), status=response.status_code)
        except requests.exceptions.RequestException as e:
            return Response({"error": "Failed to connect to Kakao API", "details": str(e)}, status=500)

#카카오 친구에게 메시지 전송
class KakaoSendMSGView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        access_token = request.user.kakao_access_token
        
        # 클라이언트에서 받은 친구 UUID와 메시지 텍스트
        friend_uuid = request.data.get("friend_uuid")
        
        if not friend_uuid:
            return Response({"error": "Friend UUID is required"}, status=400)

        # 카카오 메시지 전송 요청
        url = "https://kapi.kakao.com/v1/api/talk/friends/message/default/send"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        data = {
            "receiver_uuids": f'["{friend_uuid}"]',
            "template_object": {
                "object_type": "text",
                "text": "flan으로 당신을 초대합니다",
                "link": {
                    "web_url": "https://www.example.com"
                },
                "button_title": "초대 링크 열기"
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return Response({"message": "Message sent successfully"}, status=200)
            else:
                return Response(response.json(), status=response.status_code)
        
        except requests.exceptions.RequestException as e:
            return Response({"error": "Failed to send message", "details": str(e)}, status=500)


# 프로필 등록
class ProfileRegisterAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def patch(self, request):
        user = User.objects.get(user_id=request.user.user_id)

        if user.family is None:
            if request.data.get('invited_user') is None or request.data.get('invited_user') == '':
                # 새로운 FamilyInfo 생성
                new_family = FamilyInfo.objects.create(fam_num=1)
                user.family = new_family
                user.save()
            else:
                invited_user = User.objects.get(email=request.data.get('invited_user'))
                user.family = invited_user.family
                user.save()
                user.family.fam_num += 1
                user.family.save(update_fields=['fam_num'])

        serializer = UserSerializer(user, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# 프로필 수정 
class ProfileEditAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = User.objects.get(user_id=request.user.user_id)
        serializer = SimpleUserSerializer(user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        user = User.objects.get(user_id=request.user.user_id)
        serializer = SimpleUserSerializer(user, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class ProFileAPIView(APIView):
    def get(self, request):
        user = request.user
        serializer = ProfileSerializer(user, context={"request": request})
        return Response(serializer.data)