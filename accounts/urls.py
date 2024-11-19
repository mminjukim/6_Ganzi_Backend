from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('kakao/login/', views.kakao_login, name='kakao_login'),
    path('kakao/callback/', views.kakao_callback, name='kakao_callback'),
    path('kakao/login/finish/', views.KakaoLogin.as_view(), name='kakao_login_todjango'),
    path('kakao/logout/', views.KakaoLogoutView.as_view()),
    path('kakao/unlink/', views.KakaoUnlinkView.as_view()),
    path('myprofile/edit/', views.ProfileEditAPIView.as_view()),
    path('myprofile/', views.ProFileAPIView.as_view()),
]