
# apps/trading/urls.py
from django.urls import path
from . import views

app_name = 'trading'

urlpatterns = [
    path('portfolio/', views.PortfolioView.as_view(), name='portfolio'),
    path('orders/', views.OrderView.as_view(), name='orders'),
    path('trading-signals/', views.TradingSignalsView.as_view(), name='trading_signals'),

    # API endpoints
    path('api/place-order/', views.PlaceOrderAPIView.as_view(), name='place_order_api'),
    path('api/order/<uuid:order_id>/', views.OrderDetailAPIView.as_view(), name='order_detail_api'),
    path('api/execute-signal/<int:prediction_id>/', views.ExecuteSignalAPIView.as_view(), name='execute_signal_api'),
]
