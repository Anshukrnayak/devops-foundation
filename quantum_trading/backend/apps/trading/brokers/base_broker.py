# apps/trading/brokers/base_broker.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging
from django.utils import timezone
from core.models.market_data import Asset

logger = logging.getLogger(__name__)

class BaseBroker(ABC):
    """
    Abstract base class for all brokerage integrations
    Defines the interface that all brokers must implement
    """

    def __init__(self, name: str, api_key: str, secret_key: str, base_url: str, paper_trading: bool = True):
        self.name = name
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.paper_trading = paper_trading
        self.is_connected = False
        self.last_connection_test = None
        self.rate_limits = {}

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to broker API
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to broker API
        """
        pass

    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get trading account information
        """
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions
        """
        pass

    @abstractmethod
    def get_orders(self, status: str = None) -> List[Dict[str, Any]]:
        """
        Get order history
        """
        pass

    @abstractmethod
    def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place a new order
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order
        """
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get current status of an order
        """
        pass

    @abstractmethod
    def get_market_data(self, symbol: str, timeframe: str = '1D', limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get market data for a symbol
        """
        pass

    @abstractmethod
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time quote for a symbol
        """
        pass

    # Common utility methods
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate symbol format for this broker
        """
        if not symbol or len(symbol) > 20:
            return False
        return symbol.replace('-', '').isalnum()

    def calculate_position_size(self, account_balance: Decimal, risk_percent: Decimal, entry_price: Decimal, stop_loss: Decimal) -> Decimal:
        """
        Calculate position size based on risk management
        """
        if not all([account_balance, risk_percent, entry_price, stop_loss]):
            return Decimal('0')

        risk_amount = account_balance * (risk_percent / Decimal('100'))
        price_risk = abs(entry_price - stop_loss)

        if price_risk == 0:
            return Decimal('0')

        position_size = risk_amount / price_risk
        return position_size.quantize(Decimal('0.000001'))

    def format_quantity(self, quantity: Decimal, symbol: str) -> Decimal:
        """
        Format quantity according to broker's lot size rules
        """
        # Different brokers have different lot size requirements
        if 'BTC' in symbol or 'ETH' in symbol:
            # Crypto - allow small fractions
            return quantity.quantize(Decimal('0.00000001'))
        else:
            # Stocks - typically whole shares, but some allow fractional
            return quantity.quantize(Decimal('0.0001'))

    def check_connection(self) -> bool:
        """
        Check if connection to broker is alive
        """
        try:
            # Simple API call to test connection
            account_info = self.get_account_info()
            self.is_connected = bool(account_info)
            self.last_connection_test = timezone.now()
            return self.is_connected
        except Exception as e:
            logger.error(f"Broker connection test failed for {self.name}: {str(e)}")
            self.is_connected = False
            return False

    def get_broker_info(self) -> Dict[str, Any]:
        """
        Get broker metadata and capabilities
        """
        return {
            'name': self.name,
            'paper_trading': self.paper_trading,
            'connected': self.is_connected,
            'last_connection_test': self.last_connection_test,
            'supported_order_types': self.get_supported_order_types(),
            'supported_assets': self.get_supported_assets(),
            'rate_limits': self.rate_limits
        }

    @abstractmethod
    def get_supported_order_types(self) -> List[str]:
        """
        Get list of supported order types
        """
        pass

    @abstractmethod
    def get_supported_assets(self) -> List[str]:
        """
        Get list of supported asset types
        """
        pass