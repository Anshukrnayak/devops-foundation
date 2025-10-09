# apps/trading/executors/base_executor.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging
from django.utils import timezone

from trading.brokers.base_broker import BaseBroker
from trading.models import Order, Trade, TradingAccount
from core.services.risk_manager import RiskManager

logger = logging.getLogger(__name__)

class BaseOrderExecutor(ABC):
    """
    Abstract base class for order execution strategies
    Handles order placement, monitoring, and execution
    """

    def __init__(self, broker: BaseBroker, trading_account: TradingAccount):
        self.broker = broker
        self.trading_account = trading_account
        self.risk_manager = RiskManager(trading_account)
        self.is_running = False
        self.pending_orders = {}

    @abstractmethod
    def execute_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an order with the chosen strategy
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order
        """
        pass

    @abstractmethod
    def monitor_orders(self) -> List[Dict[str, Any]]:
        """
        Monitor pending orders and update status
        """
        pass

    def validate_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate order before execution
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # Basic validation
        required_fields = ['symbol', 'side', 'order_type', 'quantity']
        for field in required_fields:
            if field not in order_data:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing required field: {field}")

        # Symbol validation
        symbol = order_data.get('symbol')
        if symbol and not self.broker.validate_symbol(symbol):
            validation_result['valid'] = False
            validation_result['errors'].append(f"Invalid symbol format: {symbol}")

        # Quantity validation
        quantity = order_data.get('quantity')
        if quantity and quantity <= 0:
            validation_result['valid'] = False
            validation_result['errors'].append("Quantity must be positive")

        # Risk validation
        risk_check = self.risk_manager.validate_order(order_data)
        if not risk_check['passed']:
            validation_result['valid'] = False
            validation_result['errors'].append("Order failed risk validation")
            validation_result['risk_checks'] = risk_check

        return validation_result

    def format_order_data(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format order data for broker-specific requirements
        """
        formatted_data = order_data.copy()

        # Ensure symbol is uppercase
        if 'symbol' in formatted_data:
            formatted_data['symbol'] = formatted_data['symbol'].upper()

        # Format quantity according to broker rules
        if 'quantity' in formatted_data and 'symbol' in formatted_data:
            formatted_data['quantity'] = self.broker.format_quantity(
                Decimal(str(formatted_data['quantity'])),
                formatted_data['symbol']
            )

        # Add client order ID if not present
        if 'client_order_id' not in formatted_data:
            formatted_data['client_order_id'] = self._generate_client_order_id()

        return formatted_data

    def _generate_client_order_id(self) -> str:
        """
        Generate unique client order ID
        """
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_suffix = str(hash(timestamp))[-6:]
        return f"QTS_{timestamp}_{random_suffix}"

    def calculate_smart_quantity(self, symbol: str, side: str, amount: Decimal,
                                 price: Decimal = None) -> Decimal:
        """
        Calculate optimal order quantity based on available funds and position sizing
        """
        try:
            # Get current account balance
            account_info = self.broker.get_account_info()
            buying_power = account_info.get('buying_power', Decimal('0'))

            # Get current price if not provided
            if not price:
                quote = self.broker.get_quote(symbol)
                price = quote.get('ask_price' if side == 'BUY' else 'bid_price', Decimal('0'))

            if price <= 0:
                return Decimal('0')

            # Calculate maximum position size based on risk management
            max_position_size = self.trading_account.profile.max_position_size if hasattr(self.trading_account, 'profile') else Decimal('1000')
            max_quantity = max_position_size / price

            # Calculate quantity based on available buying power
            available_quantity = buying_power / price

            # Use the smaller of the two
            quantity = min(amount, max_quantity, available_quantity)

            return self.broker.format_quantity(quantity, symbol)

        except Exception as e:
            logger.error(f"Error calculating smart quantity: {str(e)}")
            return Decimal('0')