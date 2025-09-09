# backend/agent/urls.py
from django.urls import path
from .views import FreezyChatView, FreezyChatStreamView

urlpatterns = [
    path("freezy/", FreezyChatView.as_view(), name="freezy-chat"),
    path("freezy/stream/", FreezyChatStreamView.as_view(), name="freezy-chat-stream"),
]
