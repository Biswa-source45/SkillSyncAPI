from django.urls import path
from .views import UserAnalyticsView

urlpatterns = [
    path('my-analytics/', UserAnalyticsView.as_view(), name='user-analytics'),
]
