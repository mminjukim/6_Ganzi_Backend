from django.urls import path
from .views import *

app_name = 'sch_requests'

urlpatterns = [
    path('get-available-user/', AvailableUserView.as_view()),
    path('register/', FamScheduleRegisterView.as_view()),
]