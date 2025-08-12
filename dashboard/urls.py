from django.urls import path
from .views import DailyCheckInCreateView, DashboardSummaryView

urlpatterns = [
    path('checkin/', DailyCheckInCreateView.as_view(), name='checkin'),
    path('summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
   
]
