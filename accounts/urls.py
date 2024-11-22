from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('google/login/', views.google_login, name='google_login'),
    path('google/callback/', views.google_callback, name='google_callback'),
    path('google/login/finish/', views.GoogleLogin.as_view(), name='google_login_todjango'),
    path('google/logout/', views.GoogleLogoutView.as_view()),
    #path('google/unlink/', views.googleUnlinkView.as_view()),
    #path('google/friends/', views.googleFriendsListView.as_view()),
    #path('google/friends/send/', views.googleSendMSGView.as_view()),
    path('myprofile/register/', views.ProfileRegisterAPIView.as_view()),
    path('myprofile/edit/', views.ProfileEditAPIView.as_view()),
    path('myprofile/', views.ProFileAPIView.as_view()),
]