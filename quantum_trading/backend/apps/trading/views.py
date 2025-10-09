# apps/trading/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, View
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
import json

from trading.models import TradingAccount, Order, Position, Trade, Broker
from core.models.portfolios import Portfolio
from core.models.market_data import Asset
from prediction.models import QuantumPrediction
from trading.services import TradingExecutor
from core.services.risk_manager import RiskManager

class PortfolioView(LoginRequiredMixin, TemplateView):
    """
    Portfolio management interface
    """
    template_name = 'trading/portfolio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # User portfolios
        portfolios = Portfolio.objects.filter(user=user, is_active=True)

        # Trading accounts
        trading_accounts = TradingAccount.objects.filter(user=user, is_active=True)

        # Active positions
        active_positions = Position.objects.filter(
            trading_account__user=user,
            is_open=True
        ).select_related('asset', 'trading_account')

        # Performance metrics
        performance = self._calculate_performance_metrics(user)

        context.update({
            'portfolios': portfolios,
            'trading_accounts': trading_accounts,
            'active_positions': active_positions,
            'performance_metrics': performance,
            'active_tab': 'portfolio'
        })
        return context

    def _calculate_performance_metrics(self, user):
        """Calculate portfolio performance metrics"""
        positions = Position.objects.filter(trading_account__user=user)

        total_invested = sum(float(pos.quantity * pos.average_entry_price) for pos in positions if pos.average_entry_price)
        total_value = sum(float(pos.market_value) for pos in positions)
        total_pnl = sum(float(pos.unrealized_pnl) for pos in positions)

        return {
            'total_invested': total_invested,
            'total_value': total_value,
            'total_pnl': total_pnl,
            'pnl_percentage': (total_pnl / total_invested * 100) if total_invested > 0 else 0
        }

class OrderView(LoginRequiredMixin, TemplateView):
    """
    Order management interface
    """
    template_name = 'trading/orders.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Recent orders
        orders = Order.objects.filter(
            trading_account__user=user
        ).select_related('asset', 'trading_account').order_by('-created_at')[:50]

        # Order statistics
        order_stats = self._get_order_stats(user)

        # Available assets for trading
        available_assets = Asset.objects.filter(is_active=True)[:100]

        context.update({
            'orders': orders,
            'order_stats': order_stats,
            'available_assets': available_assets,
            'order_types': Order.ORDER_TYPES,
            'order_sides': Order.ORDER_SIDES,
            'time_in_force_options': Order.TIME_IN_FORCE,
            'active_tab': 'orders'
        })
        return context

    def _get_order_stats(self, user):
        """Get order statistics"""
        today = timezone.now().date()

        total_orders = Order.objects.filter(trading_account__user=user).count()
        today_orders = Order.objects.filter(
            trading_account__user=user,
            created_at__date=today
        ).count()

        filled_orders = Order.objects.filter(
            trading_account__user=user,
            status='FILLED'
        ).count()

        return {
            'total_orders': total_orders,
            'today_orders': today_orders,
            'filled_orders': filled_orders,
            'success_rate': (filled_orders / total_orders * 100) if total_orders > 0 else 0
        }

class PlaceOrderAPIView(LoginRequiredMixin, View):
    """
    API endpoint to place orders
    """
    def post(self, request):
        try:
            data = json.loads(request.body)
            user = request.user

            # Validate required fields
            required_fields = ['symbol', 'side', 'order_type', 'quantity']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({
                        'success': False,
                        'error': f'Missing required field: {field}'
                    })

            # Get trading account (use default for now)
            trading_account = TradingAccount.objects.filter(
                user=user, is_default=True
            ).first()

            if not trading_account:
                return JsonResponse({
                    'success': False,
                    'error': 'No trading account configured'
                })

            # Get asset
            asset = Asset.objects.get(symbol=data['symbol'])

            # Prepare order data
            order_data = {
                'asset_id': asset.id,
                'side': data['side'].upper(),
                'order_type': data['order_type'].upper(),
                'quantity': Decimal(str(data['quantity'])),
                'limit_price': Decimal(str(data.get('limit_price', 0))),
                'time_in_force': data.get('time_in_force', 'DAY')
            }

            # Execute order
            trading_executor = TradingExecutor(trading_account)
            result = trading_executor.execute_order(order_data)

            return JsonResponse(result)

        except Asset.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Asset not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

class OrderDetailAPIView(LoginRequiredMixin, View):
    """
    API endpoint to get order details
    """
    def get(self, request, order_id):
        try:
            order = Order.objects.get(
                id=order_id,
                trading_account__user=request.user
            )

            order_data = {
                'id': str(order.id),
                'symbol': order.asset.symbol,
                'side': order.side,
                'order_type': order.order_type,
                'status': order.status,
                'quantity': float(order.quantity),
                'filled_quantity': float(order.filled_quantity),
                'limit_price': float(order.limit_price) if order.limit_price else None,
                'average_fill_price': float(order.average_fill_price) if order.average_fill_price else None,
                'created_at': order.created_at.isoformat(),
                'filled_at': order.filled_at.isoformat() if order.filled_at else None
            }

            return JsonResponse({'success': True, 'order': order_data})

        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order not found'})

class TradingSignalsView(LoginRequiredMixin, ListView):
    """
    View to see trading signals and execute them
    """
    model = QuantumPrediction
    template_name = 'trading/signals.html'
    context_object_name = 'signals'
    paginate_by = 20

    def get_queryset(self):
        # Only show high-confidence signals
        return QuantumPrediction.objects.filter(
            final_signal__in=['BUY', 'SELL'],
            signal_confidence__gte=0.7,
            signal_executed=False
        ).select_related('asset').order_by('-signal_confidence', '-prediction_timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'active_tab': 'trading_signals',
            'trading_accounts': TradingAccount.objects.filter(user=self.request.user, is_active=True)
        })
        return context

class ExecuteSignalAPIView(LoginRequiredMixin, View):
    """
    API endpoint to execute a trading signal
    """
    def post(self, request, prediction_id):
        try:
            prediction = QuantumPrediction.objects.get(id=prediction_id)

            # Get trading account
            trading_account = TradingAccount.objects.filter(
                user=request.user, is_default=True
            ).first()

            if not trading_account:
                return JsonResponse({
                    'success': False,
                    'error': 'No trading account configured'
                })

            # Calculate order quantity based on portfolio size
            portfolio_value = float(trading_account.portfolio_value)
            position_size = portfolio_value * 0.02  # 2% position size

            current_price = prediction.market_data.close
            quantity = position_size / float(current_price)

            # Prepare order data
            order_data = {
                'asset_id': prediction.asset.id,
                'side': prediction.final_signal,
                'order_type': 'MARKET',
                'quantity': Decimal(str(quantity)),
                'time_in_force': 'DAY'
            }

            # Execute order
            trading_executor = TradingExecutor(trading_account)
            result = trading_executor.execute_order(order_data)

            if result['success']:
                # Mark prediction as executed
                prediction.signal_executed = True
                prediction.save()

            return JsonResponse(result)

        except QuantumPrediction.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Signal not found'})