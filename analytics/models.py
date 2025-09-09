from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserAnalytics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='analytics')
    total_posts = models.IntegerField(default=0)
    total_likes = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)
    total_followers = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Analytics"
