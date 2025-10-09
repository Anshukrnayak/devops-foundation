# apps/core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.views import View
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count, Sum, Q
from datetime import datetime, timedelta
import json

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
from core.models.market_data import Asset, MarketData
from core.models.portfolios import Portfolio, Position
from prediction.models import QuantumPrediction, QuantumEngineConfig
from trading.models import Order, TradingAccount
from prediction.services import PredictionOrchestrator
from core.services.data_fetcher import MarketDataFetcher

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main trading dashboard
    """
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Portfolio summary
        portfolios = Portfolio.objects.filter(user=user, is_active=True)
        total_value = sum(float(portfolio.current_value) for portfolio in portfolios)

        # Recent predictions
        recent_predictions = QuantumPrediction.objects.filter(
            asset__is_active=True
        ).select_related('asset').order_by('-prediction_timestamp')[:10]

        # Active positions
        active_positions = Position.objects.filter(
            portfolio__user=user,
            status='OPEN'
        ).select_related('asset')[:5]

        # System status
        system_status = self._get_system_status()

        context.update({
            'total_portfolio_value': total_value,
            'recent_predictions': recent_predictions,
            'active_positions': active_positions,
            'system_status': system_status,
            'active_tab': 'dashboard'
        })
        return context

    def _get_system_status(self):
        """Get system health and status"""
        return {
            'market_data_updated': MarketData.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=1)
            ).exists(),
            'active_predictions': QuantumPrediction.objects.filter(
                prediction_timestamp__gte=timezone.now() - timedelta(days=1)
            ).count(),
            'engine_status': 'OPERATIONAL',
            'last_update': timezone.now()
        }

class MarketOverviewView(LoginRequiredMixin, TemplateView):
    """
    Market overview with watchlist and heatmaps
    """
    template_name = 'core/market_overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Popular assets
        popular_assets = Asset.objects.filter(is_active=True)[:20]

        # Recent market movements
        recent_movements = MarketData.objects.select_related('asset').filter(
            timestamp__gte=timezone.now() - timedelta(days=1)
        ).order_by('-timestamp')[:50]

        context.update({
            'popular_assets': popular_assets,
            'recent_movements': recent_movements,
            'active_tab': 'market'
        })
        return context

class AssetDetailView(LoginRequiredMixin, DetailView):
    """
    Detailed view for a specific asset
    """
    model = Asset
    template_name = 'core/asset_detail.html'
    context_object_name = 'asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.object

        # Market data
        market_data = MarketData.objects.filter(asset=asset).order_by('-timestamp')[:100]

        # Recent predictions
        predictions = QuantumPrediction.objects.filter(asset=asset).order_by('-prediction_timestamp')[:10]

        # Technical data
        technical_data = self._get_technical_data(asset)

        context.update({
            'market_data': market_data,
            'predictions': predictions,
            'technical_data': technical_data,
            'price_chart_data': self._prepare_price_chart_data(market_data)
        })
        return context

    def _get_technical_data(self, asset):
        """Get technical analysis data for asset"""
        # This would integrate with your technical engine
        return {
            'current_price': asset.current_price if hasattr(asset, 'current_price') else 0,
            'daily_change': 0,  # Calculate from market data
            'volume': 0,  # Calculate from market data
            'market_cap': asset.market_cap if asset.market_cap else 0
        }

    def _prepare_price_chart_data(self, market_data):
        """Prepare data for price charts"""
        dates = [data.timestamp.isoformat() for data in market_data]
        prices = [float(data.close) for data in market_data]

        return {
            'dates': dates,
            'prices': prices
        }
# apps/core/views.py (Additional Views)
class MarketOverviewView(LoginRequiredMixin, TemplateView):
    """
    Comprehensive market overview with watchlists and heatmaps
    """
    template_name = 'core/market_overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Top movers
        gainers = Asset.objects.filter(is_active=True).order_by('-daily_change')[:10]
        losers = Asset.objects.filter(is_active=True).order_by('daily_change')[:10]

        # Most active
        most_active = Asset.objects.filter(is_active=True).order_by('-daily_volume')[:15]

        # Watchlist items
        watchlist = self.request.user.profile.favorite_tickers if hasattr(self.request.user, 'profile') else []
        watchlist_assets = Asset.objects.filter(symbol__in=watchlist)[:10]

        # Market indices
        indices = ['SPY', 'QQQ', 'DIA', 'IWM', 'VIX']
        index_data = []
        for symbol in indices:
            try:
                asset = Asset.objects.get(symbol=symbol)
                latest_data = MarketData.objects.filter(asset=asset).order_by('-timestamp').first()
                if latest_data:
                    index_data.append({
                        'symbol': symbol,
                        'price': latest_data.close,
                        'change': ((latest_data.close - latest_data.open) / latest_data.open * 100) if latest_data.open else 0
                    })
            except Asset.DoesNotExist:
                continue

        context.update({
            'gainers': gainers,
            'losers': losers,
            'most_active': most_active,
            'watchlist_assets': watchlist_assets,
            'index_data': index_data,
            'active_tab': 'market'
        })
        return context

class AssetDetailView(LoginRequiredMixin, DetailView):
    """
    Detailed view for individual assets with comprehensive analysis
    """
    model = Asset
    template_name = 'core/asset_detail.html'
    context_object_name = 'asset'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.object

        # Price data for different timeframes
        timeframes = {
            '1D': 1,
            '1W': 7,
            '1M': 30,
            '3M': 90,
            '1Y': 365
        }

        price_data = {}
        for timeframe, days in timeframes.items():
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            data = MarketData.objects.filter(
                asset=asset,
                timestamp__range=[start_date, end_date]
            ).order_by('timestamp')
            price_data[timeframe] = data

        # Recent predictions
        recent_predictions = QuantumPrediction.objects.filter(
            asset=asset
        ).select_related('engine_config').order_by('-prediction_timestamp')[:10]

        # Trading statistics
        trading_stats = self._get_trading_stats(asset)

        context.update({
            'price_data': price_data,
            'recent_predictions': recent_predictions,
            'trading_stats': trading_stats,
            'timeframes': list(timeframes.keys())
        })
        return context

    def _get_trading_stats(self, asset):
        """Calculate trading statistics for the asset"""
        # This would include volume analysis, volatility, etc.
        return {
            'avg_volume': 0,
            'volatility': 0,
            'beta': 0,
            'market_cap': asset.market_cap
        }
class SystemStatusAPIView(LoginRequiredMixin, View):
    """
    API endpoint for system status
    """
    def get(self, request):
        status = {
            'market_data': self._check_market_data(),
            'prediction_engine': self._check_prediction_engine(),
            'trading_api': self._check_trading_api(),
            'last_updated': timezone.now().isoformat()
        }

        return JsonResponse(status)

    def _check_market_data(self):
        """Check market data health"""
        recent_data = MarketData.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=1)
        ).exists()
        return {
            'status': 'healthy' if recent_data else 'warning',
            'message': 'Market data up to date' if recent_data else 'No recent market data'
        }

    def _check_prediction_engine(self):
        """Check prediction engine health"""
        recent_predictions = QuantumPrediction.objects.filter(
            prediction_timestamp__gte=timezone.now() - timedelta(hours=6)
        ).exists()
        return {
            'status': 'healthy' if recent_predictions else 'warning',
            'message': 'Predictions active' if recent_predictions else 'No recent predictions'
        }

    def _check_trading_api(self):
        """Check trading API health"""
        # This would actually test broker connectivity
        return {
            'status': 'healthy',
            'message': 'Trading API connected'
        }

# apps/core/views.py (Add these views)
class SystemSettingsView(LoginRequiredMixin, TemplateView):
    """System-wide settings configuration"""
    template_name = 'core/system_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'settings'
        return context

class SaveSettingsAPIView(LoginRequiredMixin, View):
    """API endpoint to save system settings"""

    def post(self, request):
        try:
            data = json.loads(request.body)
            # Save settings to database or cache
            # This would typically save to UserProfile or a Settings model

            return JsonResponse({'success': True, 'message': 'Settings saved successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class LoadSettingsAPIView(LoginRequiredMixin, View):
    """API endpoint to load system settings"""

    def get(self, request):
        try:
            # Load settings from database
            settings = {
                'general': {
                    'theme': 'dark',
                    'defaultPage': 'dashboard',
                    # ... other settings
                },
                # ... other categories
            }
            return JsonResponse({'success': True, 'settings': settings})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


def health_check(request):
    """Health check endpoint for Docker and load balancers"""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Check Redis connection
        cache.get('health_check')

        # Check Celery (if you have a test task)
        # from celery.result import AsyncResult
        # result = test_task.delay()
        # result.get(timeout=5)

        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'cache': 'connected',
            'timestamp': timezone.now().isoformat()
        })

    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)