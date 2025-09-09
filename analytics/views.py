from rest_framework import generics, permissions
from .models import UserAnalytics
from .serializers import UserAnalyticsSerializer

class UserAnalyticsView(generics.RetrieveAPIView):
    serializer_class = UserAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.analytics
