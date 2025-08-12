from django.shortcuts import render
from rest_framework import generics, permissions
from .models import DailyCheckIn
from .serializers import DailyCheckInSerializer
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now, timedelta
from django.db.models import Avg, Count

from .stress_model.stress_predictor import predict_stress_from_text  # Adjust path accordingly

class DailyCheckInCreateView(generics.CreateAPIView):
    serializer_class = DailyCheckInSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        description = self.request.data.get("description", "")
        predicted_stress = predict_stress_from_text(description)
        serializer.save(user=self.request.user, predicted_stress=predicted_stress)



class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = now().date()
        month_ago = today - timedelta(days=30)

        MAX_STRESS_SCORE = 10.0 
        

        last_7_checkins = DailyCheckIn.objects.filter(user=user).order_by('-date')[:7]

        if last_7_checkins:
            avg_stress_score = sum(ci.predicted_stress for ci in last_7_checkins) / len(last_7_checkins)
        else:
            avg_stress_score = 0
        # Clamp between 0 and 1
        weekly_avg = avg_stress_score / MAX_STRESS_SCORE

        weekly_avg = max(0, min(weekly_avg, 1))
    
        # Total check-ins in last month
        total_checkins = DailyCheckIn.objects.filter(user=user, date__gte=month_ago).count()

        # Current streak calculation (consecutive days with check-ins)
        streak = 0
        day = today
        while DailyCheckIn.objects.filter(user=user, date=day).exists():
            streak += 1
            day -= timedelta(days=1)

        # Wellness score (you can customize this logic)
        # Example: wellness = 100 - average stress * 10 (simple inverse scale)
        wellness_score_value = max(0, 100 - weekly_avg * 100)
        if wellness_score_value >= 80:
            wellness_score = "A+"
        elif wellness_score_value >= 60:
            wellness_score = "B+"
        elif wellness_score_value >= 40:
            wellness_score = "C+"
        else:
            wellness_score = "D"

        # Today's stress level (if any)
       
        today_entry = DailyCheckIn.objects.filter(user=user, date=today).first()
        today_stress = today_entry.predicted_stress/ MAX_STRESS_SCORE if today_entry else None
        if today_stress is not None:
            today_stress = max(0, min(today_stress, 1))

        # Show "need more data" message if less than 10 check-ins
        enough_data = total_checkins >= 10

        data = {
            "weekly_average": weekly_avg if enough_data else None,
            "total_checkins": total_checkins,
            "current_streak": streak,
            "wellness_score": wellness_score if enough_data else None,
            "today_stress": today_stress,
            "enough_data": enough_data,
        }
        return Response(data)