# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    full_name = models.CharField(max_length=150, blank=True, null=True, default="")
    email = models.EmailField(unique=True)  # required, unique
    profile_photo = models.URLField(blank=True, null=True, default=None)
    bio = models.TextField(blank=True, null=True, default="")
    gender = models.CharField(max_length=10, blank=True, null=True, default=None)
    role = models.CharField(max_length=100, blank=True, null=True, default=None)
    interests = models.JSONField(default=list, blank=True)  # safe empty list
    followers = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='following',
        blank=True
    )

    def __str__(self):
        return self.username


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(minutes=10)
