from django.urls import path
from .views import *

app_name = 'ads'

urlpatterns = [
    path('', AdPopupView.as_view()),
]