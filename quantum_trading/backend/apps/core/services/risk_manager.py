# apps/core/services/risk_manager.py
from decimal import Decimal
from django.db.models import Sum
from typing import Dict, List, Optional
import logging
from core.models.portfolios import Portfolio, Position
from trading.models import Order, TradingAccount

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Comprehensive risk management for trading operations
    """

    def __init__(self, trading_account: TradingAccount):
        self.trading_account = trading_account
        self.user = trading_account.user

    def validate_order(self, order_data: Dict) -> Dict:
        """
        Pre-trade risk validation
        """
        checks = {
            'position_size': self._check_position_size(order_data),
            'day_trading': self._check_day_trading(order_data),
            'margin_requirements': self._check_margin_requirements(order_data),
            'volatility_limits': self._check_volatility_limits(order_data),
            'concentration_risk': self._check_concentration_risk(order_data),
        }

        all_passed = all(check['passed'] for check in checks.values())

        return {
            'passed': all_passed,
            'checks': checks,
            'message': 'Order validation completed' if all_passed else 'Risk checks failed'
        }

    def _check_position_size(self, order_data: Dict) -> Dict:
        """
        Check if position size is within limits
        """
        try:
            max_position_size = Decimal('10000.00')  # Configurable
            proposed_size = Decimal(str(order_data['quantity'])) * Decimal(str(order_data.get('price', 0)))

            passed = proposed_size <= max_position_size

            return {
                'passed': passed,
                'message': f"Position size {'within' if passed else 'exceeds'} limits",
                'details': {
                    'proposed_size': float(proposed_size),
                    'max_size': float(max_position_size)
                }
            }

        except Exception as e:
            logger.error(f"Error in position size check: {str(e)}")
            return {'passed': False, 'message': str(e)}

    def _check_day_trading(self, order_data: Dict) -> Dict:
        """
        Check day trading pattern rules
        """
        # Implement FINRA day trading rules
        today = timezone.now().date()
        day_trades_today = Order.objects.filter(
            trading_account=self.trading_account,
            created_at__date=today,
            side__in=['BUY', 'SELL']
        ).count()

        max_day_trades = 3  # For pattern day trading accounts
        passed = day_trades_today < max_day_trades

        return {
            'passed': passed,
            'message': f"Day trading check {'passed' if passed else 'failed'}",
            'details': {
                'trades_today': day_trades_today,
                'max_trades': max_day_trades
            }
        }

    def calculate_portfolio_risk(self) -> Dict:
        """
        Calculate overall portfolio risk metrics
        """
        try:
            positions = Position.objects.filter(
                portfolio__user=self.user,
                status='OPEN'
            )

            total_value = sum(float(position.current_value) for position in positions)
            unrealized_pnl = sum(float(position.unrealized_pnl) for position in positions)

            # Calculate Value at Risk (VaR) - simplified
            var_95 = self._calculate_var(positions, confidence_level=0.95)

            return {
                'total_portfolio_value': total_value,
                'unrealized_pnl': unrealized_pnl,
                'var_95': var_95,
                'position_count': positions.count(),
                'concentration_risk': self._calculate_concentration_risk(positions)
            }

        except Exception as e:
            logger.error(f"Error calculating portfolio risk: {str(e)}")
            return {}

    def _calculate_var(self, positions, confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (simplified implementation)
        """
        # This is a simplified VaR calculation
        # In production, use historical simulation or parametric methods
        total_risk = 0
        for position in positions:
            # Simplified risk calculation based on volatility
            volatility = Decimal('0.02')  # Should come from actual data
            position_risk = float(position.current_value) * float(volatility)
            total_risk += position_risk

        return total_risk * (1 - confidence_level)