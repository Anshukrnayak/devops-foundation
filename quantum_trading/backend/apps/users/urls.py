# apps/users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('trading-preferences/', views.TradingPreferencesView.as_view(), name='trading_preferences'),
]

