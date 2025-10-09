# apps/prediction/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, View
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
import json

from core.models.market_data import Asset
from prediction.models import QuantumPrediction, QuantumEngineConfig, RealTimePredictionQueue
from prediction.tasks import run_quantum_analysis, queue_quantum_analysis
from prediction.services import PredictionOrchestrator
from prediction.engines import EngineFactory

class PredictionDashboardView(LoginRequiredMixin, TemplateView):
    """
    Main prediction dashboard
    """
    template_name = 'prediction/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Active engine configurations
        engine_configs = QuantumEngineConfig.objects.filter(is_active=True)

        # Recent predictions
        recent_predictions = QuantumPrediction.objects.select_related(
            'asset', 'engine_config'
        ).order_by('-prediction_timestamp')[:20]

        # Prediction statistics
        stats = self._get_prediction_stats()

        context.update({
            'engine_configs': engine_configs,
            'recent_predictions': recent_predictions,
            'prediction_stats': stats,
            'active_tab': 'predictions'
        })
        return context

    def _get_prediction_stats(self):
        """Get prediction statistics"""
        today = timezone.now().date()

        total_predictions = QuantumPrediction.objects.count()
        today_predictions = QuantumPrediction.objects.filter(
            prediction_timestamp__date=today
        ).count()

        signal_distribution = QuantumPrediction.objects.values('final_signal').annotate(
            count=Count('id')
        )

        return {
            'total_predictions': total_predictions,
            'today_predictions': today_predictions,
            'signal_distribution': list(signal_distribution)
        }

class QuantumAnalysisView(LoginRequiredMixin, TemplateView):
    """
    Quantum analysis interface (your Streamlit equivalent)
    """
    template_name = 'prediction/analysis.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Default asset
        default_asset = Asset.objects.filter(symbol='AAPL').first()

        # Engine configurations
        engine_configs = QuantumEngineConfig.objects.filter(is_active=True)

        # Recent analysis for the default asset
        recent_analysis = QuantumPrediction.objects.filter(
            asset=default_asset
        ).order_by('-prediction_timestamp')[:5] if default_asset else []

        context.update({
            'default_asset': default_asset,
            'engine_configs': engine_configs,
            'recent_analysis': recent_analysis,
            'available_assets': Asset.objects.filter(is_active=True)[:50]
        })
        return context

class RunAnalysisAPIView(LoginRequiredMixin, View):
    """
    API endpoint to run quantum analysis
    """
    def post(self, request):
        try:
            data = json.loads(request.body)
            symbol = data.get('symbol')
            engine_config_id = data.get('engine_config_id')

            if not symbol:
                return JsonResponse({'success': False, 'error': 'Symbol is required'})

            # Queue the analysis
            queue_quantum_analysis.delay(symbol, priority=5)

            return JsonResponse({
                'success': True,
                'message': f'Analysis queued for {symbol}',
                'symbol': symbol
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class AnalysisResultsAPIView(LoginRequiredMixin, View):
    """
    API endpoint to get analysis results
    """
    def get(self, request, symbol):
        try:
            asset = Asset.objects.get(symbol=symbol)

            # Get latest prediction
            latest_prediction = QuantumPrediction.objects.filter(
                asset=asset
            ).select_related('engine_config').order_by('-prediction_timestamp').first()

            if not latest_prediction:
                return JsonResponse({
                    'success': False,
                    'error': 'No analysis found for this symbol'
                })

            # Format prediction data for frontend
            prediction_data = self._format_prediction_data(latest_prediction)

            # Get historical predictions for charts
            historical_predictions = QuantumPrediction.objects.filter(
                asset=asset
            ).order_by('-prediction_timestamp')[:100]

            chart_data = self._prepare_chart_data(historical_predictions)

            return JsonResponse({
                'success': True,
                'prediction': prediction_data,
                'charts': chart_data,
                'asset': {
                    'symbol': asset.symbol,
                    'name': asset.name
                }
            })

        except Asset.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Asset not found'})

    def _format_prediction_data(self, prediction):
        """Format prediction data for JSON response"""
        return {
            'id': prediction.id,
            'timestamp': prediction.prediction_timestamp.isoformat(),
            'final_signal': prediction.final_signal,
            'signal_confidence': float(prediction.signal_confidence) if prediction.signal_confidence else 0,
            'hurst_exponent': float(prediction.hurst_exponent) if prediction.hurst_exponent else None,
            'hurst_uptrend': float(prediction.hurst_uptrend) if prediction.hurst_uptrend else None,
            'hurst_downtrend': float(prediction.hurst_downtrend) if prediction.hurst_downtrend else None,
            'particle_volatility': float(prediction.particle_volatility) if prediction.particle_volatility else None,
            'dynamic_threshold': float(prediction.dynamic_hurst_threshold) if prediction.dynamic_hurst_threshold else None,
            'fpn_signal': prediction.fpn_signal,
            'fpn_confidence': float(prediction.fpn_confidence) if prediction.fpn_confidence else 0,
            'candlestick_pattern': prediction.candlestick_pattern,
            'engine_config': prediction.engine_config.name if prediction.engine_config else 'Default',
            'signal_components': prediction.signal_components if hasattr(prediction, 'signal_components') else {}
        }

    def _prepare_chart_data(self, predictions):
        """Prepare chart data for historical predictions"""
        dates = [p.prediction_timestamp.isoformat() for p in predictions]
        hurst_values = [float(p.hurst_exponent) if p.hurst_exponent else None for p in predictions]
        volatility_values = [float(p.particle_volatility) if p.particle_volatility else None for p in predictions]
        signals = [p.final_signal for p in predictions]

        return {
            'dates': dates,
            'hurst': hurst_values,
            'volatility': volatility_values,
            'signals': signals
        }

class SignalListView(LoginRequiredMixin, ListView):
    """
    List all trading signals
    """
    model = QuantumPrediction
    template_name = 'prediction/signals.html'
    context_object_name = 'signals'
    paginate_by = 20

    def get_queryset(self):
        queryset = QuantumPrediction.objects.select_related(
            'asset', 'engine_config'
        ).order_by('-prediction_timestamp')

        # Filter by signal type
        signal_filter = self.request.GET.get('signal')
        if signal_filter and signal_filter != 'all':
            queryset = queryset.filter(final_signal=signal_filter.upper())

        # Filter by asset
        asset_filter = self.request.GET.get('asset')
        if asset_filter:
            queryset = queryset.filter(asset__symbol__icontains=asset_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'signal_types': ['BUY', 'SELL', 'HOLD'],
            'active_tab': 'signals',
            'current_filters': {
                'signal': self.request.GET.get('signal', 'all'),
                'asset': self.request.GET.get('asset', '')
            }
        })
        return context

class EngineConfigView(LoginRequiredMixin, TemplateView):
    """
    Quantum engine configuration interface
    """
    template_name = 'prediction/engine_config.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        configs = QuantumEngineConfig.objects.all().order_by('-is_active', '-created_at')
        active_config = QuantumEngineConfig.objects.filter(is_active=True).first()

        context.update({
            'engine_configs': configs,
            'active_config': active_config,
            'default_config': self._get_default_config()
        })
        return context

    def _get_default_config(self):
        """Get default configuration template"""
        return {
            'base_window_size': 20,
            'particle_count': 100,
            'hurst_threshold': 0.65,
            'volatility_entropy_weight': 1.0,
            'fractal_dimension_weight': 1.0
        }

class UpdateEngineConfigAPIView(LoginRequiredMixin, View):
    """
    API endpoint to update engine configuration
    """
    def post(self, request):
        try:
            data = json.loads(request.body)
            config_id = data.get('id')

            if config_id:
                # Update existing config
                config = QuantumEngineConfig.objects.get(id=config_id)
                for field, value in data.items():
                    if hasattr(config, field) and field != 'id':
                        setattr(config, field, value)
                config.save()
            else:
                # Create new config
                config = QuantumEngineConfig.objects.create(**data)

            return JsonResponse({
                'success': True,
                'message': 'Configuration saved successfully',
                'config_id': config.id
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class ActivateEngineConfigAPIView(LoginRequiredMixin, View):
    """
    API endpoint to activate an engine configuration
    """
    def post(self, request, config_id):
        try:
            # Deactivate all configs
            QuantumEngineConfig.objects.update(is_active=False)

            # Activate selected config
            config = QuantumEngineConfig.objects.get(id=config_id)
            config.is_active = True
            config.save()

            return JsonResponse({
                'success': True,
                'message': f'Activated configuration: {config.name}'
            })

        except QuantumEngineConfig.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Configuration not found'})