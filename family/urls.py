from django.urls import path
from .views import *

app_name = 'family'

urlpatterns = [
    path('incoming/', AllIncomingRequestsView.as_view()),
    path('incoming/<int:id>/', IncomingRequestView.as_view()),
]