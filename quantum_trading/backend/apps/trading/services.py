# apps/trading/services.py
from decimal import Decimal
import alpaca_trade_api as tradeapi
from django.conf import settings
from typing import Dict, Optional
import logging
from trading.models import TradingAccount, Order, Broker
from core.services.risk_manager import RiskManager

logger = logging.getLogger(__name__)

class TradingExecutor:
    """
    Execute trades through brokerage APIs
    """

    def __init__(self, trading_account: TradingAccount):
        self.trading_account = trading_account
        self.broker = trading_account.broker
        self.api_client = self._initialize_api_client()
        self.risk_manager = RiskManager(trading_account)

    def _initialize_api_client(self):
        """
        Initialize brokerage API client
        """
        if self.broker.name == 'ALPACA':
            return tradeapi.REST(
                key=self.broker.api_key_encrypted,
                secret=self.broker.secret_key_encrypted,
                base_url=self.broker.base_url,
                api_version='v2'
            )
        # Add other brokers here
        else:
            raise ValueError(f"Unsupported broker: {self.broker.name}")

    def execute_order(self, order_data: Dict) -> Dict:
        """
        Execute a trading order with risk checks
        """
        try:
            # Pre-trade risk validation
            risk_check = self.risk_manager.validate_order(order_data)
            if not risk_check['passed']:
                return {
                    'success': False,
                    'order_id': None,
                    'message': 'Risk validation failed',
                    'risk_checks': risk_check
                }

            # Create order in database
            order = Order.objects.create(
                trading_account=self.trading_account,
                asset_id=order_data['asset_id'],
                order_type=order_data.get('order_type', 'LIMIT'),
                side=order_data['side'],
                quantity=Decimal(str(order_data['quantity'])),
                limit_price=Decimal(str(order_data.get('limit_price', 0))),
                time_in_force=order_data.get('time_in_force', 'DAY')
            )

            # Execute with broker
            if self.broker.paper_trading:
                result = self._execute_paper_trade(order, order_data)
            else:
                result = self._execute_live_trade(order, order_data)

            return result

        except Exception as e:
            logger.error(f"Error executing order: {str(e)}")
            return {
                'success': False,
                'order_id': None,
                'message': str(e)
            }

    def _execute_live_trade(self, order: Order, order_data: Dict) -> Dict:
        """
        Execute live trade through brokerage API
        """
        try:
            # Alpaca execution example
            if self.broker.name == 'ALPACA':
                api_order = self.api_client.submit_order(
                    symbol=order.asset.symbol,
                    qty=float(order.quantity),
                    side=order.side.lower(),
                    type=order.order_type.lower(),
                    time_in_force=order.time_in_force,
                    limit_price=float(order.limit_price) if order.limit_price else None,
                    stop_price=float(order.stop_price) if order.stop_price else None
                )

                # Update order with broker response
                order.broker_order_id = api_order.id
                order.status = api_order.status.upper()
                order.save()

                return {
                    'success': True,
                    'order_id': order.id,
                    'broker_order_id': api_order.id,
                    'message': 'Order submitted successfully'
                }

            # Add other broker implementations

        except Exception as e:
            logger.error(f"Error in live trade execution: {str(e)}")
            order.status = 'REJECTED'
            order.error_message = str(e)
            order.save()

            return {
                'success': False,
                'order_id': order.id,
                'message': str(e)
            }