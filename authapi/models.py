from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # example extra fields, add more as needed
    full_name = models.CharField(max_length=100, blank=True)
    # You can add fields like age, gender, etc.

    def __str__(self):
        return self.user.username