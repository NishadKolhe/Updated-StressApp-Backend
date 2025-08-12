from rest_framework import serializers
from .models import DailyCheckIn

class DailyCheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyCheckIn
        fields = '__all__'
        read_only_fields = ['user', 'predicted_stress', 'date']
