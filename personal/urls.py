from django.urls import path
from .views import *

app_name = 'personal'

urlpatterns = [
    path('', HomeAPIView.as_view()),
    #path('personal/one-word/'),
    #path('personal/my-schedule/'),
    #path('personal/register/'),
    #path('personal/schedule/'),
    #path('/personal/{personal_schedule_id}/edit/'),
    #path('/personal/{personal_schedule_id}/delete'),
]