from django.urls import path
from .views import *

app_name = 'personal'

urlpatterns = [
    path('', HomeAPIView.as_view()),
    path('personal/one-word/', OneWordAPIView.as_view),
    path('personal/my-schedule/', ScheduleAPIView.as_view),
    #path('personal/schedule/'),
    #path('/personal/{personal_schedule_id}/edit/'),
    #path('/personal/{personal_schedule_id}/delete'),
]