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
from .models import *
from sch_requests.models import *
from family.models import FamilyInfo
from .serializers import UserSerializer, ProfileSerializer, SimpleUserSerializer

BASE_URL = 'http://3.34.78.66/'
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
    scopes = "account_email friends talk_message"
    return redirect(
        f"https://kauth.kakao.com/oauth/authorize?client_id={rest_api_key}&redirect_uri={KAKAO_CALLBACK_URI}&response_type=code&scope={scopes}"
    )

# 카카오 로그인 콜백
def kakao_callback(request):
    rest_api_key = getattr(settings, 'KAKAO_REST_API_KEY')
    client_secret = getattr(settings, 'KAKAO_CLIENT_SECRET_KEY')
    code = request.GET.get('code')
    redirect_uri = "http://localhost:5173/kakaologinredirection/"

    # 액세스 토큰 요청
    token_req = requests.post(
        f"https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": rest_api_key,
            "redirect_uri": redirect_uri, 
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
        # 이미 소셜 계정이 있을 경우
        social_user = SocialAccount.objects.get(provider='kakao', uid=kakao_uid)
        user = social_user.user

        # kakao_access_token 필드 업데이트
        if hasattr(user, 'kakao_access_token'):
            user.kakao_access_token = access_token
            user.save()

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

        # kakao_access_token 필드에 저장
        user.kakao_access_token = access_token
        user.save()

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