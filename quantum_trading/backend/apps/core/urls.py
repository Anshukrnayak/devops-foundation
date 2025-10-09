# apps/core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('market/', views.MarketOverviewView.as_view(), name='market_overview'),
    path('asset/<str:symbol>/', views.AssetDetailView.as_view(), name='asset_detail'),

    # API endpoints
    path('api/asset/<str:symbol>/', views.AssetDataAPIView.as_view(), name='asset_data_api'),
    path('api/system-status/', views.SystemStatusAPIView.as_view(), name='system_status_api'),
]


