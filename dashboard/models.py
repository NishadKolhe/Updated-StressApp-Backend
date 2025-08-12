from django.db import models
from django.contrib.auth.models import User

class DailyCheckIn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    description = models.TextField()
    tags = models.JSONField()  # List of selected tags
    mood = models.IntegerField()  # From slider (0–10)
    predicted_stress = models.FloatField()  # From your ML model

    def __str__(self):
        return f"{self.user.username} - {self.date}"
