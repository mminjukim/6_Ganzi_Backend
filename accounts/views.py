from django.utils import timezone
import requests
from django.shortcuts import redirect
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google import views as google_view
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from rest_framework.views import APIView
from .models import User
from .serializers import UserSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.socialaccount.models import SocialAccount, SocialLogin
from .models import *
from sch_requests.models import *
from family.models import FamilyInfo
from .serializers import UserSerializer, ProfileSerializer, SimpleUserSerializer

BASE_URL = 'http://127.0.0.1:8000/'
GOOGLE_CALLBACK_URI = BASE_URL + 'accounts/google/callback/'

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
def google_login(request):
    scope = "https://www.googleapis.com/auth/userinfo.email"
    client_id = getattr(settings, "GOOGLE_CLIENT_ID")
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&response_type=code&redirect_uri={GOOGLE_CALLBACK_URI}&scope={scope}")

def google_callback(request):
    state = 'random'
    client_id = getattr(settings, "GOOGLE_CLIENT_ID")
    client_secret = getattr(settings, "GOOGLE_SECRET")
    code = request.GET.get('code')
    redirect_uri = "http://localhost:5173/googleLogin"
    # 액세스 토큰 요청
    token_req = requests.post(
        f"https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "state": state
        }
    )
    token_req_json = token_req.json()
    access_token = token_req_json.get('access_token')
    
    # 구글 API에서 이메일 정보 요청
    email_req = requests.get(
        f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}"
    )
    email_req_status = email_req.status_code
    if email_req_status != 200:
        return JsonResponse({'err_msg': 'failed to get email'}, status=status.HTTP_400_BAD_REQUEST)
    email_req_json = email_req.json()
    email = email_req_json.get('email')
    
    # 이메일로 유저 확인
    try:
        user = User.objects.get(email=email)
        social_login = SocialLogin(account=SocialAccount(user=user, provider='google', uid=email))

        merge_social_account(user, social_login)
        
        social_user = SocialAccount.objects.get(user=user)
        
        if social_user is None:
            return JsonResponse({'err_msg': 'email exists but not social user'}, status=status.HTTP_400_BAD_REQUEST)
        if social_user.provider != 'google':
            return JsonResponse({'err_msg': 'no matching social type'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 이미 로그인된 유저인 경우 JWT 토큰 발급
        access_token, refresh_token = create_jwt_token(user)  # JWT 토큰 생성 함수

        user.last_login = timezone.now()  # 여기서 last_login을 갱신
        user.save()  

        response = JsonResponse({
            'message': 'Login successful',
            'access_token':access_token,
            'refresh_token':refresh_token
        })

        response["Authorization"] = f'Bearer {access_token}'
        response["Refresh-Token"] = refresh_token

        return response
    
    except User.DoesNotExist:
        # 신규 유저의 경우
        user = User.objects.create(email=email)
        social_user = SocialAccount.objects.create(user=user, provider='google', extra_data=email_req_json)
        
        # 신규 유저인 경우 JWT 토큰 발급
        access_token, refresh_token = create_jwt_token(user)  # JWT 토큰 생성 함수
        response = JsonResponse({'message': 'User created and logged in'})
        response['Authorization'] = f'Bearer {access_token}'
        response['Refresh-Token'] = refresh_token
        return response

def merge_social_account(user, social_login):
    try:
        existing_account = SocialAccount.objects.get(user=user, provider='google')
        if existing_account:
            # 기존 계정에 병합 처리
            existing_account.uid = social_login.account.uid
            existing_account.save()
    except SocialAccount.DoesNotExist:
        social_login.account.save()

def create_jwt_token(user):
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    return access_token, refresh_token

class GoogleLogin(SocialLoginView):
    adapter_class = google_view.GoogleOAuth2Adapter
    callback_url = GOOGLE_CALLBACK_URI
    client_class = OAuth2Client

class GoogleLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 사용자의 Google Access Token 가져오기
        access_token = request.user.google_access_token

        # Google 토큰 취소 요청
        revoke_url = "https://oauth2.googleapis.com/revoke"
        params = {"token": access_token}
        revoke_request = requests.post(revoke_url, params=params)

        if revoke_request.status_code == 200:
            return Response({"message": "Successfully logged out from Google"}, status=200)
        else:
            return Response({"error": "Failed to revoke access token"}, status=revoke_request.status_code)


# Google 계정 연결 해제 (회원탈퇴)
class GoogleUnlinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 사용자의 Google Access Token 가져오기
        access_token = request.user.google_access_token

        # Google 연결 해제 요청 (Google 계정 연결 끊기)
        unlink_url = "https://accounts.google.com/o/oauth2/revoke"
        params = {"token": access_token}
        unlink_request = requests.post(unlink_url, params=params)

        if unlink_request.status_code == 200:
            try:
                # 서버에서 사용자 정보 삭제
                # SocialAccount에서 해당 사용자 삭제
                social_account = SocialAccount.objects.get(user=request.user, provider='google')
                social_account.delete()

                # 사용자와 관련된 추가 데이터 정리
                if request.user.family:
                    user_family = request.user.family
                    user_family.fam_num -= 1
                    user_family.save(update_fields=['fam_num'])
                    if user_family.fam_num == 0:
                        user_family.delete()

                # 사용자 삭제
                request.user.delete()

                return Response({"message": "Successfully unlinked Google account and deleted user"}, status=200)
            except SocialAccount.DoesNotExist:
                return Response({"error": "Google account not linked to this user"}, status=400)
        else:
            return Response({"error": "Failed to unlink Google account"}, status=unlink_request.status_code)
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