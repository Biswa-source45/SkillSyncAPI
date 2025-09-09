from rest_framework import serializers
from .models import UserAnalytics

class UserAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnalytics
        fields = '__all__'
