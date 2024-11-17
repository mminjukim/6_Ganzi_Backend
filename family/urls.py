from django.urls import path
from .views import *

app_name = 'family'

urlpatterns = [
    path('calendar/<int:y>/<int:m>/<int:d>/', FamilyCalendarView.as_view()),
    path('incoming/', AllIncomingRequestsView.as_view()),
    path('incoming/<int:id>/', IncomingRequestView.as_view()),
    path('declined/', AllDeclinedRequestsView.as_view()),
    path('declined/<int:id>/', DeclinedRequestView.as_view()),
    path('outgoing/', AllOutgoingRequestsView.as_view()),
    path('outgoing/<int:id>/', OutgoingRequestView.as_view()),
]