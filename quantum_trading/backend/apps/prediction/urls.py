# apps/prediction/urls.py
from django.urls import path
from . import views

app_name = 'prediction'

urlpatterns = [
    path('', views.PredictionDashboardView.as_view(), name='prediction_dashboard'),
    path('analysis/', views.QuantumAnalysisView.as_view(), name='quantum_analysis'),
    path('signals/', views.SignalListView.as_view(), name='signal_list'),
    path('engine-config/', views.EngineConfigView.as_view(), name='engine_config'),

    # API endpoints
    path('api/run-analysis/', views.RunAnalysisAPIView.as_view(), name='run_analysis_api'),
    path('api/analysis-results/<str:symbol>/', views.AnalysisResultsAPIView.as_view(), name='analysis_results_api'),
    path('api/update-config/', views.UpdateEngineConfigAPIView.as_view(), name='update_config_api'),
    path('api/activate-config/<int:config_id>/', views.ActivateEngineConfigAPIView.as_view(), name='activate_config_api'),
]
